"""
Script para popular tabelas de Empresas, Clientes e Produtos
a partir dos dados importados dos XMLs de NF-e
"""

import os
import sys
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')

def formatar_cnpj(cnpj):
    """Formata CNPJ no padrão 00.000.000/0000-00"""
    if not cnpj or len(cnpj) != 14:
        return cnpj
    return f"{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"

def formatar_cpf(cpf):
    """Formata CPF no padrão 000.000.000-00"""
    if not cpf or len(cpf) != 11:
        return cpf
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

def popular_empresas(conn):
    """Popula tabela de empresas a partir dos emitentes das NF-e"""
    print("\n" + "="*80)
    print("POPULANDO TABELA DE EMPRESAS (EMITENTES)")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # 1. Limpar tabela
    print("\n[1/3] Limpando tabela de empresas...")
    cursor.execute("TRUNCATE TABLE empresas")
    conn.commit()
    print("✓ Tabela limpa")
    
    # 2. Buscar emitentes únicos
    print("\n[2/3] Buscando emitentes únicos das NF-e...")
    query = """
        SELECT DISTINCT
            emit_cnpj,
            emit_razao_social,
            emit_nome_fantasia,
            emit_ie,
            emit_telefone,
            emit_cep,
            emit_logradouro,
            emit_numero,
            emit_complemento,
            emit_bairro,
            emit_municipio,
            emit_uf
        FROM nfe_staging_notas
        WHERE emit_cnpj IS NOT NULL 
          AND emit_cnpj != ''
          AND emit_razao_social IS NOT NULL
        GROUP BY 
            emit_cnpj,
            emit_razao_social,
            emit_nome_fantasia,
            emit_ie,
            emit_telefone,
            emit_cep,
            emit_logradouro,
            emit_numero,
            emit_complemento,
            emit_bairro,
            emit_municipio,
            emit_uf
        ORDER BY emit_razao_social
    """
    
    cursor.execute(query)
    emitentes = cursor.fetchall()
    print(f"✓ Encontrados {len(emitentes)} emitentes únicos")
    
    # 3. Inserir empresas
    print("\n[3/3] Inserindo empresas...")
    insert_query = """
        INSERT INTO empresas (
            razao_social, nome_fantasia, cnpj, inscricao_estadual,
            telefone, cep, logradouro, numero, complemento,
            bairro, cidade, estado, ativo, created_at
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """
    
    importados = 0
    erros = 0
    
    for emitente in emitentes:
        try:
            cnpj_formatado = formatar_cnpj(emitente['emit_cnpj'])
            nome_fantasia = emitente['emit_nome_fantasia'] or emitente['emit_razao_social']
            
            cursor.execute(insert_query, (
                emitente['emit_razao_social'],
                nome_fantasia,
                cnpj_formatado,
                emitente['emit_ie'],
                emitente['emit_telefone'],
                emitente['emit_cep'],
                emitente['emit_logradouro'],
                emitente['emit_numero'],
                emitente['emit_complemento'],
                emitente['emit_bairro'],
                emitente['emit_municipio'],
                emitente['emit_uf'],
                True,
                datetime.now()
            ))
            importados += 1
        except Exception as e:
            print(f"✗ Erro ao inserir empresa {emitente['emit_razao_social']}: {e}")
            erros += 1
    
    conn.commit()
    print(f"✓ {importados} empresas importadas com sucesso")
    if erros > 0:
        print(f"✗ {erros} erros encontrados")
    
    cursor.close()
    return importados, erros

def popular_clientes(conn):
    """Popula tabela de clientes a partir dos destinatários das NF-e"""
    print("\n" + "="*80)
    print("POPULANDO TABELA DE CLIENTES (DESTINATÁRIOS)")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # 1. Limpar tabela
    print("\n[1/3] Limpando tabela de clientes...")
    cursor.execute("TRUNCATE TABLE customers")
    conn.commit()
    print("✓ Tabela limpa")
    
    # 2. Buscar destinatários únicos
    print("\n[2/3] Buscando destinatários únicos das NF-e...")
    query = """
        SELECT DISTINCT
            dest_cnpj_cpf,
            dest_razao_social,
            dest_nome_fantasia,
            dest_telefone,
            dest_email,
            dest_cep,
            dest_logradouro,
            dest_numero,
            dest_complemento,
            dest_bairro,
            dest_municipio,
            dest_uf
        FROM nfe_staging_notas
        WHERE dest_cnpj_cpf IS NOT NULL 
          AND dest_cnpj_cpf != ''
          AND dest_razao_social IS NOT NULL
        GROUP BY 
            dest_cnpj_cpf,
            dest_razao_social,
            dest_nome_fantasia,
            dest_telefone,
            dest_email,
            dest_cep,
            dest_logradouro,
            dest_numero,
            dest_complemento,
            dest_bairro,
            dest_municipio,
            dest_uf
        ORDER BY dest_razao_social
    """
    
    cursor.execute(query)
    destinatarios = cursor.fetchall()
    print(f"✓ Encontrados {len(destinatarios)} destinatários únicos")
    
    # 3. Inserir clientes
    print("\n[3/3] Inserindo clientes...")
    insert_query = """
        INSERT INTO customers (
            name, razao_social, cnpj, phone, email,
            cep, address, number, complement, neighborhood,
            city, state, active, origem_cadastro, created_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """
    
    importados = 0
    erros = 0
    
    for dest in destinatarios:
        try:
            # Formatar documento
            doc = dest['dest_cnpj_cpf']
            if len(doc) == 14:
                doc_formatado = formatar_cnpj(doc)
            elif len(doc) == 11:
                doc_formatado = formatar_cpf(doc)
            else:
                doc_formatado = doc
            
            # Nome (preferir nome fantasia)
            name = dest['dest_nome_fantasia'] or dest['dest_razao_social']
            if not name:
                name = f"Cliente - {doc[:10]}"
            
            cursor.execute(insert_query, (
                name[:100],  # Limitar tamanho
                dest['dest_razao_social'],
                doc_formatado,
                dest['dest_telefone'],
                dest['dest_email'],
                dest['dest_cep'],
                dest['dest_logradouro'],
                dest['dest_numero'],
                dest['dest_complemento'],
                dest['dest_bairro'],
                dest['dest_municipio'],
                dest['dest_uf'],
                True,
                'importacao_nfe',
                datetime.now()
            ))
            importados += 1
        except Exception as e:
            print(f"✗ Erro ao inserir cliente {dest['dest_razao_social']}: {e}")
            erros += 1
    
    conn.commit()
    print(f"✓ {importados} clientes importados com sucesso")
    if erros > 0:
        print(f"✗ {erros} erros encontrados")
    
    cursor.close()
    return importados, erros

def verificar_campos_produtos(conn):
    """Verifica e adiciona campos necessários na tabela products"""
    print("\n" + "="*80)
    print("VERIFICANDO ESTRUTURA DA TABELA PRODUCTS")
    print("="*80)
    
    cursor = conn.cursor()
    
    campos_necessarios = [
        ("codigo_produto", "VARCHAR(60)", "Código do produto (fornecedor)", "name"),
        ("codigo_ean", "VARCHAR(14)", "Código de barras EAN", "codigo_produto"),
        ("ncm", "VARCHAR(8)", "NCM - Nomenclatura Comum do Mercosul", "codigo_ean"),
        ("cfop", "VARCHAR(4)", "CFOP padrão", "ncm"),
        ("unidade", "VARCHAR(10)", "Unidade (UN, KG, etc)", "cfop"),
        ("cest", "VARCHAR(7)", "Código CEST", "unidade"),
        ("origem_cadastro", "VARCHAR(50)", "Origem do cadastro", "cest")
    ]
    
    for campo, tipo, comentario, after in campos_necessarios:
        try:
            # Verificar se campo existe
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{DB_NAME}'
                AND TABLE_NAME = 'products'
                AND COLUMN_NAME = '{campo}'
            """)
            
            exists = cursor.fetchone()[0]
            
            if not exists:
                print(f"   Adicionando campo {campo}...")
                cursor.execute(f"""
                    ALTER TABLE products 
                    ADD COLUMN {campo} {tipo} 
                    COMMENT '{comentario}' 
                    AFTER {after}
                """)
                conn.commit()
                print(f"   ✓ Campo {campo} adicionado")
            else:
                print(f"   ✓ Campo {campo} já existe")
                
        except Exception as e:
            print(f"   ✗ Erro ao verificar/adicionar campo {campo}: {e}")
    
    cursor.close()

def popular_produtos(conn):
    """Popula tabela de produtos a partir dos itens das NF-e"""
    print("\n" + "="*80)
    print("POPULANDO TABELA DE PRODUTOS (ITENS DAS NF-e)")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # 1. Limpar tabela
    print("\n[1/3] Limpando tabela de produtos...")
    cursor.execute("TRUNCATE TABLE products")
    conn.commit()
    print("✓ Tabela limpa")
    
    # 2. Buscar produtos únicos
    print("\n[2/3] Buscando produtos únicos das NF-e...")
    query = """
        SELECT 
            codigo_produto,
            codigo_ean,
            descricao,
            ncm,
            cfop,
            cest,
            unidade_comercial,
            AVG(valor_unitario_comercial) as preco_medio,
            COUNT(*) as total_vendas
        FROM nfe_staging_itens
        WHERE descricao IS NOT NULL 
          AND descricao != ''
          AND codigo_produto IS NOT NULL
        GROUP BY 
            codigo_produto,
            codigo_ean,
            descricao,
            ncm,
            cfop,
            cest,
            unidade_comercial
        ORDER BY descricao
    """
    
    cursor.execute(query)
    produtos = cursor.fetchall()
    print(f"✓ Encontrados {len(produtos)} produtos únicos")
    
    # 3. Inserir produtos
    print("\n[3/3] Inserindo produtos...")
    insert_query = """
        INSERT INTO products (
            name, codigo_produto, codigo_ean, description,
            ncm, cfop, cest, unidade, price,
            stock, min_stock, active, origem_cadastro, created_at
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """
    
    importados = 0
    erros = 0
    
    for produto in produtos:
        try:
            name = produto['descricao'][:100]  # Limitar tamanho
            unidade = produto['unidade_comercial'] or 'UN'
            preco = round(float(produto['preco_medio']), 2)
            
            cursor.execute(insert_query, (
                name,
                produto['codigo_produto'],
                produto['codigo_ean'],
                produto['descricao'],
                produto['ncm'],
                produto['cfop'],
                produto['cest'],
                unidade,
                preco,
                0,  # stock inicial
                5,  # min_stock
                True,
                'importacao_nfe',
                datetime.now()
            ))
            importados += 1
            
            if importados % 100 == 0:
                print(f"   {importados} produtos processados...")
                
        except Exception as e:
            print(f"✗ Erro ao inserir produto {produto['descricao'][:50]}: {e}")
            erros += 1
    
    conn.commit()
    print(f"✓ {importados} produtos importados com sucesso")
    if erros > 0:
        print(f"✗ {erros} erros encontrados")
    
    # Adicionar índices
    print("\n[4/4] Criando índices...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_codigo_produto ON products(codigo_produto)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_codigo_ean ON products(codigo_ean)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ncm ON products(ncm)")
        conn.commit()
        print("✓ Índices criados")
    except Exception as e:
        print(f"✗ Erro ao criar índices: {e}")
    
    cursor.close()
    return importados, erros

def exibir_estatisticas(conn):
    """Exibe estatísticas finais"""
    print("\n" + "="*80)
    print("ESTATÍSTICAS FINAIS")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # Totais por tabela
    print("\n📊 TOTAIS POR TABELA:")
    
    cursor.execute("SELECT COUNT(*) as total FROM empresas")
    total_empresas = cursor.fetchone()['total']
    print(f"   Empresas: {total_empresas}")
    
    cursor.execute("SELECT COUNT(*) as total FROM customers")
    total_clientes = cursor.fetchone()['total']
    print(f"   Clientes: {total_clientes}")
    
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total_produtos = cursor.fetchone()['total']
    print(f"   Produtos: {total_produtos}")
    
    # Top 10 produtos por NCM
    print("\n📦 TOP 10 NCMs MAIS UTILIZADOS:")
    cursor.execute("""
        SELECT 
            ncm,
            COUNT(*) as total
        FROM products
        WHERE ncm IS NOT NULL
        GROUP BY ncm
        ORDER BY total DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"   {row['ncm']}: {row['total']} produtos")
    
    cursor.close()

def main():
    """Função principal"""
    print("\n" + "="*80)
    print("POPULAR DADOS DE NF-e PARA TABELAS PRINCIPAIS")
    print("="*80)
    print(f"\nConectando ao banco: {DB_NAME}@{DB_HOST}")
    
    try:
        # Conectar ao banco
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        print("✓ Conectado com sucesso\n")
        
        # Executar populações
        emp_importados, emp_erros = popular_empresas(conn)
        cli_importados, cli_erros = popular_clientes(conn)
        
        verificar_campos_produtos(conn)
        prod_importados, prod_erros = popular_produtos(conn)
        
        # Estatísticas
        exibir_estatisticas(conn)
        
        # Fechar conexão
        conn.close()
        
        print("\n" + "="*80)
        print("✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print(f"\nResumo:")
        print(f"   Empresas: {emp_importados} importadas, {emp_erros} erros")
        print(f"   Clientes: {cli_importados} importados, {cli_erros} erros")
        print(f"   Produtos: {prod_importados} importados, {prod_erros} erros")
        print(f"\nData/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
    except mysql.connector.Error as err:
        print(f"\n✗ ERRO DE CONEXÃO: {err}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
