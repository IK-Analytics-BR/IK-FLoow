import mysql.connector
import pandas as pd
import os

def create_cfop_table():
    """Cria a tabela CFOP no banco de dados."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("SHOW TABLES LIKE 'cfop'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("A tabela CFOP já existe. Deseja recriá-la? (s/n)")
            response = input().lower()
            if response == 's':
                cursor.execute("DROP TABLE cfop")
                print("Tabela CFOP removida.")
            else:
                print("Operação cancelada.")
                cursor.close()
                conn.close()
                return
        
        # Criar a tabela CFOP
        print("Criando tabela CFOP...")
        create_table_query = """
        CREATE TABLE cfop (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL,
            descricao TEXT NOT NULL,
            tipo VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY (codigo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_table_query)
        print("Tabela CFOP criada com sucesso!")
        
        # Commit das alterações
        conn.commit()
        
    except mysql.connector.Error as e:
        print(f"Erro ao criar tabela CFOP: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

def import_cfop_data(excel_file_path):
    """Importa dados do arquivo Excel para a tabela CFOP."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SHOW TABLES LIKE 'cfop'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("A tabela CFOP não existe. Crie a tabela primeiro.")
            cursor.close()
            conn.close()
            return
        
        # Carregar dados do arquivo Excel
        print(f"Carregando dados do arquivo: {excel_file_path}")
        try:
            df = pd.read_excel(excel_file_path)
            print("Arquivo Excel carregado com sucesso!")
            print(f"Colunas encontradas: {df.columns.tolist()}")
            
            # Verificar se as colunas necessárias existem
            required_columns = ['Código', 'Descrição', 'Tipo']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"Colunas necessárias não encontradas: {missing_columns}")
                print("Tentando identificar colunas por conteúdo...")
                
                # Mostrar as primeiras linhas para análise
                print("Primeiras linhas do arquivo:")
                print(df.head())
                
                # Tentar identificar colunas por conteúdo
                # Aqui você pode implementar lógica para identificar colunas por conteúdo
                # Por exemplo, procurar por colunas que contenham códigos CFOP (números com formato específico)
                
                # Para este exemplo, vamos assumir que as colunas estão presentes mas com nomes diferentes
                # Você precisará ajustar isso com base no formato real do seu arquivo
                column_mapping = {}
                for col in df.columns:
                    if 'cod' in col.lower() or 'cfop' in col.lower():
                        column_mapping['Código'] = col
                    elif 'desc' in col.lower():
                        column_mapping['Descrição'] = col
                    elif 'tipo' in col.lower() or 'nat' in col.lower():
                        column_mapping['Tipo'] = col
                
                print(f"Mapeamento de colunas identificado: {column_mapping}")
                
                # Verificar se todas as colunas foram mapeadas
                if len(column_mapping) < len(required_columns):
                    print("Não foi possível identificar todas as colunas necessárias.")
                    cursor.close()
                    conn.close()
                    return
                
                # Renomear colunas
                df = df.rename(columns=column_mapping)
            
        except Exception as e:
            print(f"Erro ao carregar arquivo Excel: {e}")
            cursor.close()
            conn.close()
            return
        
        # Preparar a query de inserção
        insert_query = """
        INSERT INTO cfop (codigo, descricao, tipo)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        descricao = VALUES(descricao),
        tipo = VALUES(tipo)
        """
        
        # Inserir dados na tabela
        print("Importando dados para a tabela CFOP...")
        count = 0
        for _, row in df.iterrows():
            try:
                codigo = str(row['Código']).strip()
                descricao = str(row['Descrição']).strip()
                tipo = str(row['Tipo']).strip() if 'Tipo' in row and pd.notna(row['Tipo']) else ''
                
                # Verificar se o código é válido
                if not codigo or pd.isna(codigo) or codigo == 'nan':
                    continue
                
                # Inserir na tabela
                cursor.execute(insert_query, (codigo, descricao, tipo))
                count += 1
                
                # Commit a cada 100 registros para evitar transações muito grandes
                if count % 100 == 0:
                    conn.commit()
                    print(f"Importados {count} registros...")
            except Exception as e:
                print(f"Erro ao importar CFOP {codigo}: {e}")
        
        # Commit final
        conn.commit()
        print(f"Importação concluída! Total de {count} registros importados.")
        
    except Exception as e:
        print(f"Erro ao importar dados CFOP: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    # Criar a tabela CFOP
    create_cfop_table()
    
    # Importar dados do arquivo Excel
    excel_file_path = os.path.expanduser("~/Downloads/160314_Tabela_CFOP.xlsx")
    import_cfop_data(excel_file_path)
