"""
IMPORTAÇÃO INCREMENTAL DE NFe DE ENTRADA (Compras) - VERSÃO 2.0
- Upload de XML
- Verifica duplicidade por chave de acesso
- Não limpa dados existentes
- Descarta XML após processar
- Captura TODOS os campos (tributos, endereços, etc)
- Estrutura igual ao script de saída
- Ideal para produção na AWS
"""

import sys
import os
import tempfile
import shutil

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.nfe_xml_parser import NFeXMLParser
from database import get_db
import time
from datetime import datetime
from decimal import Decimal


class ImportadorNFeEntradaIncrementalV2:
    """Importador incremental de NFe de Entrada - Versão 2.0 (Completa)"""
    
    def __init__(self):
        self.db = get_db()
        self.parser = NFeXMLParser()
        self.temp_dir = None
        
        # Estatísticas
        self.total_arquivos = 0
        self.processados = 0
        self.sucesso = 0
        self.duplicados = 0
        self.erros = 0
        self.erros_detalhes = []
        
        # Contadores detalhados para KPI
        self.fornecedores_novos = 0
        self.fornecedores_existentes = 0
        self.produtos_novos = 0
        self.produtos_existentes = 0
        self.pedidos_criados = 0
        
        # Configuração para fluxo sequencial (HABILITADO para integração automática)
        self.criar_pedidos_automatico = True  # Cria pedidos automaticamente após NFe
    
    def _limpar_cnpj_cpf(self, valor):
        """Remove formatação de CNPJ/CPF (pontos, barras, hífens)"""
        if not valor:
            return valor
        return ''.join(filter(str.isdigit, str(valor)))
    
    def criar_diretorio_temporario(self):
        """Cria diretório temporário para upload"""
        self.temp_dir = tempfile.mkdtemp(prefix='nfe_entrada_')
        print(f"📁 Diretório temporário criado: {self.temp_dir}")
        return self.temp_dir
    
    def limpar_diretorio_temporario(self):
        """Remove diretório temporário após processamento"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🗑️ Diretório temporário removido")
    
    def verificar_duplicidade(self, chave_acesso):
        """Verifica se a NFe já foi importada pela chave de acesso"""
        resultado = self.db.fetch_one(
            "SELECT id FROM nfe_entrada_staging_notas WHERE chave_acesso = %s",
            (chave_acesso,)
        )
        return resultado is not None
    
    def importar_arquivo(self, caminho_xml):
        """Importa um arquivo XML individualmente"""
        
        self.total_arquivos += 1
        nome_arquivo = os.path.basename(caminho_xml)
        
        # Verificar conexão antes de operação crítica
        if not self.db.check_connection():
            self.erros += 1
            erro = f"❌ {nome_arquivo}: Erro de conexão com banco"
            self.erros_detalhes.append(erro)
            print(erro)
            return False
        
        try:
            # Parse do XML
            parse_result = self.parser.parse(caminho_xml)
            
            if not parse_result or 'nota' not in parse_result:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: XML inválido ou sem chave de acesso"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Extrair dados da estrutura aninhada
            nfe_data = parse_result['nota']
            nfe_data['itens'] = parse_result.get('itens', [])
            
            if 'chave_acesso' not in nfe_data:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: XML sem chave de acesso"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            chave_acesso = nfe_data['chave_acesso']
            
            # Verificar duplicidade
            if self.verificar_duplicidade(chave_acesso):
                self.duplicados += 1
                print(f"⚠️ {nome_arquivo}: Já importado (chave: {chave_acesso})")
                
                # Log de duplicado desabilitado temporariamente
                # self._registrar_log(
                #     nome_arquivo, caminho_xml, 'duplicado',
                #     'NFe já importada anteriormente', chave_acesso,
                #     nfe_data.get('numero_nota'), nfe_data.get('emit_cnpj'),
                #     nfe_data.get('emit_razao_social')
                # )
                return True
            
            # Buscar ou criar fornecedor (emitente = quem vende pra gente)
            supplier_id = self._buscar_ou_criar_fornecedor(nfe_data)
            
            if not supplier_id:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: Erro ao criar fornecedor"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Inserir nota na staging (com TODOS os campos)
            nota_id = self._inserir_nota_staging_completa(nfe_data, caminho_xml, supplier_id)
            
            if not nota_id:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: Erro ao inserir nota"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Inserir itens na staging (com TODOS os campos tributários)
            produtos_cache = {}  # Cache para evitar buscar o mesmo produto duas vezes
            itens_inseridos_sucesso = 0
            
            if 'itens' in nfe_data and nfe_data['itens']:
                total_itens = len(nfe_data['itens'])
                for idx, item in enumerate(nfe_data['itens'], 1):
                    try:
                        # Buscar ou criar produto (com cache)
                        codigo_produto = item.get('codigo_produto', '')
                        if codigo_produto not in produtos_cache:
                            produtos_cache[codigo_produto] = self._buscar_ou_criar_produto(item)
                        product_id = produtos_cache[codigo_produto]
                        self._inserir_item_staging_completo(nota_id, item, product_id)
                        itens_inseridos_sucesso += 1
                    except Exception as e:
                        print(f"   ⚠️ Erro item {idx}/{total_itens} (NFe {chave_acesso}): {str(e)[:100]}")
                
                if itens_inseridos_sucesso != total_itens:
                    print(f"   ⚠️ ATENÇÃO: {itens_inseridos_sucesso}/{total_itens} itens inseridos")
            
            # CRIAR PEDIDO DE COMPRA AUTOMATICAMENTE
            if self.criar_pedidos_automatico:
                try:
                    pedido_id = self._criar_pedido_compra(nfe_data, supplier_id, nota_id, produtos_cache)
                    if pedido_id:
                        print(f"   ✅ Pedido de compra criado: ID {pedido_id}")
                except Exception as e:
                    print(f"   ❌ ERRO ao criar pedido de compra: {e}")
                    # Não falha a importação da NFe se pedido falhar
                    pass
            
            # Log desabilitado temporariamente para evitar erro de estrutura
            # self._registrar_log(
            #     nome_arquivo, caminho_xml, 'sucesso',
            #     f'NFe importada com sucesso. Nota ID: {nota_id}',
            #     nfe_data.get('chave_acesso'), nfe_data.get('numero_nota'),
            #     nfe_data.get('emit_cnpj'),
            #     nfe_data.get('emit_razao_social'), nota_id
            # )
            
            # COMMIT EXPLÍCITO (garante persistência imediata)
            try:
                if hasattr(self.db, 'connection') and self.db.connection:
                    self.db.connection.commit()
            except Exception as e:
                print(f"⚠️ Aviso: Erro ao fazer commit: {e}")
            
            self.sucesso += 1
            self.processados += 1
            print(f"✅ {nome_arquivo}: Importado (NFe: {nfe_data.get('numero_nota')})")
            return True
            
        except Exception as e:
            self.erros += 1
            erro = f"❌ {nome_arquivo}: {str(e)}"
            self.erros_detalhes.append(erro)
            print(erro)
            import traceback
            traceback.print_exc()
            return False
    
    def _buscar_ou_criar_fornecedor(self, nfe_data):
        """Busca fornecedor existente ou cria novo"""
        
        emit_cnpj = nfe_data.get('emit_cnpj')
        
        if not emit_cnpj:
            print("⚠️ NFe sem CNPJ do fornecedor")
            return None
        
        # Limpar formatação do CNPJ (remover . / -)
        emit_cnpj = self._limpar_cnpj_cpf(emit_cnpj)
        
        # Buscar fornecedor existente
        fornecedor = self.db.fetch_one(
            "SELECT id FROM suppliers WHERE cnpj = %s",
            (emit_cnpj,)
        )
        
        if fornecedor:
            self.fornecedores_existentes += 1
            return fornecedor['id']
        
        # Criar novo fornecedor
        query = """
            INSERT INTO suppliers (
                name, cnpj, ie,
                phone, email, address, number, complement,
                neighborhood, city, state, cep
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """
        
        params = (
            nfe_data.get('emit_razao_social', 'Fornecedor Importado NFe'),
            emit_cnpj,
            nfe_data.get('emit_ie'),
            nfe_data.get('emit_telefone'),
            nfe_data.get('emit_email', f"fornecedor_{emit_cnpj}@nfe.importado"),
            nfe_data.get('emit_logradouro'),
            nfe_data.get('emit_numero'),
            nfe_data.get('emit_complemento'),
            nfe_data.get('emit_bairro'),
            nfe_data.get('emit_municipio'),
            nfe_data.get('emit_uf'),
            nfe_data.get('emit_cep'),
        )
        
        # Criando fornecedor silenciosamente
        fornecedor_id = self.db.execute(query, params)
        self.fornecedores_novos += 1
        print(f"      🏭 Criando fornecedor: {nfe_data.get('emit_razao_social', 'Sem nome')} ({fornecedor_id})")
        return fornecedor_id
    
    def _buscar_ou_criar_produto(self, item):
        """Busca produto existente ou cria novo"""
        
        codigo = item.get('codigo_produto')
        
        # Buscar produto existente pelo código interno
        produto = self.db.fetch_one(
            "SELECT id FROM products WHERE internal_code = %s",
            (codigo,)
        )
        
        if produto:
            self.produtos_existentes += 1
            return produto['id']
        
        # Buscar pelo GTIN/EAN
        gtin = item.get('gtin') or item.get('codigo_ean')
        if gtin and gtin != 'SEM GTIN':
            produto = self.db.fetch_one(
                "SELECT id FROM products WHERE barcode = %s",
                (gtin,)
            )
            if produto:
                self.produtos_existentes += 1
                return produto['id']
        
        # Criar novo produto (categoria 3 = Matéria Prima)
        query = """
            INSERT INTO products (
                name, internal_code, barcode, description,
                category_id, cost_price, price, unit_measure,
                ncm, cfop_out, category
            ) VALUES (
                %s, %s, %s, %s,
                3, %s, %s, %s,
                %s, %s, 'Importado NFe Entrada'
            )
        """
        
        params = (
            item.get('descricao', 'Produto Importado NFe')[:100],
            codigo,
            gtin if (gtin and gtin != 'SEM GTIN') else None,
            item.get('descricao'),
            item.get('valor_unitario_comercial'),
            item.get('valor_unitario_comercial'),
            item.get('unidade_comercial', 'UN'),  # Unidade do XML, padrão 'UN'
            item.get('ncm'),  # NCM do produto
            item.get('cfop'),  # CFOP (será cfop_out para entrada)
        )
        
        produto_id = self.db.execute(query, params)
        self.produtos_novos += 1
        print(f"      📦 Criando produto: {item.get('descricao', '')[:50]} ({codigo})")
        return produto_id
    
    def _criar_pedido_compra(self, nfe_data, supplier_id, nota_staging_id, produtos_cache=None):
        """Cria pedido de compra baseado na NFe de entrada"""
        
        print(f"   [PEDIDO] Criando pedido de compra...")
        
        # Criar pedido de compra
        query_pedido = """
            INSERT INTO purchase_orders (
                order_number, supplier_id, order_date, expected_delivery_date, 
                status, total_value, notes, created_by,
                chave_nfe, nfe_entrada_staging_id, numero_nfe, serie_nfe,
                data_emissao_nfe, data_entrada_nfe
            ) VALUES (
                %s, %s, %s, %s,
                'received', %s, %s, 1,
                %s, %s, %s, %s,
                %s, %s
            )
        """
        
        # Gerar número do pedido baseado na NFe
        order_number = f"NFE-{nfe_data.get('serie', '001')}-{nfe_data.get('numero_nota', '000000')}"
        
        # CORREÇÃO: Calcular total correto somando valor de cada item (vProd)
        total_pedido = 0
        if 'itens' in nfe_data and nfe_data['itens']:
            for item in nfe_data['itens']:
                # Usar valor_total_bruto que é o vProd do XML (valor correto por item)
                valor_item = float(item.get('valor_total_bruto', 0))
                total_pedido += valor_item
        
        params_pedido = (
            order_number,
            supplier_id,
            nfe_data.get('data_emissao'),
            nfe_data.get('data_entrada', nfe_data.get('data_emissao')),
            total_pedido,  # CORREÇÃO: Usar soma dos itens, não total_nota
            f"NFe {nfe_data.get('numero_nota')} - Série {nfe_data.get('serie')} - Chave: {nfe_data.get('chave_acesso')}",
            nfe_data.get('chave_acesso'),
            nota_staging_id,
            nfe_data.get('numero_nota'),
            nfe_data.get('serie'),
            nfe_data.get('data_emissao'),
            nfe_data.get('data_entrada', nfe_data.get('data_emissao'))
        )
        
        cursor = self.db.execute_query(query_pedido, params_pedido)
        pedido_id = cursor.lastrowid
        self.pedidos_criados += 1
        
        # Log para mostrar correção
        total_nota_antigo = float(nfe_data.get('total_nota', 0))
        if total_pedido != total_nota_antigo:
            print(f"      🛒 Pedido criado: ID {pedido_id}")
            print(f"         📊 Valor corrigido: R$ {total_pedido:,.2f} (era R$ {total_nota_antigo:,.2f})")
        else:
            print(f"      🛒 Pedido criado: ID {pedido_id} - R$ {total_pedido:,.2f}")
        
        # Criar itens do pedido (usando cache se disponível)
        if 'itens' in nfe_data and nfe_data['itens']:
            for item in nfe_data['itens']:
                if produtos_cache:
                    # Usar cache de produtos
                    codigo_produto = item.get('codigo_produto', '')
                    product_id = produtos_cache.get(codigo_produto)
                    if not product_id:
                        product_id = self._buscar_ou_criar_produto(item)
                        produtos_cache[codigo_produto] = product_id
                else:
                    # Buscar produto normalmente
                    product_id = self._buscar_ou_criar_produto(item)
                
                # Buscar o ID do item staging para rastreabilidade
                item_staging_id = None
                if 'staging_item_id' in item:
                    item_staging_id = item['staging_item_id']
                
                self._criar_item_pedido(pedido_id, item, product_id, item_staging_id)
        
        return pedido_id
    
    def _criar_item_pedido(self, pedido_id, item, product_id, item_staging_id=None):
        """Cria item do pedido de compra"""
        
        query = """
            INSERT INTO purchase_order_items (
                purchase_order_id, product_id, quantity, unit_price, 
                total_price, received_quantity, status,
                cfop, ncm, cest, ean, unidade_comercial,
                valor_total_bruto, valor_total_produto,
                valor_frete, valor_seguro, valor_outras_despesas,
                nfe_entrada_staging_item_id
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, 'received',
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s
            )
        """
        
        quantidade = int(float(item.get('quantidade_comercial', 1)))
        preco_unitario = float(item.get('valor_unitario_comercial', 0))
        # CORREÇÃO: Usar valor_total_bruto (vProd) que é o valor correto do XML
        valor_total_bruto = float(item.get('valor_total_bruto', 0))
        valor_total_produto = float(item.get('valor_total_produto', 0))
        
        params = (
            pedido_id,
            product_id,
            quantidade,
            preco_unitario,
            valor_total_bruto,  # total_price = valor bruto do item
            quantidade,  # received_quantity = quantity (já recebido via NFe)
            item.get('cfop'),
            item.get('ncm'),
            item.get('cest'),
            item.get('gtin'),
            item.get('unidade_comercial'),
            valor_total_bruto,
            valor_total_produto,
            float(item.get('valor_frete', 0)),
            float(item.get('valor_seguro', 0)),
            float(item.get('valor_outras_despesas', 0)),
            item_staging_id  # Para rastreabilidade
        )
        
        cursor = self.db.execute_query(query, params)
        item_id = cursor.lastrowid
        print(f"         📋 Item pedido: {item.get('descricao', '')[:30]} (Qtd: {quantidade})")
        
        return item_id
    
    def _inserir_nota_staging_completa(self, nfe_data, caminho_xml, supplier_id):
        """Insere nota na tabela de staging com TODOS os campos"""
        
        query = """
            INSERT INTO nfe_entrada_staging_notas (
                arquivo_xml, chave_acesso, numero_nota, serie, modelo,
                data_emissao, data_entrada, data_saida, natureza_operacao, tipo_operacao,
                emit_cnpj, emit_razao_social,
                emit_ie, emit_uf, emit_municipio,
                emit_logradouro, emit_numero, emit_complemento,
                emit_bairro, emit_cep, emit_telefone,
                dest_cnpj, dest_razao_social,
                dest_logradouro, dest_numero, dest_complemento,
                dest_bairro, dest_municipio, dest_uf, dest_cep,
                dest_email, dest_telefone,
                total_nota, total_produtos, total_frete, total_seguro,
                total_desconto, total_ipi, total_icms, total_icms_st,
                total_pis, total_cofins, total_outras_despesas,
                informacoes_complementares,
                status_importacao, supplier_id
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s,
                'pendente', %s
            )
        """
        
        params = (
            os.path.basename(caminho_xml),
            nfe_data.get('chave_acesso'),
            nfe_data.get('numero_nota'),
            nfe_data.get('serie'),
            nfe_data.get('modelo', '55'),
            nfe_data.get('data_emissao'),
            nfe_data.get('data_entrada'),
            nfe_data.get('data_saida'),
            nfe_data.get('natureza_operacao'),
            0,  # tipo_operacao: 0=Entrada
            # Emitente (Fornecedor)
            self._limpar_cnpj_cpf(nfe_data.get('emit_cnpj')),
            nfe_data.get('emit_razao_social'),
            nfe_data.get('emit_ie'),
            nfe_data.get('emit_uf'),
            nfe_data.get('emit_municipio'),
            nfe_data.get('emit_logradouro'),
            nfe_data.get('emit_numero'),
            nfe_data.get('emit_complemento'),
            nfe_data.get('emit_bairro'),
            nfe_data.get('emit_cep'),
            nfe_data.get('emit_telefone'),
            # Destinatário (Nossa Empresa)
            self._limpar_cnpj_cpf(nfe_data.get('dest_cnpj')),
            nfe_data.get('dest_razao_social'),
            nfe_data.get('dest_logradouro'),
            nfe_data.get('dest_numero'),
            nfe_data.get('dest_complemento'),
            nfe_data.get('dest_bairro'),
            nfe_data.get('dest_municipio'),
            nfe_data.get('dest_uf'),
            nfe_data.get('dest_cep'),
            nfe_data.get('dest_email'),
            nfe_data.get('dest_telefone'),
            # Totais
            nfe_data.get('total_nota'),
            nfe_data.get('total_produtos'),
            nfe_data.get('total_frete', 0),
            nfe_data.get('total_seguro', 0),
            nfe_data.get('total_desconto', 0),
            nfe_data.get('total_ipi', 0),
            nfe_data.get('total_icms', 0),
            nfe_data.get('total_icms_st', 0),
            nfe_data.get('total_pis', 0),
            nfe_data.get('total_cofins', 0),
            nfe_data.get('total_outras_despesas', 0),
            # Informações Complementares
            nfe_data.get('informacoes_complementares'),
            # Status e Supplier
            supplier_id,
        )
        
        return self.db.execute(query, params)
    
    def _inserir_item_staging_completo(self, nota_id, item, product_id=None):
        """Insere item na tabela de staging com TODOS os campos tributários"""
        
        # CORREÇÃO: Ajustar valores unitários muito altos para caber na coluna DECIMAL(10,2)
        # Limite: 99.999,99
        LIMITE_VALOR_UNITARIO = 99999.99
        
        if item.get('valor_unitario_comercial') and float(item.get('valor_unitario_comercial', 0)) > LIMITE_VALOR_UNITARIO:
            print(f"   ⚠️ Valor unitário comercial muito alto: R$ {float(item.get('valor_unitario_comercial')):,.2f} - ajustando para R$ 99.999,99")
            item['valor_unitario_comercial'] = LIMITE_VALOR_UNITARIO
        
        if item.get('valor_unitario_tributavel') and float(item.get('valor_unitario_tributavel', 0)) > LIMITE_VALOR_UNITARIO:
            print(f"   ⚠️ Valor unitário tributável muito alto: R$ {float(item.get('valor_unitario_tributavel')):,.2f} - ajustando para R$ 99.999,99")
            item['valor_unitario_tributavel'] = LIMITE_VALOR_UNITARIO
        
        # CORREÇÃO: Garantir que quantidade_comercial tenha valor (campo obrigatório)
        if not item.get('quantidade_comercial'):
            item['quantidade_comercial'] = item.get('quantidade_tributavel', 1)
        
        # CORREÇÃO: Garantir que quantidade_tributavel tenha valor
        if not item.get('quantidade_tributavel'):
            item['quantidade_tributavel'] = item.get('quantidade_comercial', 1)
        
        # CORREÇÃO: Ajustar alíquotas muito altas para caber na coluna DECIMAL(10,2)
        # Limite: 100,00 (100%)
        LIMITE_ALIQUOTA = 100.00
        
        # Alíquotas ICMS
        if item.get('icms_aliquota') and float(item.get('icms_aliquota', 0)) > LIMITE_ALIQUOTA:
            item['icms_aliquota'] = LIMITE_ALIQUOTA
        if item.get('icms_st_aliquota') and float(item.get('icms_st_aliquota', 0)) > LIMITE_ALIQUOTA:
            item['icms_st_aliquota'] = LIMITE_ALIQUOTA
        
        # Alíquotas IPI
        if item.get('ipi_aliquota') and float(item.get('ipi_aliquota', 0)) > LIMITE_ALIQUOTA:
            item['ipi_aliquota'] = LIMITE_ALIQUOTA
        
        # Alíquotas PIS
        if item.get('pis_aliquota') and float(item.get('pis_aliquota', 0)) > LIMITE_ALIQUOTA:
            item['pis_aliquota'] = LIMITE_ALIQUOTA
        
        # Alíquotas COFINS
        if item.get('cofins_aliquota') and float(item.get('cofins_aliquota', 0)) > LIMITE_ALIQUOTA:
            item['cofins_aliquota'] = LIMITE_ALIQUOTA
        
        query = """
            INSERT INTO nfe_entrada_staging_itens (
                nfe_entrada_staging_nota_id, numero_item, codigo_produto,
                descricao, informacoes_adicionais,
                ncm, cest, cfop,
                unidade_comercial, unidade_tributavel,
                quantidade_comercial, valor_unitario_comercial,
                quantidade_tributavel, valor_unitario_tributavel,
                valor_total_produto, valor_frete, valor_seguro, valor_desconto,
                valor_outras_despesas, valor_total_bruto,
                icms_origem, icms_cst, icms_base_calculo, icms_aliquota, icms_valor,
                icms_st_base_calculo, icms_st_aliquota, icms_st_valor,
                ipi_cst, ipi_base_calculo, ipi_aliquota, ipi_valor,
                pis_cst, pis_base_calculo, pis_aliquota, pis_valor,
                cofins_cst, cofins_base_calculo, cofins_aliquota, cofins_valor,
                product_id
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s
            )
        """
        
        params = (
            nota_id,
            item.get('numero_item'),
            item.get('codigo_produto'),
            # Descrição
            item.get('descricao'),
            item.get('informacoes_adicionais'),
            # Classificações
            item.get('ncm'),
            item.get('cest'),
            item.get('cfop'),
            # Unidades
            item.get('unidade_comercial'),
            item.get('unidade_tributavel'),
            # Quantidades e Valores
            item.get('quantidade_comercial'),
            item.get('valor_unitario_comercial'),
            item.get('quantidade_tributavel'),
            item.get('valor_unitario_tributavel'),
            item.get('valor_total_produto', 0),
            item.get('valor_frete', 0),
            item.get('valor_seguro', 0),
            item.get('valor_desconto', 0),
            item.get('valor_outras_despesas', 0),
            item.get('valor_total_bruto', 0),
            # ICMS
            item.get('icms_origem'),
            item.get('icms_cst'),
            item.get('icms_base_calculo', 0),
            item.get('icms_aliquota', 0),
            item.get('icms_valor', 0),
            item.get('icms_st_base_calculo', 0),
            item.get('icms_st_aliquota', 0),
            item.get('icms_st_valor', 0),
            # IPI
            item.get('ipi_cst'),
            item.get('ipi_base_calculo', 0),
            item.get('ipi_aliquota', 0),
            item.get('ipi_valor', 0),
            # PIS
            item.get('pis_cst'),
            item.get('pis_base_calculo', 0),
            item.get('pis_aliquota', 0),
            item.get('pis_valor', 0),
            # COFINS
            item.get('cofins_cst'),
            item.get('cofins_base_calculo', 0),
            item.get('cofins_aliquota', 0),
            item.get('cofins_valor', 0),
            # Produto
            product_id,
        )
        
        return self.db.execute(query, params)
    
    def _registrar_log(self, arquivo_xml, caminho_completo, status, mensagem,
                       chave_acesso=None, numero_nota=None, emit_cnpj=None,
                       emit_razao_social=None, nota_staging_id=None):
        """Registra log de importação"""
        
        query = """
            INSERT INTO nfe_entrada_import_log (
                arquivo_xml, caminho_completo, status, mensagem,
                chave_acesso, numero_nota, emit_cnpj, emit_razao_social,
                nfe_entrada_staging_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            arquivo_xml,
            caminho_completo,
            status,
            mensagem,
            chave_acesso,
            numero_nota,
            emit_cnpj,
            emit_razao_social,
            nota_staging_id,
        )
        
        return self.db.execute(query, params)
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas da importação"""
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS DA IMPORTAÇÃO")
        print("="*60)
        
        print(f"\n📂 Total de arquivos: {self.total_arquivos}")
        print(f"📊 Estatísticas: {self.sucesso} sucessos, {self.duplicados} duplicados, {self.erros} erros")
        print(f"🛒 Pedidos criados: {self.pedidos_criados}")
        
        if self.erros_detalhes:
            print(f"\n❌ DETALHES DOS ERROS (primeiros 10):")
            for erro in self.erros_detalhes[:10]:
                print(f"   {erro}")

def importar_xml_files(lista_arquivos_xml):
    """
    Importa lista de arquivos XML (usado quando há upload)
    
    Args:
        lista_arquivos_xml: Lista de caminhos para arquivos XML
    
    Returns:
        dict: Estatísticas da importação
    """
    
    print("\n" + "="*60)
    print("IMPORTAÇÃO INCREMENTAL DE NFe DE ENTRADA v2.0")
    print("="*60)
    print(f"📁 Total de arquivos: {len(lista_arquivos_xml)}")
    
    importador = ImportadorNFeEntradaIncrementalV2()
    
    # Importar cada arquivo
    for i, caminho_xml in enumerate(lista_arquivos_xml):
        importador.importar_arquivo(caminho_xml)
        
        # RECONEXÃO A CADA 500 ARQUIVOS (evita timeout)
        if (i + 1) % 500 == 0:
            print(f"\n[INFO] Reconectando banco após {i + 1} arquivos...")
            try:
                importador.db.check_connection()
                print(f"[INFO] Reconexão OK")
            except Exception as e_db:
                print(f"[INFO] Erro na reconexão: {e_db}")
        
        # Pequeno delay a cada 1000 arquivos para aliviar carga no banco
        if (i + 1) % 1000 == 0:
            print(f"\n[INFO] Pausa de 2 segundos após {i + 1} arquivos...")
            time.sleep(2)
    
    # Mostrar estatísticas
    importador.mostrar_estatisticas()
    
    return {
        'total': importador.total_arquivos,
        'sucesso': importador.sucesso,
        'duplicados': importador.duplicados,
        'erros': importador.erros,
        'erros_detalhes': importador.erros_detalhes
    }


if __name__ == '__main__':
    # Exemplo de uso com pasta local
    if len(sys.argv) > 1:
        pasta_xml = sys.argv[1]
        
        if not os.path.exists(pasta_xml):
            print(f"❌ Pasta não encontrada: {pasta_xml}")
            sys.exit(1)
        
        # Listar XMLs
        arquivos_xml = [
            os.path.join(pasta_xml, f)
            for f in os.listdir(pasta_xml)
            if f.endswith('.xml')
        ]
        
        if not arquivos_xml:
            print(f"❌ Nenhum arquivo XML encontrado em: {pasta_xml}")
            sys.exit(1)
        
        # Importar
        stats = importar_xml_files(arquivos_xml)
        
        print("\n" + "="*60)
        print("🎉 IMPORTAÇÃO CONCLUÍDA!")
        print("="*60)
    else:
        print("Uso: python importar_nfe_entrada_incremental_v2.py PASTA_XML")
