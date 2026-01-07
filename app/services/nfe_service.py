#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NFeService (arquivo 4/4) - Integrado e corrigido

Responsável por:
- Ler dados do banco de forma robusta e com consumo de memória moderado
- Gerar XML NF-e (modelo 55) usando NFeXMLBuilder
- Validar XML contra XSD
- Assinar XML com CertificadoDigital (A1)
- Salvar histórico e itens no banco
- (Opcional) Enviar para SEFAZ via SefazService (mTLS)

Observações sobre memória:
- Evitei criar cópias desnecessárias de listas/strings.
- Se a sua classe Database expõe um cursor, o código usa fetchall()
  apenas quando o cursor retorna esse método. Caso seu driver permita
  streaming (fetchmany/iterator), adapte a implementação de carregar_itens_venda
  para usar fetchmany().
- Para grandes cargas de itens, prefira alterar Database.execute_query()
  para retornar um generator ou usar server-side cursor.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Any

# ajustar path do projeto (assumindo layout padrão)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database import Database
from app.services.nfe_xml_builder import NFeXMLBuilder
from app.services.certificado_digital import CertificadoDigital
from app.services.sefaz_service import SefazService

try:
    from app.auto_config import DEFAULT_EMPRESA_ID
except Exception:
    DEFAULT_EMPRESA_ID = 9  # IK Analytics (exemplo)


class NFeService:
    """
    Serviço de geração de NF-e integrado com o banco.

    Principais métodos:
    - gerar_nfe(...)
    - salvar_nfe(...)
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()
        self.certificado: Optional[CertificadoDigital] = None

    @staticmethod
    def validar_ean(ean: str) -> str:
        """
        Valida e corrige código EAN/GTIN para NF-e
        
        Aceita:
        - "SEM GTIN" ou vazio
        - 8 dígitos (EAN-8)
        - 12 dígitos (UPC)
        - 13 dígitos (EAN-13)
        - 14 dígitos (GTIN-14)
        
        Args:
            ean: Código de barras do produto
            
        Returns:
            EAN válido ou "SEM GTIN"
        """
        if not ean or ean.upper() == 'SEM GTIN':
            return 'SEM GTIN'
        
        # Remover espaços e caracteres não numéricos
        ean_limpo = ''.join(c for c in str(ean) if c.isdigit())
        
        # Verificar se tem tamanho válido
        if len(ean_limpo) in [8, 12, 13, 14]:
            return ean_limpo
        
        # Se inválido, retornar "SEM GTIN"
        return 'SEM GTIN'

    # -------------------------
    # Carregamento de registros
    # -------------------------
    def carregar_empresa(self, empresa_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT
                id,
                nome_fantasia,
                razao_social,
                cnpj,
                COALESCE(inscricao_estadual, 'ISENTO') as inscricao_estadual,
                COALESCE(crt, '3') as crt,
                logradouro,
                numero,
                complemento,
                bairro,
                cidade,
                estado,
                cep,
                codigo_municipio_ibge,
                COALESCE(ambiente_nfe, '2') as ambiente_nfe,
                proximo_numero_nfe,
                serie_nfe_padrao
            FROM empresas
            WHERE id = %s
            LIMIT 1
        """
        try:
            resultado = self.db.execute_query(query, (empresa_id,))
            # compatibilidade com diferentes retornos da Database
            if hasattr(resultado, "fetchone"):
                empresa = resultado.fetchone()
            else:
                empresa = resultado[0] if resultado else None
            return empresa
        except Exception as e:
            print(f"[EMPRESA] Erro ao carregar empresa {empresa_id}: {e}")
            return None

    def carregar_cliente(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT
                id,
                name as nome,
                cpf,
                cnpj,
                razao_social,
                ie as inscricao_estadual,
                address as logradouro,
                number as numero,
                complement as complemento,
                neighborhood as bairro,
                city as cidade,
                state as estado,
                cep,
                codigo_municipio,
                COALESCE(ind_ie, '9') as ind_ie,
                email
            FROM customers
            WHERE id = %s
            LIMIT 1
        """
        try:
            resultado = self.db.execute_query(query, (cliente_id,))
            if hasattr(resultado, "fetchone"):
                cliente = resultado.fetchone()
            else:
                cliente = resultado[0] if resultado else None

            if cliente:
                # Normalizar documento (remover não dígitos)
                doc = cliente.get("cnpj") or cliente.get("cpf") or ""
                doc_digits = "".join(filter(str.isdigit, str(doc)))
                if len(doc_digits) == 11:
                    cliente["cpf"] = doc_digits
                    cliente["cnpj"] = None
                elif len(doc_digits) == 14:
                    cliente["cnpj"] = doc_digits
                    cliente["cpf"] = None
            return cliente
        except Exception as e:
            print(f"[CLIENTE] Erro ao carregar cliente {cliente_id}: {e}")
            return None

    def carregar_itens_venda(self, venda_id: int) -> List[Dict[str, Any]]:
        """
        Carrega itens da venda.
        Observação: para vendas com muitos itens, ajuste Database para usar
        server-side cursor / streaming (fetchmany).
        """
        query = """
            SELECT 
                p.id as produto_id,
                p.name as descricao,
                COALESCE(p.internal_code, '') as codigo,
                COALESCE(p.barcode, 'SEM GTIN') as ean,
                COALESCE(si.ncm, p.ncm, '00000000') as ncm,
                COALESCE(si.cfop, p.cfop_out, '5102') as cfop,
                COALESCE(p.unit_measure, 'UN') as unidade,
                si.quantity as quantidade,
                si.unit_price as valor_unitario,
                COALESCE(p.icms_rate, 18.00) as aliquota_icms,
                COALESCE(p.ipi_rate, 0.00) as aliquota_ipi,
                COALESCE(p.pis_rate, 1.65) as aliquota_pis,
                COALESCE(p.cofins_rate, 7.60) as aliquota_cofins,
                12.50 as aliquota_ibs,
                12.50 as aliquota_cbs,
                0.00 as aliquota_is,
                0 as tem_ipi,
                0 as tem_is
            FROM sale_items si
            JOIN products p ON p.id = si.product_id
            WHERE si.sale_id = %s
            ORDER BY si.id
        """
        try:
            itens = self.db.execute_query(query, (venda_id,))
            # adapt to different Database return types
            if hasattr(itens, "fetchall"):
                itens = itens.fetchall()
            
            # Validar e corrigir EAN de cada item
            for item in itens:
                if 'ean' in item:
                    ean_original = item['ean']
                    ean_validado = self.validar_ean(ean_original)
                    if ean_original != ean_validado:
                        print(f"[ITENS] EAN corrigido: '{ean_original}' → '{ean_validado}'")
                    item['ean'] = ean_validado
            
            return itens or []
        except Exception as e:
            print(f"[ITENS] Erro ao carregar itens da venda {venda_id}: {e}")
            return []

    # -------------------------
    # Validação de dados
    # -------------------------
    def validar_dados_nfe(self, empresa: Dict[str, Any], cliente: Dict[str, Any], itens: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        erros: List[str] = []

        # empresa
        if not empresa:
            erros.append("Empresa não informada")
        else:
            if not empresa.get("cnpj"):
                erros.append("CNPJ da empresa é obrigatório")
            if not empresa.get("codigo_municipio_ibge"):
                erros.append("Código município IBGE da empresa é obrigatório")
            if not empresa.get("razao_social"):
                erros.append("Razão social da empresa é obrigatória")

        # cliente
        if not cliente:
            erros.append("Cliente não informado")
        else:
            if not cliente.get("cnpj") and not cliente.get("cpf"):
                erros.append("CPF ou CNPJ do cliente é obrigatório")
            if not cliente.get("codigo_municipio"):
                erros.append("Código município do cliente é obrigatório")
            if not cliente.get("nome"):
                erros.append("Nome do cliente é obrigatório")

        # itens
        if not itens:
            erros.append("Nenhum item informado")
        else:
            for i, it in enumerate(itens, start=1):
                ncm = str(it.get("ncm") or "")
                cfop = str(it.get("cfop") or "")
                qtd = it.get("quantidade")
                vun = it.get("valor_unitario")
                if not ncm or len(ncm) != 8 or not ncm.isdigit():
                    erros.append(f"Item {i}: NCM inválido (deve ter 8 dígitos numéricos)")
                if not cfop or len(cfop) != 4 or not cfop.isdigit():
                    erros.append(f"Item {i}: CFOP inválido (deve ter 4 dígitos numéricos)")
                try:
                    if qtd is None or float(qtd) <= 0:
                        erros.append(f"Item {i}: Quantidade inválida")
                except Exception:
                    erros.append(f"Item {i}: Quantidade inválida")
                try:
                    if vun is None or float(vun) <= 0:
                        erros.append(f"Item {i}: Valor unitário inválido")
                except Exception:
                    erros.append(f"Item {i}: Valor unitário inválido")

        if erros:
            return False, erros
        return True, []

    # -------------------------
    # Geração da NF-e
    # -------------------------
    def gerar_nfe(
        self,
        venda_id: int,
        empresa_id: int = DEFAULT_EMPRESA_ID,
        serie: int = 1,
        numero: Optional[int] = None,
        enviar_para_sefaz: bool = False
    ) -> Dict[str, Any]:
        """
        Gera NF-e (modelo 55) a partir de uma venda.
        Se enviar_para_sefaz=True, tenta enviar o lote após gerar e assinar.
        """
        try:
            print(f"[NFE] Iniciando geração da NFe para venda {venda_id}")
            
            # 1) Carregar venda (apenas metadados)
            q_venda = """
                SELECT id, customer_id as cliente_id, empresa_id, net_total as valor_total
                FROM sales WHERE id = %s LIMIT 1
            """
            venda_res = self.db.execute_query(q_venda, (venda_id,))
            if hasattr(venda_res, "fetchone"):
                venda = venda_res.fetchone()
            else:
                venda = venda_res[0] if venda_res else None

            if not venda:
                print(f"[NFE] Venda {venda_id} não encontrada")
                return {"sucesso": False, "erro": f"Venda {venda_id} não encontrada"}

            cliente_id = venda["cliente_id"]
            empresa_id = venda.get("empresa_id", empresa_id)
            print(f"[NFE] Venda encontrada - Cliente: {cliente_id}, Empresa: {empresa_id}")

            # 2) Carregar dados
            print(f"[NFE] Carregando dados da empresa {empresa_id}")
            empresa = self.carregar_empresa(empresa_id)
            if not empresa:
                return {"sucesso": False, "erro": f"Empresa {empresa_id} não encontrada"}
            
            print(f"[NFE] Carregando dados do cliente {cliente_id}")
            cliente = self.carregar_cliente(cliente_id)
            if not cliente:
                return {"sucesso": False, "erro": f"Cliente {cliente_id} não encontrado"}
            
            print(f"[NFE] Carregando itens da venda {venda_id}")
            itens = self.carregar_itens_venda(venda_id)
            if not itens:
                return {"sucesso": False, "erro": f"Nenhum item encontrado na venda {venda_id}"}

            # 3) Validar dados
            valido, erros = self.validar_dados_nfe(empresa, cliente, itens)
            if not valido:
                return {"sucesso": False, "erros": erros}

            # 4) Próximo número se necessário
            if numero is None:
                q_prox = "SELECT COALESCE(MAX(numero),0)+1 as proximo_numero FROM nfe_emitidas WHERE empresa_id=%s AND serie=%s"
                prox_res = self.db.execute_query(q_prox, (empresa_id, serie))
                if hasattr(prox_res, "fetchone"):
                    row = prox_res.fetchone()
                else:
                    row = prox_res[0] if prox_res else {"proximo_numero": 1}
                numero = row.get("proximo_numero", 1)

            # 5) Gerar XML via builder
            builder = NFeXMLBuilder(
                empresa_id=empresa_id,
                sale_id=venda_id,
                destinatario_teste=cliente,
                itens_teste=itens
            )
            builder.serie_nfe = serie
            builder.numero_nfe = numero

            xml_string = builder.build_xml()
            
            # 6) Validar XSD
            valido_xsd, erros_xsd = builder.validar_xml(xml_string)
            erros_xsd_filtrados = [e for e in erros_xsd if "Signature" not in e]

            if erros_xsd_filtrados:
                return {
                    "sucesso": False,
                    "erro": "XML inválido",
                    "erros_xsd": erros_xsd_filtrados,
                    "xml": xml_string
                }

            # 7) Assinar XML
            # O certificado_digital.py usa deepcopy na canonicalização para
            # evitar xmlns="" que causaria rejeição 297 na SEFAZ
            try:
                if self.certificado is None:
                    self.certificado = CertificadoDigital(empresa_id)

                if not self.certificado.carregar_do_banco():
                    raise Exception("Certificado não encontrado ou inválido")

                xml_assinado = self.certificado.assinar_xml(xml_string)

            except Exception as e:
                # Em ambiente de homologação você pode querer prosseguir sem assinatura.
                # Aqui retornamos erro para produção; ajuste conforme sua necessidade.
                return {"sucesso": False, "erro": f"Falha na assinatura: {e}"}

            # 8) Salvar NF-e no banco
            nfe_id = self.salvar_nfe(
                xml_original=xml_string,
                xml_assinado=xml_assinado,
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                venda_id=venda_id,
                numero=numero,
                serie=serie,
                chave_acesso=builder.chave_acesso,
                totais={
                    "total_nfe": float(builder.total_nfe),
                    "total_produtos": float(builder.total_produtos),
                    "total_icms": float(builder.total_icms),
                    "total_ipi": float(builder.total_ipi),
                    "total_pis": float(builder.total_pis),
                    "total_cofins": float(builder.total_cofins),
                    "total_ibs": float(builder.total_ibs),
                    "total_cbs": float(builder.total_cbs),
                    "total_is": float(builder.total_is)
                },
                itens=itens
            )

            resultado_final = {
                "sucesso": True,
                "nfe_id": nfe_id,
                "numero": numero,
                "serie": serie,
                "chave_acesso": builder.chave_acesso,
                "xml_original": xml_string,
                "xml_assinado": xml_assinado,
                "valor_total": float(builder.total_nfe)
            }

            # 9) Opcional: enviar para SEFAZ
            if enviar_para_sefaz:
                try:
                    # ambiente_nfe vem do cadastro como '1' (produção) ou '2' (homologação)
                    ambiente_cfg = str(empresa.get("ambiente_nfe", "2"))
                    ambiente_txt = "producao" if ambiente_cfg == "1" else "homologacao"

                    # UF é detectada automaticamente a partir da empresa_id
                    sefaz = SefazService(
                        ambiente=ambiente_txt,
                        empresa_id=empresa_id
                    )

                    envio = sefaz.enviar_nfe(xml_assinado)
                    resultado_final["envio_sefaz"] = envio

                    # Determinar se a NF-e foi de fato AUTORIZADA (cStat da NFe = 100)
                    codigo_nfe = str(
                        envio.get("status")
                        or envio.get("codigo_status")
                        or envio.get("codigo")
                        or ""
                    )
                    autorizado = bool(envio.get("autorizado")) or codigo_nfe == "100"

                    if autorizado and envio.get("protocolo"):
                        # Propagar protocolo e data de autorização para o resultado
                        resultado_final["protocolo"] = envio.get("protocolo")
                        resultado_final["data_autorizacao"] = envio.get("data_autorizacao")

                        # Atualizar venda com protocolo e status de autorização
                        try:
                            self.db.execute_query(
                                """
                                UPDATE sales
                                SET status_nfe = 'autorizada',
                                    protocolo_nfe = %s,
                                    data_autorizacao_nfe = %s
                                WHERE id = %s
                                """,
                                (
                                    envio.get("protocolo"),
                                    envio.get("data_autorizacao"),
                                    venda_id,
                                ),
                            )
                        except Exception as e_upd:
                            print(f"[NFE] Erro ao atualizar status de autorização: {e_upd}")
                    else:
                        # Se não houver autorização, considerar falha geral da emissão
                        resultado_final["sucesso"] = False
                        msg = (
                            envio.get("erro")
                            or envio.get("mensagem")
                            or envio.get("motivo")
                            or "Falha ao enviar NF-e para SEFAZ"
                        )
                        resultado_final["erro"] = msg
                except Exception as e:
                    resultado_final["envio_sefaz"] = {"sucesso": False, "erro": str(e)}
                    resultado_final["sucesso"] = False
                    if not resultado_final.get("erro"):
                        resultado_final["erro"] = str(e)

            return resultado_final

        except Exception as e:
            # evitar expor stack trace em produção; logue localmente
            import traceback
            erro_detalhado = traceback.format_exc()
            print(f"[ERRO] gerar_nfe({venda_id}) -> {e}")
            print(f"[ERRO] Stack trace:\n{erro_detalhado}")
            return {"sucesso": False, "erro": str(e) if str(e) else "Erro desconhecido ao gerar NFe", "stack_trace": erro_detalhado}

    # -------------------------
    # Persistência
    # -------------------------
    def salvar_nfe(
        self,
        xml_original: str,
        xml_assinado: str,
        empresa_id: int,
        cliente_id: int,
        venda_id: int,
        numero: int,
        serie: int,
        chave_acesso: str,
        totais: Dict[str, Any],
        itens: List[Dict[str, Any]]
    ) -> int:
        """
        Salva NF-e em tabelas: atualiza a venda, insere em nfe_emitidas e nfe_itens.
        Retorna o id do registro inserido em nfe_emitidas (ou venda_id configurado).
        """
        try:
            # 1) Atualizar venda
            q_update_sale = """
                UPDATE sales SET
                    chave_acesso_nfe=%s,
                    numero_nfe=%s,
                    serie_nfe=%s,
                    data_emissao_nfe=NOW(),
                    status_nfe='pendente',
                    xml_nfe=%s,
                    empresa_id=%s
                WHERE id=%s
            """
            self.db.execute_query(q_update_sale, (chave_acesso, numero, serie, xml_assinado, empresa_id, venda_id))

            # 2) Inserir em nfe_emitidas
            q_insert_nfe = """
                INSERT INTO nfe_emitidas (
                    empresa_id, cliente_id, venda_id,
                    numero, serie, chave_acesso,
                    xml_original, xml_assinado,
                    status, ambiente,
                    valor_total, valor_produtos,
                    valor_icms, valor_ipi, valor_pis, valor_cofins,
                    valor_ibs, valor_cbs, valor_is,
                    created_at
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    NOW()
                )
            """
            params_nfe = (
                empresa_id, cliente_id, venda_id,
                numero, serie, chave_acesso,
                xml_original, xml_assinado,
                "pendente", "2",  # ambiente '2' = homologação por padrão; ajuste conforme empresa
                totais.get("total_nfe", 0.0),
                totais.get("total_produtos", 0.0),
                totais.get("total_icms", 0.0),
                totais.get("total_ipi", 0.0),
                totais.get("total_pis", 0.0),
                totais.get("total_cofins", 0.0),
                totais.get("total_ibs", 0.0),
                totais.get("total_cbs", 0.0),
                totais.get("total_is", 0.0)
            )
            self.db.execute_query(q_insert_nfe, params_nfe)

            # recuperar id inserido — adaptável ao seu driver (aqui assumimos SELECT LAST_INSERT_ID())
            id_res = self.db.execute_query("SELECT LAST_INSERT_ID() as id")
            if hasattr(id_res, "fetchone"):
                row = id_res.fetchone()
            else:
                row = id_res[0] if id_res else None
            nfe_id = row["id"] if row and "id" in row else venda_id

            # 3) Inserir itens em nfe_itens
            q_insert_item = """
                INSERT INTO nfe_itens (
                    nfe_id, nfe_nota_id, product_id, numero_item,
                    codigo_produto, descricao, ncm, cfop,
                    unidade_comercial, quantidade_comercial,
                    valor_unitario_comercial, valor_total_bruto, valor_total_produto,
                    valor_icms, valor_ipi, valor_pis, valor_cofins,
                    valor_ibs, valor_cbs, valor_is
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
            """

            for idx, item in enumerate(itens, start=1):
                qtd = float(item.get("quantidade", 0))
                valor_unit = float(item.get("valor_unitario", 0.0))
                valor_total = qtd * valor_unit

                aliq_icms = float(item.get("aliquota_icms", 0.0))
                aliq_ipi = float(item.get("aliquota_ipi", 0.0))
                aliq_pis = float(item.get("aliquota_pis", 0.0))
                aliq_cofins = float(item.get("aliquota_cofins", 0.0))
                aliq_ibs = float(item.get("aliquota_ibs", 0.0))
                aliq_cbs = float(item.get("aliquota_cbs", 0.0))
                aliq_is = float(item.get("aliquota_is", 0.0))

                valor_icms = valor_total * (aliq_icms / 100.0)
                valor_ipi = valor_total * (aliq_ipi / 100.0) if item.get("tem_ipi") else 0.0
                valor_pis = valor_total * (aliq_pis / 100.0)
                valor_cofins = valor_total * (aliq_cofins / 100.0)
                valor_ibs = valor_total * (aliq_ibs / 100.0)
                valor_cbs = valor_total * (aliq_cbs / 100.0)
                valor_is = valor_total * (aliq_is / 100.0) if item.get("tem_is") else 0.0

                params_item = (
                    nfe_id, nfe_id, item.get("produto_id"), idx,
                    item.get("codigo", ""), item.get("descricao"),
                    item.get("ncm"), item.get("cfop"),
                    item.get("unidade", "UN"), qtd,
                    valor_unit, valor_total, valor_total,
                    valor_icms, valor_ipi, valor_pis, valor_cofins,
                    valor_ibs, valor_cbs, valor_is
                )
                self.db.execute_query(q_insert_item, params_item)

            return nfe_id

        except Exception as e:
            print(f"[SALVAR] Erro ao salvar NF-e: {e}")
            raise


# -------------------------
# Teste
# -------------------------
def testar_nfe_service(venda_id: int = 1, empresa_id: int = DEFAULT_EMPRESA_ID):
    print("\n" + "="*60)
    print("TESTE DO NFeService")
    print("="*60 + "\n")
    svc = NFeService()
    resultado = svc.gerar_nfe(venda_id=venda_id, empresa_id=empresa_id, serie=1, enviar_para_sefaz=False)
    if resultado.get("sucesso"):
        print("[OK] NF-e gerada com sucesso")
        print(f"Chave: {resultado.get('chave_acesso')}")
    else:
        print("[ERRO] Falha ao gerar NF-e")
        print(resultado)


if __name__ == "__main__":
    testar_nfe_service()
