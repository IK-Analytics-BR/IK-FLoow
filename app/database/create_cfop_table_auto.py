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
            print("A tabela CFOP já existe. Recriando...")
            cursor.execute("DROP TABLE cfop")
            print("Tabela CFOP removida.")
        
        # Criar a tabela CFOP
        print("Criando tabela CFOP...")
        create_table_query = """
        CREATE TABLE cfop (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL,
            descricao TEXT NOT NULL,
            ind_nfe TINYINT DEFAULT 0,
            ind_comunica TINYINT DEFAULT 0,
            ind_transp TINYINT DEFAULT 0,
            ind_devol TINYINT DEFAULT 0,
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
            if 'CFOP' not in df.columns or 'Descrição Resumida' not in df.columns:
                # Tentar com nomes alternativos devido a problemas de codificação
                if 'CFOP' in df.columns:
                    codigo_col = 'CFOP'
                else:
                    print("Coluna CFOP não encontrada!")
                    return
                
                # Encontrar coluna de descrição
                desc_col = None
                for col in df.columns:
                    if 'Descri' in col:
                        desc_col = col
                        break
                
                if not desc_col:
                    print("Coluna de descrição não encontrada!")
                    return
                
                print(f"Usando colunas: Código={codigo_col}, Descrição={desc_col}")
            else:
                codigo_col = 'CFOP'
                desc_col = 'Descrição Resumida'
            
            # Identificar colunas de indicadores
            ind_nfe_col = next((col for col in df.columns if 'indNFe' in col), None)
            ind_comunica_col = next((col for col in df.columns if 'indComunica' in col), None)
            ind_transp_col = next((col for col in df.columns if 'indTransp' in col), None)
            ind_devol_col = next((col for col in df.columns if 'indDevol' in col), None)
            
        except Exception as e:
            print(f"Erro ao carregar arquivo Excel: {e}")
            cursor.close()
            conn.close()
            return
        
        # Preparar a query de inserção
        insert_query = """
        INSERT INTO cfop (codigo, descricao, ind_nfe, ind_comunica, ind_transp, ind_devol)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        descricao = VALUES(descricao),
        ind_nfe = VALUES(ind_nfe),
        ind_comunica = VALUES(ind_comunica),
        ind_transp = VALUES(ind_transp),
        ind_devol = VALUES(ind_devol)
        """
        
        # Inserir dados na tabela
        print("Importando dados para a tabela CFOP...")
        count = 0
        for _, row in df.iterrows():
            try:
                codigo = str(row[codigo_col]).strip()
                descricao = str(row[desc_col]).strip()
                
                # Obter valores dos indicadores
                ind_nfe = int(row[ind_nfe_col]) if ind_nfe_col and pd.notna(row[ind_nfe_col]) else 0
                ind_comunica = int(row[ind_comunica_col]) if ind_comunica_col and pd.notna(row[ind_comunica_col]) else 0
                ind_transp = int(row[ind_transp_col]) if ind_transp_col and pd.notna(row[ind_transp_col]) else 0
                ind_devol = int(row[ind_devol_col]) if ind_devol_col and pd.notna(row[ind_devol_col]) else 0
                
                # Verificar se o código é válido
                if not codigo or pd.isna(codigo) or codigo == 'nan':
                    continue
                
                # Inserir na tabela
                cursor.execute(insert_query, (codigo, descricao, ind_nfe, ind_comunica, ind_transp, ind_devol))
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
