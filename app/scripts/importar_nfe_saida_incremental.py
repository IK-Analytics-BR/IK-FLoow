"""
IMPORTAÇÃO INCREMENTAL DE NFe DE SAÍDA (Vendas)
- Upload de XML
- Verifica duplicidade por chave de acesso
- Não limpa dados existentes
- Descarta XML após processar
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


class ImportadorNFeSaidaIncremental:
    """Importador incremental de NFe de Saída"""
    
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
        
        # Contadores detalhados (NOVOS)
        self.clientes_novos = 0
        self.clientes_existentes = 0
        self.produtos_novos = 0
        self.produtos_existentes = 0
        self.vendas_criadas = 0
    
    def _limpar_cnpj_cpf(self, valor):
        """Remove formatação de CNPJ/CPF (pontos, barras, hífens)"""
        if not valor:
            return valor
        return ''.join(filter(str.isdigit, str(valor)))
    
    def criar_diretorio_temporario(self):
        """Cria diretório temporário para upload"""
        self.temp_dir = tempfile.mkdtemp(prefix='nfe_saida_')
        print(f"📁 Diretório temporário criado: {self.temp_dir}")
        return self.temp_dir
    
    def limpar_diretorio_temporario(self):
        """Remove diretório temporário após processamento"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🗑️ Diretório temporário removido")
    
    def verificar_duplicidade(self, chave_acesso):
        """Verifica se a NFe já foi importada pela chave de acesso"""
        # Verificar na tabela de vendas (usar coluna existente)
        resultado = self.db.fetch_one(
            "SELECT id FROM sales WHERE chave_acesso_nfe = %s",
            (chave_acesso,)
        )
        return resultado is not None
    
    def importar_arquivo(self, caminho_xml):
        """Importa um arquivo XML individualmente"""
        
        self.total_arquivos += 1
        nome_arquivo = os.path.basename(caminho_xml)
        
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
            nfe_data['xml_completo'] = parse_result.get('xml_original', '')
            
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
                return False  # Duplicado não é sucesso
            
            # Buscar ou criar empresa emitente (quem está vendendo)
            empresa_id = self._buscar_ou_criar_empresa(nfe_data)
            
            # Buscar ou criar cliente
            customer_id = self._buscar_ou_criar_cliente(nfe_data)
            
            if not customer_id:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: Erro ao criar cliente"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Criar venda
            sale_id = self._criar_venda(nfe_data, customer_id, empresa_id)
            
            if not sale_id:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: Erro ao criar venda"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Inserir itens da venda
            itens_inseridos_sucesso = 0
            
            if 'itens' in nfe_data and nfe_data['itens']:
                total_itens = len(nfe_data['itens'])
                for idx, item in enumerate(nfe_data['itens'], 1):
                    try:
                        self._inserir_item_venda(sale_id, item, nfe_data)
                        itens_inseridos_sucesso += 1
                    except Exception as e:
                        print(f"   ⚠️ Erro item {idx}/{total_itens} (NFe {chave_acesso}): {str(e)[:100]}")
                
                if itens_inseridos_sucesso != total_itens:
                    print(f"   ⚠️ ATENÇÃO: {itens_inseridos_sucesso}/{total_itens} itens inseridos")
            
            # Inserir também nas tabelas staging (para análises e relatórios)
            try:
                staging_nota_id = self._inserir_staging(nfe_data, customer_id, sale_id)
                if staging_nota_id and 'itens' in nfe_data and nfe_data['itens']:
                    for item in nfe_data['itens']:
                        # Buscar product_id para salvar no staging
                        product_id = self._buscar_ou_criar_produto(item)
                        self._inserir_item_staging(staging_nota_id, item, product_id)
            except Exception as e:
                print(f"   ⚠️⚠️⚠️ ERRO STAGING: {str(e)}")
                import traceback
                traceback.print_exc()
            
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
    
    def _buscar_ou_criar_empresa(self, nfe_data):
        """Busca empresa emitente ou cria nova"""
        
        cnpj_emit = self._limpar_cnpj_cpf(nfe_data.get('emit_cnpj'))
        print(f"   [EMPRESA] Buscando CNPJ: {cnpj_emit}")
        
        # Buscar empresa pelo CNPJ
        empresa = self.db.fetch_one(
            "SELECT id FROM empresas WHERE cnpj = %s",
            (cnpj_emit,)
        )
        
        if empresa:
            print(f"   [EMPRESA] ✅ Encontrada (ID: {empresa['id']})")
            return empresa['id']
        
        # Criar nova empresa
        print(f"   [EMPRESA] ⚠️ NÃO encontrada. CRIANDO...")
        query = """
            INSERT INTO empresas (
                razao_social, nome_fantasia, cnpj,
                inscricao_estadual, logradouro, numero,
                bairro, cidade, estado, cep, telefone
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """
        
        params = (
            nfe_data.get('emit_razao_social'),
            nfe_data.get('emit_nome_fantasia'),
            cnpj_emit,
            nfe_data.get('emit_inscricao_estadual'),
            nfe_data.get('emit_logradouro'),
            nfe_data.get('emit_numero'),
            nfe_data.get('emit_bairro'),
            nfe_data.get('emit_municipio'),
            nfe_data.get('emit_uf'),
            nfe_data.get('emit_cep'),
            nfe_data.get('emit_telefone'),
        )
        
        empresa_id = self.db.execute(query, params)
        print(f"   [EMPRESA] 🆕 CRIADA (ID: {empresa_id})")
        return empresa_id
    
    def _buscar_ou_criar_cliente(self, nfe_data):
        """Busca ou cria cliente baseado nos dados da NFe"""
        
        # Conexão gerenciada automaticamente pelo sistema de retry
        
        # Extrair documento (CNPJ ou CPF)
        cnpj_cpf = nfe_data.get('dest_cnpj_cpf', '').strip()
        
        if not cnpj_cpf:
            # Buscar cliente genérico "Consumidor Final"
            cliente = self.db.fetch_one(
                "SELECT id FROM customers WHERE name = 'CONSUMIDOR FINAL'"
            )
            if cliente:
                print(f"   [CLIENTE] ✅ Consumidor Final (ID: {cliente['id']})")
                self.clientes_existentes += 1
                return cliente['id']
            # Criar cliente genérico
            print(f"   [CLIENTE] 🆕 CRIANDO Consumidor Final...")
            query = """
                INSERT INTO customers (
                    name, cnpj, address, neighborhood, city, state, cep, phone, email
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            params = (
                'CONSUMIDOR FINAL',
                '',
                'Endereço não informado',
                'Bairro não informado', 
                'Cidade não informada',
                'UF',
                '00000000',
                '',
                ''
            )
            cliente_id = self.db.execute(query, params)
            self.clientes_novos += 1
            print(f"   [CLIENTE] 🆕 Consumidor Final CRIADO (ID: {cliente_id})")
            return cliente_id
        
        # Buscar cliente pelo CNPJ/CPF
        cliente = self.db.fetch_one(
            "SELECT id FROM customers WHERE cnpj = %s",
            (cnpj_cpf,)
        )
        
        if cliente:
            print(f"   [CLIENTE] ✅ Encontrado (ID: {cliente['id']})")
            self.clientes_existentes += 1
            return cliente['id']
        
        # Criar novo cliente
        print(f"   [CLIENTE] ⚠️ NÃO encontrado. CRIANDO...")
        query = """
            INSERT INTO customers (
                name, cnpj,
                address, neighborhood, city, state, cep,
                phone, email
            ) VALUES (
                %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s
            )
        """
        
        params = (
            nfe_data.get('dest_razao_social', 'Cliente Importado NFe'),
            cnpj_cpf,
            nfe_data.get('dest_logradouro') or 'Endereço não informado',
            nfe_data.get('dest_bairro') or 'Bairro não informado',
            nfe_data.get('dest_municipio') or 'Cidade não informada',
            nfe_data.get('dest_uf') or 'UF',
            nfe_data.get('dest_cep') or '00000000',
            nfe_data.get('dest_telefone') or '',
            nfe_data.get('dest_email') or '',
        )
        
        cliente_id = self.db.execute(query, params)
        self.clientes_novos += 1
        print(f"   [CLIENTE] 🆕 CRIADO (ID: {cliente_id})")
        return cliente_id
    
    def _criar_venda(self, nfe_data, customer_id, empresa_id=None):
        """Cria registro de venda"""
        print(f"   [VENDA] Criando venda...")
        
        query = """
            INSERT INTO sales (
                customer_id, empresa_id, sale_date, net_total, gross_total, discount_total,
                payment_method, status, origem_venda,
                notes, numero_nfe, serie_nfe, chave_acesso_nfe,
                data_emissao_nfe
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, 'confirmed', 'nfe_importada',
                %s, %s, %s, %s,
                %s
            )
        """
        
        # USAR TOTAIS DO XML (valores oficiais da NFe)
        total_produtos = float(nfe_data.get('total_produtos', 0))
        total_desconto = float(nfe_data.get('total_desconto', 0))
        
        # gross_total = total dos PRODUTOS (bruto, antes do desconto)
        # net_total = total dos PRODUTOS após desconto
        total_bruto = total_produtos
        total_liquido = total_produtos - total_desconto
        
        params = (
            customer_id,
            empresa_id,
            nfe_data.get('data_emissao'),
            total_liquido,    # net_total = total_produtos - desconto
            total_bruto,      # gross_total = total_produtos (bruto)
            total_desconto,   # discount_total do XML
            'nfe_importada',
            f"NFe {nfe_data.get('numero_nota')} importada automaticamente",
            nfe_data.get('numero_nota'),
            nfe_data.get('serie'),
            nfe_data.get('chave_acesso'),
            nfe_data.get('data_emissao'),
        )
        
        sale_id = self.db.execute(query, params)
        self.vendas_criadas += 1
        
        # Log da venda criada
        print(f"      💰 Venda criada: ID {sale_id} - R$ {total_bruto:,.2f}")
        return sale_id
    
    def _inserir_item_venda(self, sale_id, item, nfe_data):
        """Insere item da venda"""
        
        # Buscar produto pelo código ou criar novo
        product_id = self._buscar_ou_criar_produto(item)
        
        if not product_id:
            print(f"   ⚠️ Produto não encontrado/criado: {item.get('codigo_produto')}")
            return None
        
        # VALIDAÇÕES E AJUSTES (para evitar erros de overflow)
        LIMITE_VALOR_UNITARIO = 99999.99
        
        # Garantir quantidade
        quantidade = float(item.get('quantidade_comercial', 0))
        if not quantidade or quantidade <= 0:
            quantidade = float(item.get('quantidade_tributavel', 1))
        if not quantidade or quantidade <= 0:
            quantidade = 1.0
        
        # Usar valor_total_bruto (vProd) que é o valor OFICIAL do XML
        valor_bruto_item_xml = float(item.get('valor_total_bruto', 0))
        valor_desconto = float(item.get('valor_desconto', 0))
        
        # CALCULAR valor unitário a partir do bruto (para garantir consistência)
        # unit_price * quantity = valor_bruto_item
        valor_unitario = valor_bruto_item_xml / quantidade if quantidade > 0 else 0
        
        # Validar valor unitário (só para o campo unit_price, não afeta total!)
        if valor_unitario > LIMITE_VALOR_UNITARIO:
            valor_unitario = LIMITE_VALOR_UNITARIO
        
        # Calcular percentual: (desconto / valor_bruto) * 100
        discount_percent = (valor_desconto / valor_bruto_item_xml * 100) if valor_bruto_item_xml > 0 else 0
        
        # total_price = valor BRUTO DO XML (EXATO, sem recalcular!)
        # Para que a soma dos itens bata com sales.gross_total
        total_price = valor_bruto_item_xml
        
        query = """
            INSERT INTO sale_items (
                sale_id, product_id, quantity, unit_price,
                discount_percent, total_price
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            sale_id,
            product_id,
            quantidade,
            valor_unitario,
            discount_percent,
            total_price,
        )
        
        return self.db.execute(query, params)
    
    def _buscar_ou_criar_produto(self, item):
        """Busca produto existente ou cria novo"""
        
        codigo = item.get('codigo_produto')
        print(f"      [PRODUTO] Buscando código: {codigo}")
        
        # Buscar produto existente pelo código interno
        produto = self.db.fetch_one(
            "SELECT id FROM products WHERE internal_code = %s",
            (codigo,)
        )
        
        if produto:
            print(f"      [PRODUTO] ✅ Encontrado (ID: {produto['id']})")
            self.produtos_existentes += 1
            return produto['id']
        
        # Buscar pelo GTIN
        gtin = item.get('gtin')
        if gtin and gtin != 'SEM GTIN':
            produto = self.db.fetch_one(
                "SELECT id FROM products WHERE barcode = %s",
                (gtin,)
            )
            if produto:
                print(f"      [PRODUTO] ✅ Encontrado por GTIN (ID: {produto['id']})")
                self.produtos_existentes += 1
                return produto['id']
        
        # Criar novo produto (categoria 1 = Produto Acabado)
        print(f"      [PRODUTO] ⚠️ NÃO encontrado. CRIANDO...")
        query = """
            INSERT INTO products (
                name, internal_code, barcode, description,
                category_id, cost_price, price, unit_measure,
                ncm, cfop_out, category
            ) VALUES (
                %s, %s, %s, %s,
                1, %s, %s, %s,
                %s, %s, 'Importado NFe Saida'
            )
        """
        
        params = (
            item.get('descricao', 'Produto Importado NFe')[:100],
            codigo,
            gtin if gtin != 'SEM GTIN' else None,
            item.get('descricao'),
            item.get('valor_unitario_comercial'),
            item.get('valor_unitario_comercial'),
            item.get('unidade_comercial', 'UN'),  # Unidade do XML, padrão 'UN'
            item.get('ncm'),  # NCM do produto
            item.get('cfop'),  # CFOP (será cfop_out para saída)
        )
        
        produto_id = self.db.execute(query, params)
        self.produtos_novos += 1
        print(f"      [PRODUTO] 🆕 CRIADO (ID: {produto_id})")
        return produto_id
    
    def _inserir_staging(self, nfe_data, customer_id, sale_id):
        """Insere NFe na tabela staging para análises"""
        
        # Verificar se já existe
        existe = self.db.fetch_one(
            "SELECT id FROM nfe_staging_notas WHERE chave_acesso = %s",
            (nfe_data.get('chave_acesso'),)
        )
        
        if existe:
            return existe['id']
        
        query = """
            INSERT INTO nfe_staging_notas (
                chave_acesso, numero_nota, serie, modelo,
                tipo_operacao, data_emissao, data_saida,
                natureza_operacao,
                emit_cnpj, emit_razao_social, emit_nome_fantasia,
                emit_logradouro, emit_numero, emit_complemento,
                emit_bairro, emit_municipio, emit_uf, emit_cep,
                emit_telefone, emit_ie,
                dest_cnpj_cpf, dest_razao_social, dest_nome_fantasia,
                dest_logradouro, dest_numero, dest_complemento,
                dest_bairro, dest_municipio, dest_uf, dest_cep,
                dest_telefone, dest_ie, dest_email,
                total_produtos, total_desconto, total_frete,
                total_seguro, total_outras_despesas,
                total_icms, total_icms_st, total_ipi,
                total_pis, total_cofins, total_nota,
                customer_id, sale_id,
                status_importacao, arquivo_xml
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                'processada', %s
            )
        """
        
        params = (
            nfe_data.get('chave_acesso'),
            nfe_data.get('numero_nota'),
            nfe_data.get('serie'),
            nfe_data.get('modelo'),
            nfe_data.get('tipo_operacao'),
            nfe_data.get('data_emissao'),
            nfe_data.get('data_saida'),
            nfe_data.get('natureza_operacao'),
            # Emitente (sua empresa)
            nfe_data.get('emit_cnpj'),
            nfe_data.get('emit_razao_social'),
            nfe_data.get('emit_nome_fantasia'),
            nfe_data.get('emit_logradouro'),
            nfe_data.get('emit_numero'),
            nfe_data.get('emit_complemento'),
            nfe_data.get('emit_bairro'),
            nfe_data.get('emit_municipio'),
            nfe_data.get('emit_uf'),
            nfe_data.get('emit_cep'),
            nfe_data.get('emit_telefone'),
            nfe_data.get('emit_ie'),
            # Destinatário (cliente)
            nfe_data.get('dest_cnpj_cpf'),
            nfe_data.get('dest_razao_social'),
            nfe_data.get('dest_nome_fantasia'),
            nfe_data.get('dest_logradouro'),
            nfe_data.get('dest_numero'),
            nfe_data.get('dest_complemento'),
            nfe_data.get('dest_bairro'),
            nfe_data.get('dest_municipio'),
            nfe_data.get('dest_uf'),
            nfe_data.get('dest_cep'),
            nfe_data.get('dest_telefone'),
            nfe_data.get('dest_ie'),
            nfe_data.get('dest_email'),
            # Totais
            nfe_data.get('total_produtos', 0),
            nfe_data.get('total_desconto', 0),
            nfe_data.get('total_frete', 0),
            nfe_data.get('total_seguro', 0),
            nfe_data.get('total_outras_despesas', 0),
            nfe_data.get('total_icms', 0),
            nfe_data.get('total_icms_st', 0),
            nfe_data.get('total_ipi', 0),
            nfe_data.get('total_pis', 0),
            nfe_data.get('total_cofins', 0),
            nfe_data.get('total_nota', 0),
            customer_id,
            sale_id,
            nfe_data.get('chave_acesso') + '.xml'
        )
        
        return self.db.execute(query, params)
    
    def _inserir_item_staging(self, staging_nota_id, item, product_id):
        """Insere item na tabela staging"""
        
        # Aplicar validações (mesmas do sale_items)
        LIMITE_VALOR_UNITARIO = 99999.99
        LIMITE_ALIQUOTA = 100.00
        
        # Garantir quantidade
        quantidade_comercial = item.get('quantidade_comercial')
        if not quantidade_comercial or float(quantidade_comercial) <= 0:
            quantidade_comercial = item.get('quantidade_tributavel', 1)
        
        quantidade_tributavel = item.get('quantidade_tributavel')
        if not quantidade_tributavel or float(quantidade_tributavel) <= 0:
            quantidade_tributavel = quantidade_comercial
        
        # Validar valores
        valor_unitario_comercial = float(item.get('valor_unitario_comercial', 0))
        if valor_unitario_comercial > LIMITE_VALOR_UNITARIO:
            valor_unitario_comercial = LIMITE_VALOR_UNITARIO
        
        valor_unitario_tributavel = float(item.get('valor_unitario_tributavel', 0))
        if valor_unitario_tributavel > LIMITE_VALOR_UNITARIO:
            valor_unitario_tributavel = LIMITE_VALOR_UNITARIO
        
        # Validar alíquotas
        aliquotas = {}
        for campo in ['icms_aliquota', 'icms_st_aliquota', 'ipi_aliquota', 'pis_aliquota', 'cofins_aliquota']:
            valor = float(item.get(campo, 0))
            if valor > LIMITE_ALIQUOTA:
                valor = LIMITE_ALIQUOTA
            aliquotas[campo] = valor
        
        query = """
            INSERT INTO nfe_staging_itens (
                nfe_staging_nota_id, numero_item, codigo_produto,
                descricao, ncm, cfop, cest,
                codigo_ean, codigo_ean_tributavel,
                unidade_comercial, unidade_tributavel,
                quantidade_comercial, valor_unitario_comercial,
                quantidade_tributavel, valor_unitario_tributavel,
                valor_total_bruto, valor_desconto, valor_frete,
                valor_seguro, valor_outras_despesas, valor_total_produto,
                icms_origem, icms_cst, icms_base_calculo, icms_aliquota, icms_valor,
                icms_st_base_calculo, icms_st_aliquota, icms_st_valor,
                ipi_cst, ipi_base_calculo, ipi_aliquota, ipi_valor,
                pis_cst, pis_base_calculo, pis_aliquota, pis_valor,
                cofins_cst, cofins_base_calculo, cofins_aliquota, cofins_valor,
                informacoes_adicionais, product_id
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
        """
        
        params = (
            staging_nota_id,
            item.get('numero_item'),
            item.get('codigo_produto'),
            item.get('descricao'),
            item.get('ncm'),
            item.get('cfop'),
            item.get('cest'),
            item.get('gtin'),
            item.get('gtin_tributavel'),
            item.get('unidade_comercial'),
            item.get('unidade_tributavel'),
            quantidade_comercial,
            valor_unitario_comercial,
            quantidade_tributavel,
            valor_unitario_tributavel,
            item.get('valor_total_bruto', 0),
            item.get('valor_desconto', 0),
            item.get('valor_frete', 0),
            item.get('valor_seguro', 0),
            item.get('valor_outras_despesas', 0),
            item.get('valor_total_produto', 0),
            item.get('icms_origem'),
            item.get('icms_cst'),
            item.get('icms_base_calculo', 0),
            aliquotas['icms_aliquota'],
            item.get('icms_valor', 0),
            item.get('icms_st_base_calculo', 0),
            aliquotas['icms_st_aliquota'],
            item.get('icms_st_valor', 0),
            item.get('ipi_cst'),
            item.get('ipi_base_calculo', 0),
            aliquotas['ipi_aliquota'],
            item.get('ipi_valor', 0),
            item.get('pis_cst'),
            item.get('pis_base_calculo', 0),
            aliquotas['pis_aliquota'],
            item.get('pis_valor', 0),
            item.get('cofins_cst'),
            item.get('cofins_base_calculo', 0),
            aliquotas['cofins_aliquota'],
            item.get('cofins_valor', 0),
            item.get('informacoes_adicionais'),
            product_id
        )
        
        return self.db.execute(query, params)
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas da importação"""
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS DA IMPORTAÇÃO")
        print("="*60)
        
        print(f"\n📂 Total de arquivos: {self.total_arquivos}")
        print(f"✅ Sucesso: {self.sucesso}")
        print(f"⚠️ Duplicados: {self.duplicados}")
        print(f"❌ Erros: {self.erros}")
        
        print(f"\n👥 CLIENTES:")
        print(f"   🆕 Novos criados: {self.clientes_novos}")
        print(f"   ✅ Já existentes: {self.clientes_existentes}")
        
        print(f"\n📦 PRODUTOS:")
        print(f"   🆕 Novos criados: {self.produtos_novos}")
        print(f"   ✅ Já existentes: {self.produtos_existentes}")
        
        print(f"\n💰 VENDAS:")
        print(f"   🆕 Criadas: {self.vendas_criadas}")
        
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
    print("IMPORTAÇÃO INCREMENTAL DE NFe DE SAÍDA")
    print("="*60)
    print(f"📁 Total de arquivos: {len(lista_arquivos_xml)}")
    
    importador = ImportadorNFeSaidaIncremental()
    
    # Importar cada arquivo
    import time
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
        print("Uso: python importar_nfe_saida_incremental.py PASTA_XML")
