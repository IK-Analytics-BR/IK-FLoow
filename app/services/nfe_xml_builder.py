# nfe_xml_builder.py
# -*- coding: utf-8 -*-
"""
Módulo de Construção de XML para NF-e
Conforme NT 2025.002 v1.31 (IBS/CBS/IS)
Leiaute v4.00

Responsável por:
- Gerar XML completo da NF-e (modelo 55)
- Incluir grupos IBS/CBS/IS (opcional)
- Calcular chave de acesso
- Validar contra XSD (função externa já implementada no projeto)
- Formatar conforme padrão SEFAZ
"""
from lxml import etree
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
import mysql.connector
from typing import Dict, List, Optional
from app.database import get_db
import os
import sys
import random
import re

# Ajustar precisão Decimal global (suficiente para cálculos)
getcontext().prec = 28

# Adicionar o diretório raiz ao path (se necessário)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from app.auto_config import DB_CONFIG
except Exception:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'aritana',
        'database': 'supply_chain_system'
    }


def only_digits(value: str) -> str:
    return re.sub(r'\D', '', str(value or ''))


def quantize_decimal(value, places=2) -> Decimal:
    """
    Normaliza e quantiza Decimal com arredondamento HALF_UP.
    places: número de casas decimais.
    """
    d = Decimal(str(value or '0')).quantize(Decimal('1.' + '0' * places), rounding=ROUND_HALF_UP)
    return d


class NFeXMLBuilder:
    """
    Construtor de XML para NF-e modelo 55
    """
    NAMESPACE = "http://www.portalfiscal.inf.br/nfe"
    VERSAO = "4.00"

    # UF -> código IBGE (mantido local)
    UF_CODIGO = {
        'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29',
        'CE': '23', 'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21',
        'MT': '51', 'MS': '50', 'MG': '31', 'PA': '15', 'PB': '25',
        'PR': '41', 'PE': '26', 'PI': '22', 'RJ': '33', 'RN': '24',
        'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42', 'SP': '35',
        'SE': '28', 'TO': '17'
    }

    def __init__(self, empresa_id: int, sale_id: int = None, destinatario_teste: Dict = None, itens_teste: List = None):
        self.empresa_id = empresa_id
        self.sale_id = sale_id
        self.destinatario_teste = destinatario_teste
        self.itens_teste = itens_teste

        # dados carregados
        self.empresa = None
        self.destinatario = None
        self.itens: List[Dict] = []
        self.pagamentos = []

        # números / chaves
        self.numero_nfe: Optional[int] = None
        self.serie_nfe: Optional[int] = None
        self.chave_acesso: Optional[str] = None
        self.codigo_numerico: Optional[str] = None
        self.digito_verificador: Optional[str] = None

        # totais (Decimal)
        self.total_produtos = Decimal('0.00')
        self.total_nfe = Decimal('0.00')
        self.total_bc_icms = Decimal('0.00')  # Base de cálculo do ICMS
        self.total_icms = Decimal('0.00')
        self.total_ipi = Decimal('0.00')
        self.total_pis = Decimal('0.00')
        self.total_cofins = Decimal('0.00')
        self.total_ibs = Decimal('0.00')
        self.total_cbs = Decimal('0.00')
        self.total_is = Decimal('0.00')
        # total aproximado de tributos (somatório de vTotTrib dos itens)
        self.total_trib_aprox = Decimal('0.00')

        # flags / controles
        self.habilitar_ibscbs = False  # controlado por empresa['aceita_ibscbs'] se disponível
        self.ambiente = '2'  # default homologação (2)

    def carregar_dados(self):
        """Carrega dados básicos da empresa, destinatário e itens de teste (se houver)."""
        db = get_db()
        try:
            resultado = db.execute_query("SELECT * FROM empresas WHERE id = %s", (self.empresa_id,))
            if hasattr(resultado, 'fetchone'):
                self.empresa = resultado.fetchone()
            else:
                self.empresa = resultado[0] if resultado else None
            if not self.empresa:
                raise Exception(f"Empresa {self.empresa_id} não encontrada")

            # set ambiente se presente
            self.ambiente = str(self.empresa.get('ambiente_nfe', '2'))

            # definir número/serie padrão vindo do cadastro (se disponível)
            # IMPORTANTE: Só usar do cadastro se não foi setado externamente
            if self.numero_nfe is None:
                self.numero_nfe = self.empresa.get('proximo_numero_nfe')
            if self.serie_nfe is None:
                self.serie_nfe = self.empresa.get('serie_nfe_padrao')

            # aceitar IBS/CBS se campo específico estiver marcado no cadastro
            self.habilitar_ibscbs = bool(self.empresa.get('aceita_ibscbs', False))

            # destinatário e itens de teste
            if self.destinatario_teste:
                self.destinatario = self.destinatario_teste
            if self.itens_teste:
                self.itens = self.itens_teste

        except Exception as e:
            raise Exception(f"Erro ao carregar dados: {e}")

    def gerar_codigo_numerico(self):
        """Gera código numérico aleatório de 8 dígitos (string)."""
        self.codigo_numerico = f"{random.randint(0, 99999999):08d}"
        return self.codigo_numerico

    def calcular_chave_acesso(self):
        """
        Calcula a chave de acesso (44 dígitos) com módulo 11.
        """
        if not self.empresa:
            raise Exception("Empresa não carregada")

        estado = (self.empresa.get('estado') or '').upper()
        cuf = self.UF_CODIGO.get(estado, '00')

        # AAMM (ano/mês atual)
        agora = datetime.now(timezone.utc).astimezone()
        aamm = agora.strftime('%y%m')

        # CNPJ (14)
        cnpj_raw = only_digits(self.empresa.get('cnpj', ''))
        if len(cnpj_raw) > 14:
            cnpj_raw = cnpj_raw[-14:]
        cnpj = cnpj_raw.zfill(14)

        mod = '55'
        serie = str(self.serie_nfe or 0).zfill(3)
        nnf = str(self.numero_nfe or 0).zfill(9)
        tpemis = '1'

        if not self.codigo_numerico:
            self.gerar_codigo_numerico()
        cnf = self.codigo_numerico

        chave_sem_dv = f"{cuf}{aamm}{cnpj}{mod}{serie}{nnf}{tpemis}{cnf}"

        # módulo 11
        soma = 0
        multiplicador = 2
        for i in range(len(chave_sem_dv) - 1, -1, -1):
            soma += int(chave_sem_dv[i]) * multiplicador
            multiplicador += 1
            if multiplicador > 9:
                multiplicador = 2
        resto = soma % 11
        dv = 0 if resto == 0 or resto == 1 else 11 - resto
        self.digito_verificador = str(dv)
        self.chave_acesso = chave_sem_dv + self.digito_verificador
        return self.chave_acesso

    # ---- helpers de XML ----
    def _elem(self, tag, text=None, ns=None, **attrs):
        if ns:
            el = etree.Element(f"{{{ns}}}{tag}", **attrs)
        else:
            el = etree.Element(tag, **attrs)
        if text is not None:
            el.text = str(text)
        return el

    def _sub(self, parent, tag, text=None, **attrs):
        """
        Cria SubElement SEM namespace explícito no tag.
        
        IMPORTANTE: Os elementos são criados sem namespace no tag para que
        a canonicalização C14N 1.0 do lxml funcione corretamente.
        O namespace é herdado do root (NFe) que define nsmap={None: NAMESPACE}.
        
        Quando elementos são criados com namespace explícito no tag (ex: {ns}tag),
        o lxml adiciona xmlns="" nos elementos netos durante a canonicalização,
        o que invalida a assinatura digital (erro 297 da SEFAZ).
        """
        el = etree.SubElement(parent, tag, **attrs)
        if text is not None:
            el.text = str(text)
        return el

    # ---- construção dos grupos ----
    def _build_ide(self, root_infnfe):
        ide = self._sub(root_infnfe, "ide")
        estado = (self.empresa.get('estado') or '').upper()
        self._sub(ide, "cUF", self.UF_CODIGO.get(estado, '00'))

        # cNF (código numérico)
        if not self.codigo_numerico:
            self.gerar_codigo_numerico()
        self._sub(ide, "cNF", self.codigo_numerico)

        self._sub(ide, "natOp", "VENDA DE MERCADORIA")
        self._sub(ide, "mod", "55")
        self._sub(ide, "serie", str(self.serie_nfe or 0))
        self._sub(ide, "nNF", str(self.numero_nfe or 0))

        # dhEmi no formato SEFAZ: YYYY-MM-DDTHH:MM:SS+HH:MM (sem microsegundos)
        now = datetime.now(timezone.utc).astimezone()
        dh_emi = now.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Adicionar ':' no offset (ex: -0400 -> -04:00)
        if len(dh_emi) >= 5 and dh_emi[-3] != ':':
            dh_emi = dh_emi[:-2] + ':' + dh_emi[-2:]
        self._sub(ide, "dhEmi", dh_emi)

        self._sub(ide, "tpNF", "1")
        
        # idDest: 1=Operação interna, 2=Operação interestadual, 3=Operação com exterior
        uf_emitente = self.empresa.get('estado', '').upper()
        uf_destinatario = self.destinatario.get('estado', '').upper()
        if uf_emitente == uf_destinatario:
            id_dest = "1"  # Operação interna
        else:
            id_dest = "2"  # Operação interestadual
        # guardar para uso na definição do CFOP dos itens
        self.id_dest = id_dest
        self._sub(ide, "idDest", id_dest)
        
        self._sub(ide, "cMunFG", str(self.empresa.get('codigo_municipio_ibge', '0')))
        self._sub(ide, "tpImp", "1")
        self._sub(ide, "tpEmis", "1")
        self._sub(ide, "cDV", self.digito_verificador or '')
        self._sub(ide, "tpAmb", str(self.empresa.get('ambiente_nfe', self.ambiente)))
        self._sub(ide, "finNFe", "1")
        self._sub(ide, "indFinal", "1")
        self._sub(ide, "indPres", "1")
        self._sub(ide, "procEmi", "0")
        self._sub(ide, "verProc", "SupplyChain v1.0")

    def _build_emit(self, root_infnfe):
        emit = self._sub(root_infnfe, "emit")
        cnpj = only_digits(self.empresa.get('cnpj', '')).zfill(14)
        self._sub(emit, "CNPJ", cnpj)
        self._sub(emit, "xNome", self.empresa.get('razao_social', ''))
        if self.empresa.get('nome_fantasia'):
            self._sub(emit, "xFant", self.empresa['nome_fantasia'])

        ender = self._sub(emit, "enderEmit")
        self._sub(ender, "xLgr", self.empresa.get('logradouro', ''))
        self._sub(ender, "nro", str(self.empresa.get('numero', 'S/N')))
        if self.empresa.get('complemento'):
            self._sub(ender, "xCpl", self.empresa['complemento'])
        self._sub(ender, "xBairro", self.empresa.get('bairro', ''))
        self._sub(ender, "cMun", str(self.empresa.get('codigo_municipio_ibge', '0')))
        self._sub(ender, "xMun", self.empresa.get('cidade', '').upper())
        self._sub(ender, "UF", (self.empresa.get('estado') or '').upper())
        cep = only_digits(self.empresa.get('cep', ''))
        self._sub(ender, "CEP", cep)
        self._sub(ender, "cPais", "1058")
        self._sub(ender, "xPais", "BRASIL")

        ie = self.empresa.get('inscricao_estadual') or ''
        if ie.strip() == '':
            ie = 'ISENTO'
        self._sub(emit, "IE", ie)
        self._sub(emit, "CRT", str(self.empresa.get('crt', '3')))

    def _build_dest(self, root_infnfe):
        if not self.destinatario:
            # Sem destinatário e em homologação, criar dest mínimo
            if self.ambiente == '2':
                dest = self._sub(root_infnfe, "dest")
                self._sub(dest, "xNome", "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL")
                ender = self._sub(dest, "enderDest")
                self._sub(ender, "xLgr", "Rua Teste")
                self._sub(ender, "nro", "123")
                self._sub(ender, "xBairro", "Centro")
                self._sub(ender, "cMun", "5002704")
                self._sub(ender, "xMun", "CAMPO GRANDE")
                self._sub(ender, "UF", "MS")
                self._sub(ender, "CEP", "79000000")
                self._sub(ender, "cPais", "1058")
                self._sub(ender, "xPais", "BRASIL")
                self._sub(dest, "indIEDest", "9")
            return
        
        dest = self._sub(root_infnfe, "dest")
        
        # CNPJ ou CPF do destinatário (dados reais)
        if self.destinatario.get('cnpj'):
            self._sub(dest, "CNPJ", only_digits(self.destinatario['cnpj']).zfill(14))
        elif self.destinatario.get('cpf'):
            self._sub(dest, "CPF", only_digits(self.destinatario['cpf']).zfill(11))
        
        # xNome: Em HOMOLOGAÇÃO, usar nome fixo obrigatório (antes da assinatura)
        # Em PRODUÇÃO, usar nome real do destinatário
        if self.ambiente == '2':
            self._sub(dest, "xNome", "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL")
        else:
            nome = self.destinatario.get('nome', '').strip()
            import re
            nome = re.sub(r'^[\d\.\s\-/]+', '', nome).strip()
            if not nome:
                nome = 'CLIENTE'
            self._sub(dest, "xNome", nome[:60])
        
        # Endereço do destinatário (dados reais)
        ender = self._sub(dest, "enderDest")
        self._sub(ender, "xLgr", self.destinatario.get('logradouro', 'RUA'))
        self._sub(ender, "nro", str(self.destinatario.get('numero', 'S/N')))
        if self.destinatario.get('complemento'):
            self._sub(ender, "xCpl", self.destinatario['complemento'])
        self._sub(ender, "xBairro", self.destinatario.get('bairro', 'CENTRO'))
        codigo_mun = str(self.destinatario.get('codigo_municipio') or self.destinatario.get('codigo_municipio_ibge') or '0')
        self._sub(ender, "cMun", codigo_mun)
        self._sub(ender, "xMun", self.destinatario.get('cidade', '').upper())
        self._sub(ender, "UF", (self.destinatario.get('estado') or '').upper())
        cep = only_digits(self.destinatario.get('cep', ''))
        self._sub(ender, "CEP", cep or '00000000')
        self._sub(ender, "cPais", "1058")
        self._sub(ender, "xPais", "BRASIL")
        
        # Indicador IE e IE do destinatário (dados reais)
        ie = self.destinatario.get('ie') or self.destinatario.get('inscricao_estadual')
        if ie and str(ie).strip() and str(ie).upper() not in ['ISENTO', 'ISENTA', '']:
            self._sub(dest, "indIEDest", "1")  # Contribuinte ICMS
            self._sub(dest, "IE", only_digits(str(ie)))
        else:
            self._sub(dest, "indIEDest", "9")  # Não contribuinte
            
        if self.destinatario.get('email'):
            self._sub(dest, "email", self.destinatario['email'])

    def _build_imposto(self, det_node, item: Dict):
        """
        Cria elemento <imposto> com ICMS, IPI (opcional), PIS e COFINS.
        Opcionalmente inclui IBSCBS/IS se habilitado.
        """
        imposto = self._sub(det_node, "imposto")
        icms = self._sub(imposto, "ICMS")
        
        valor_total = quantize_decimal(Decimal(str(item['quantidade'])) * Decimal(str(item['valor_unitario'])), 2)
        pICMS = Decimal(str(item.get('aliquota_icms', '0')))  # percentual

        # garantir valores default para todos os tributos do item
        valor_icms = Decimal('0.00')
        valor_ipi = Decimal('0.00')
        valor_pis = Decimal('0.00')
        valor_cofins = Decimal('0.00')
        
        # Se alíquota ICMS = 0, usar ICMS40 (Isenta), senão ICMS00 (Tributada integralmente)
        if pICMS == 0:
            # ICMS40 - Isenta (não tem base de cálculo)
            icms40 = self._sub(icms, "ICMS40")
            self._sub(icms40, "orig", str(item.get('orig', '0')))
            self._sub(icms40, "CST", "40")  # Isenta
            valor_icms = Decimal('0.00')
            bc_icms = Decimal('0.00')  # Sem BC para isenta
        else:
            # ICMS00 - Tributada integralmente
            icms00 = self._sub(icms, "ICMS00")
            self._sub(icms00, "orig", str(item.get('orig', '0')))
            self._sub(icms00, "CST", "00")
            self._sub(icms00, "modBC", "0")  # 0=Margem Valor Agregado
            self._sub(icms00, "vBC", f"{valor_total:.2f}")
            self._sub(icms00, "pICMS", f"{pICMS:.2f}")
            valor_icms = (valor_total * pICMS / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self._sub(icms00, "vICMS", f"{valor_icms:.2f}")
            bc_icms = valor_total  # BC = valor do item
        
        # acumular
        self.total_bc_icms += bc_icms
        self.total_icms += valor_icms

        # IPI (se aplicável)
        valor_ipi = Decimal('0.00')  # Inicializar
        if item.get('tem_ipi'):
            ipi = self._sub(imposto, "IPI")
            self._sub(ipi, "cEnq", item.get('cEnq', '999'))
            ipi_trib = self._sub(ipi, "IPITrib")
            self._sub(ipi_trib, "CST", str(item.get('cst_ipi', '50')))
            self._sub(ipi_trib, "vBC", f"{valor_total:.2f}")
            pIPI = Decimal(str(item.get('aliquota_ipi', '0')))
            self._sub(ipi_trib, "pIPI", f"{pIPI:.2f}")
            valor_ipi = (valor_total * pIPI / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self._sub(ipi_trib, "vIPI", f"{valor_ipi:.2f}")
            self.total_ipi += valor_ipi

        # PIS
        pis = self._sub(imposto, "PIS")
        pis_aliq = self._sub(pis, "PISAliq")
        self._sub(pis_aliq, "CST", str(item.get('cst_pis', '01')))
        self._sub(pis_aliq, "vBC", f"{valor_total:.2f}")
        pPIS = Decimal(str(item.get('aliquota_pis', '0')))
        self._sub(pis_aliq, "pPIS", f"{pPIS:.2f}")
        valor_pis = (valor_total * pPIS / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self._sub(pis_aliq, "vPIS", f"{valor_pis:.2f}")
        self.total_pis += valor_pis

        # COFINS
        cofins = self._sub(imposto, "COFINS")
        cofins_aliq = self._sub(cofins, "COFINSAliq")
        self._sub(cofins_aliq, "CST", str(item.get('cst_cofins', '01')))
        self._sub(cofins_aliq, "vBC", f"{valor_total:.2f}")
        pCOF = Decimal(str(item.get('aliquota_cofins', '0')))
        self._sub(cofins_aliq, "pCOFINS", f"{pCOF:.2f}")
        valor_cofins = (valor_total * pCOF / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self._sub(cofins_aliq, "vCOFINS", f"{valor_cofins:.2f}")
        self.total_cofins += valor_cofins

        # vTotTrib aproximado do ITEM = ICMS + IPI + PIS + COFINS (Lei da Transparência 12.741/2012)
        valor_trib_item = (valor_icms + valor_ipi + valor_pis + valor_cofins).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        self.total_trib_aprox += valor_trib_item

        # IBSCBS/IS (opcional)
        if self.habilitar_ibscbs:
            # IBSCBS simplificado
            ibscbs = self._sub(imposto, "IBSCBS")
            self._sub(ibscbs, "CST", item.get('cst_ibscbs', '000'))
            # cClassTrib: primeiros 6 do NCM
            ncm = str(item.get('ncm', '00000000'))
            cclass_trib = (ncm[:6]).ljust(6, '0')
            self._sub(ibscbs, "cClassTrib", cclass_trib)
            g_ibscbs = self._sub(ibscbs, "gIBSCBS")
            self._sub(g_ibscbs, "vBC", f"{valor_total:.2f}")
            # IBS UF / Mun (exemplo: divide aliquota)
            aliquota_ibs_uf = Decimal(str(item.get('aliquota_ibs_uf', '6.25')))
            aliquota_ibs_mun = Decimal(str(item.get('aliquota_ibs_mun', '6.25')))
            vIBSUF = (valor_total * aliquota_ibs_uf / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            vIBSMUN = (valor_total * aliquota_ibs_mun / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            g_ibsuf = self._sub(g_ibscbs, "gIBSUF")
            self._sub(g_ibsuf, "pIBSUF", f"{aliquota_ibs_uf:.2f}")
            self._sub(g_ibsuf, "vIBSUF", f"{vIBSUF:.2f}")
            g_ibsmun = self._sub(g_ibscbs, "gIBSMun")
            self._sub(g_ibsmun, "pIBSMun", f"{aliquota_ibs_mun:.2f}")
            self._sub(g_ibsmun, "vIBSMun", f"{vIBSMUN:.2f}")
            vIBS = (vIBSUF + vIBSMUN).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self._sub(g_ibscbs, "vIBS", f"{vIBS:.2f}")
            self.total_ibs += vIBS

            # CBS
            g_cbs = self._sub(g_ibscbs, "gCBS")
            aliquota_cbs = Decimal(str(item.get('aliquota_cbs', '12.50')))
            self._sub(g_cbs, "pCBS", f"{aliquota_cbs:.2f}")
            vCBS = (valor_total * aliquota_cbs / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self._sub(g_cbs, "vCBS", f"{vCBS:.2f}")
            self.total_cbs += vCBS

        # IS (Imposto Seletivo) - aplicado se item['tem_is'] True
        if item.get('tem_is'):
            is_node = self._sub(imposto, "IS")
            self._sub(is_node, "vBC", f"{valor_total:.2f}")
            aliquota_is = Decimal(str(item.get('aliquota_is', '0')))
            self._sub(is_node, "pIS", f"{aliquota_is:.2f}")
            vIS = (valor_total * aliquota_is / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self._sub(is_node, "vIS", f"{vIS:.2f}")
            self.total_is += vIS

    def _build_det(self, root_infnfe):
        if not self.itens:
            return
        for idx, item in enumerate(self.itens, start=1):
            det = self._sub(root_infnfe, "det", nItem=str(idx))
            prod = self._sub(det, "prod")
            self._sub(prod, "cProd", item.get('codigo') or f'PROD{idx:03d}')
            # cEAN/cEANTrib: se não tiver GTIN válido, usar 'SEM GTIN' conforme NT
            ean = item.get('ean', '')
            ean_str = str(ean).strip() if ean is not None else ''
            if (not ean_str or ean_str.upper() == 'SEM GTIN' or
                    not ean_str.isdigit() or len(ean_str) not in [8, 12, 13, 14]):
                ean_str = 'SEM GTIN'
            self._sub(prod, "cEAN", ean_str)
            
            # Sanitizar descrição: remover caracteres especiais do início
            descricao = item.get('descricao', '').strip()
            # Remover hífens, underscores, pontos do início
            descricao = descricao.lstrip('-_. ')
            # Se ficou vazio, usar descrição genérica
            if not descricao:
                descricao = 'PRODUTO'
            self._sub(prod, "xProd", descricao[:1000])
            ncm_val = str(item.get('ncm', '00000000')).zfill(8)
            self._sub(prod, "NCM", ncm_val)

            # Ajustar CFOP conforme idDest (1=interno → 5xxx, 2=interestadual → 6xxx)
            cfop_raw = str(item.get('cfop', '5102') or '5102')
            cfop_val = cfop_raw.zfill(4)
            id_dest = getattr(self, 'id_dest', None)
            if id_dest == '1' and cfop_val.startswith('6'):
                # operação interna com CFOP interestadual → converter 6xxx para 5xxx
                cfop_val = '5' + cfop_val[1:]
            elif id_dest == '2' and cfop_val.startswith('5'):
                # operação interestadual com CFOP interno → converter 5xxx para 6xxx
                cfop_val = '6' + cfop_val[1:]
            self._sub(prod, "CFOP", cfop_val)
            self._sub(prod, "uCom", item.get('unidade', 'UN'))

            qCom = quantize_decimal(item.get('quantidade', 0), 4)
            self._sub(prod, "qCom", f"{qCom:.4f}")

            # unitários com 4 casas (conforme validação)
            vUnCom = Decimal(str(item.get('valor_unitario', '0'))).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            self._sub(prod, "vUnCom", f"{vUnCom:.4f}")

            valor_total = (qCom * vUnCom).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self._sub(prod, "vProd", f"{valor_total:.2f}")

            self._sub(prod, "cEANTrib", ean_str)
            self._sub(prod, "uTrib", item.get('unidade', 'UN'))
            self._sub(prod, "qTrib", f"{qCom:.4f}")
            self._sub(prod, "vUnTrib", f"{vUnCom:.4f}")
            self._sub(prod, "indTot", "1")

            # atualiza total de produtos
            self.total_produtos += valor_total

            # construir grupo imposto por item
            self._build_imposto(det, item)

        # fim loop de itens

    def _build_total(self, root_infnfe):
        total = self._sub(root_infnfe, "total")
        icms_tot = self._sub(total, "ICMSTot")
        self._sub(icms_tot, "vBC", f"{self.total_bc_icms:.2f}")  # BC = soma das BCs dos itens
        self._sub(icms_tot, "vICMS", f"{self.total_icms:.2f}")
        self._sub(icms_tot, "vICMSDeson", "0.00")
        self._sub(icms_tot, "vFCP", "0.00")
        self._sub(icms_tot, "vBCST", "0.00")
        self._sub(icms_tot, "vST", "0.00")
        self._sub(icms_tot, "vFCPST", "0.00")
        self._sub(icms_tot, "vFCPSTRet", "0.00")
        self._sub(icms_tot, "vProd", f"{self.total_produtos:.2f}")
        self._sub(icms_tot, "vFrete", "0.00")
        self._sub(icms_tot, "vSeg", "0.00")
        self._sub(icms_tot, "vDesc", "0.00")
        self._sub(icms_tot, "vII", "0.00")
        self._sub(icms_tot, "vIPI", f"{self.total_ipi:.2f}")
        self._sub(icms_tot, "vIPIDevol", "0.00")
        self._sub(icms_tot, "vPIS", f"{self.total_pis:.2f}")
        self._sub(icms_tot, "vCOFINS", f"{self.total_cofins:.2f}")
        self._sub(icms_tot, "vOutro", "0.00")

        # total NF-e (sem IBS/CBS/IS se não habilitado)
        self.total_nfe = (self.total_produtos + self.total_ipi).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self._sub(icms_tot, "vNF", f"{self.total_nfe:.2f}")

        # vTotTrib aproximado (conforme Lei 12.741/2012)
        # DEVE ser igual a vICMS + vIPI + vPIS + vCOFINS para evitar rejeição
        total_tributos = (self.total_icms + self.total_ipi + self.total_pis + self.total_cofins).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self._sub(icms_tot, "vTotTrib", f"{total_tributos:.2f}")

        # Se IBSCBSTot habilitado, montar nó separado (fora do ICMSTot)
        if self.habilitar_ibscbs:
            ibscbs_tot = self._sub(total, "IBSCBSTot")
            self._sub(ibscbs_tot, "vBCIBSCBS", f"{self.total_produtos:.2f}")
            g_ibs = self._sub(ibscbs_tot, "gIBS")
            g_ibs_uf = self._sub(g_ibs, "gIBSUF")
            self._sub(g_ibs_uf, "vDif", "0.00")
            self._sub(g_ibs_uf, "vDevTrib", "0.00")
            self._sub(g_ibs_uf, "vIBSUF", f"{(self.total_ibs / 2):.2f}")
            g_ibs_mun = self._sub(g_ibs, "gIBSMun")
            self._sub(g_ibs_mun, "vDif", "0.00")
            self._sub(g_ibs_mun, "vDevTrib", "0.00")
            self._sub(g_ibs_mun, "vIBSMun", f"{(self.total_ibs / 2):.2f}")
            self._sub(g_ibs, "vIBS", f"{self.total_ibs:.2f}")
            self._sub(ibscbs_tot, "vCredPres", "0.00")
            self._sub(ibscbs_tot, "vCredPresCondSus", "0.00")
            g_cbs = self._sub(ibscbs_tot, "gCBS")
            self._sub(g_cbs, "vDif", "0.00")
            self._sub(g_cbs, "vDevTrib", "0.00")
            self._sub(g_cbs, "vCBS", f"{self.total_cbs:.2f}")
            self._sub(g_cbs, "vCredPres", "0.00")
            self._sub(g_cbs, "vCredPresCondSus", "0.00")
            if self.total_is > 0:
                is_tot = self._sub(ibscbs_tot, "ISTot")
                self._sub(is_tot, "vIS", f"{self.total_is:.2f}")

    def _build_transp(self, infnfe_node):
        transp = self._sub(infnfe_node, "transp")
        self._sub(transp, "modFrete", "9")
        vol = self._sub(transp, "vol")
        self._sub(vol, "qVol", "1")
        self._sub(vol, "esp", "CAIXA")
        peso_estimado = max(0.001, len(self.itens) * 2.0)
        self._sub(vol, "pesoL", f"{peso_estimado:.3f}")
        self._sub(vol, "pesoB", f"{(peso_estimado * 1.1):.3f}")

    def _build_pag(self, infnfe_node):
        pag = self._sub(infnfe_node, "pag")
        det_pag = self._sub(pag, "detPag")
        self._sub(det_pag, "indPag", "0")
        self._sub(det_pag, "tPag", "01")
        self._sub(det_pag, "vPag", f"{self.total_nfe:.2f}")

    def _build_infadic(self, infnfe_node):
        infadic = self._sub(infnfe_node, "infAdic")
        info_complementar = f"DOCUMENTO FISCAL. ICMS: R$ {self.total_icms:.2f} | PIS: R$ {self.total_pis:.2f} | COFINS: R$ {self.total_cofins:.2f}"
        if self.total_ipi > 0:
            info_complementar += f" | IPI: R$ {self.total_ipi:.2f}"
        if self.habilitar_ibscbs:
            info_complementar += f" | IBS: R$ {self.total_ibs:.2f} | CBS: R$ {self.total_cbs:.2f}"
        if self.total_is > 0:
            info_complementar += f" | IS: R$ {self.total_is:.2f}"
        self._sub(infadic, "infCpl", info_complementar)

    def _build_infresptec(self, infnfe_node):
        """Informações do Responsável Técnico - obrigatório para NF-e"""
        # Dados do responsável técnico (software house)
        resp_tec = self._sub(infnfe_node, "infRespTec")
        # CNPJ do responsável técnico (empresa desenvolvedora)
        cnpj_resp = self.empresa.get('cnpj_resp_tec') or '40169163000117'  # Usa CNPJ da empresa se não tiver
        self._sub(resp_tec, "CNPJ", cnpj_resp.replace('.', '').replace('/', '').replace('-', ''))
        # Nome do contato
        self._sub(resp_tec, "xContato", self.empresa.get('contato_resp_tec') or "Suporte Tecnico")
        # Email
        self._sub(resp_tec, "email", self.empresa.get('email_resp_tec') or "aritana@ikanalytics.com.br")
        # Telefone
        self._sub(resp_tec, "fone", self.empresa.get('fone_resp_tec') or "67981750909")

    # infNFeSupl é próprio de NFC-e (modelo 65) — NÃO incluir para NF-e (modelo 55)
    def _build_infnfesupl(self, root):
        infsupl = etree.SubElement(root, 'infNFeSupl')
        url_consulta = 'http://www.dfe.ms.gov.br/nfce/qrcode'
        etree.SubElement(infsupl, 'qrCode').text = f'<![CDATA[{url_consulta}?chNFe={self.chave_acesso}&nVersao=100&tpAmb={self.ambiente}]]>'
        etree.SubElement(infsupl, 'urlChave').text = url_consulta

    def build_xml_element(self):
        """
        Gera o elemento XML da NF-e (sem serializar).
        Retorna (root, infnfe) para permitir assinatura antes de serializar.
        """
        # carregar dados
        self.carregar_dados()
        # gerar código numérico e chave
        if not self.codigo_numerico:
            self.gerar_codigo_numerico()
        self.calcular_chave_acesso()

        # raiz com namespace padrão no nsmap - elementos SEM namespace no tag
        # para que a canonicalização C14N 1.0 do lxml funcione corretamente
        nsmap = {None: self.NAMESPACE}
        root = etree.Element("NFe", nsmap=nsmap)
        infnfe = etree.SubElement(root, "infNFe", versao=self.VERSAO, Id=f"NFe{self.chave_acesso}")

        # construir grupos
        self._build_ide(infnfe)
        self._build_emit(infnfe)
        self._build_dest(infnfe)
        self._build_det(infnfe)
        self._build_total(infnfe)
        self._build_transp(infnfe)
        self._build_pag(infnfe)
        self._build_infadic(infnfe)
        self._build_infresptec(infnfe)

        return root, infnfe

    def build_xml(self) -> str:
        """Gera o XML completo da NF-e e retorna string (sem assinatura)."""
        root, infnfe = self.build_xml_element()
        
        # IMPORTANTE: NÃO usar pretty_print=True, pois adiciona espaços/quebras
        # que alteram a canonicalização e invalidam a assinatura
        xml_bytes = etree.tostring(root, encoding='UTF-8', pretty_print=False, xml_declaration=True)
        return xml_bytes.decode('utf-8')

    def validar_xml(self, xml_string: str) -> tuple:
        """
        Validação simples via XSD (espera que o caminho do XSD esteja no projeto).
        Retorna (True, []) ou (False, [erros...])
        """
        try:
            schema_dir = os.path.join(os.path.dirname(__file__), '../../schemas/nfe/PL_010b_NT2025_002_v1.30')
            schema_path = os.path.join(schema_dir, 'nfe_v4.00.xsd')
            if not os.path.exists(schema_path):
                return False, [f"Schema XSD não encontrado: {schema_path}"]
            with open(schema_path, 'rb') as f:
                schema_doc = etree.parse(f)
                schema = etree.XMLSchema(schema_doc)
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))
            is_valid = schema.validate(xml_doc)
            if is_valid:
                return True, []
            else:
                erros = [f"Linha {e.line}: {e.message}" for e in schema.error_log]
                return False, erros
        except Exception as e:
            return False, [str(e)]


# ---- teste rápido (modo leve) ----
def testar_xml_builder_pequeno():
    destinatario = {
        'cnpj': '12.345.678/0001-90',
        'nome': 'EMPRESA TESTE LTDA',
        'logradouro': 'Rua Teste',
        'numero': '123',
        'bairro': 'Centro',
        'codigo_municipio': '5002704',
        'cidade': 'CAMPO GRANDE',
        'estado': 'MS',
        'cep': '79000000',
        'ind_ie': '9',
        'email': 'teste@empresa.com.br'
    }
    itens = [
        {'codigo': 'PROD001', 'descricao': 'PRODUTO TESTE 1', 'ncm': '84714900', 'cfop': '5102', 'unidade': 'UN',
         'quantidade': 10, 'valor_unitario': '100.00', 'ean': '7891234567890', 'tem_ipi': False,
         'aliquota_icms': '18.00', 'aliquota_pis': '1.65', 'aliquota_cofins': '7.60'},
        {'codigo': 'PROD002', 'descricao': 'PRODUTO TESTE 2 COM IPI', 'ncm': '84715000', 'cfop': '5102', 'unidade': 'UN',
         'quantidade': 5, 'valor_unitario': '250.00', 'ean': 'SEM GTIN', 'tem_ipi': True,
         'aliquota_icms': '18.00', 'aliquota_ipi': '10.00', 'aliquota_pis': '1.65', 'aliquota_cofins': '7.60'}
    ]

    builder = NFeXMLBuilder(empresa_id=9, destinatario_teste=destinatario, itens_teste=itens)
    xml = builder.build_xml()
    print(xml[:1000])
    valido, erros = builder.validar_xml(xml)
    print("Valido XSD:", valido)
    if not valido:
        print("Erros:", erros)


if __name__ == "__main__":
    testar_xml_builder_pequeno()
