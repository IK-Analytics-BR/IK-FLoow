import mysql.connector
import json
import os

def create_ncm_table():
    """Cria a tabela NCM no banco de dados."""
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
        cursor.execute("SHOW TABLES LIKE 'ncm'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("A tabela NCM já existe. Deseja recriá-la? (s/n)")
            response = input().lower()
            if response == 's':
                cursor.execute("DROP TABLE ncm")
                print("Tabela NCM removida.")
            else:
                print("Operação cancelada.")
                cursor.close()
                conn.close()
                return
        
        # Criar a tabela NCM
        print("Criando tabela NCM...")
        create_table_query = """
        CREATE TABLE ncm (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(20) NOT NULL,
            descricao TEXT NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim DATE NOT NULL,
            tipo_ato_ini VARCHAR(50),
            numero_ato_ini VARCHAR(20),
            ano_ato_ini VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY (codigo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_table_query)
        print("Tabela NCM criada com sucesso!")
        
        # Commit das alterações
        conn.commit()
        
    except mysql.connector.Error as e:
        print(f"Erro ao criar tabela NCM: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

def import_ncm_data(json_file_path):
    """Importa dados do arquivo JSON para a tabela NCM."""
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
        cursor.execute("SHOW TABLES LIKE 'ncm'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("A tabela NCM não existe. Crie a tabela primeiro.")
            cursor.close()
            conn.close()
            return
        
        # Carregar dados do arquivo JSON
        print(f"Carregando dados do arquivo: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Verificar a estrutura do JSON
        if 'Nomenclaturas' not in data:
            print("Estrutura do JSON inválida. A chave 'Nomenclaturas' não foi encontrada.")
            cursor.close()
            conn.close()
            return
        
        # Preparar a query de inserção
        insert_query = """
        INSERT INTO ncm (codigo, descricao, data_inicio, data_fim, tipo_ato_ini, numero_ato_ini, ano_ato_ini)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        descricao = VALUES(descricao),
        data_inicio = VALUES(data_inicio),
        data_fim = VALUES(data_fim),
        tipo_ato_ini = VALUES(tipo_ato_ini),
        numero_ato_ini = VALUES(numero_ato_ini),
        ano_ato_ini = VALUES(ano_ato_ini)
        """
        
        # Inserir dados na tabela
        print("Importando dados para a tabela NCM...")
        count = 0
        for item in data['Nomenclaturas']:
            codigo = item.get('Codigo', '')
            descricao = item.get('Descricao', '')
            data_inicio = item.get('Data_Inicio', '01/01/2000')
            data_fim = item.get('Data_Fim', '31/12/9999')
            tipo_ato_ini = item.get('Tipo_Ato_Ini', '')
            numero_ato_ini = item.get('Numero_Ato_Ini', '')
            ano_ato_ini = item.get('Ano_Ato_Ini', '')
            
            # Converter datas para o formato MySQL (YYYY-MM-DD)
            data_inicio_parts = data_inicio.split('/')
            data_inicio_mysql = f"{data_inicio_parts[2]}-{data_inicio_parts[1]}-{data_inicio_parts[0]}"
            
            data_fim_parts = data_fim.split('/')
            data_fim_mysql = f"{data_fim_parts[2]}-{data_fim_parts[1]}-{data_fim_parts[0]}"
            
            # Inserir na tabela
            try:
                cursor.execute(insert_query, (
                    codigo, 
                    descricao, 
                    data_inicio_mysql, 
                    data_fim_mysql, 
                    tipo_ato_ini, 
                    numero_ato_ini, 
                    ano_ato_ini
                ))
                count += 1
                
                # Commit a cada 1000 registros para evitar transações muito grandes
                if count % 1000 == 0:
                    conn.commit()
                    print(f"Importados {count} registros...")
            except Exception as e:
                print(f"Erro ao importar NCM {codigo}: {e}")
        
        # Commit final
        conn.commit()
        print(f"Importação concluída! Total de {count} registros importados.")
        
    except Exception as e:
        print(f"Erro ao importar dados NCM: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    # Criar a tabela NCM
    create_ncm_table()
    
    # Importar dados do arquivo JSON
    json_file_path = os.path.expanduser("~/Downloads/Tabela_NCM_Vigente_20250908.json")
    import_ncm_data(json_file_path)
