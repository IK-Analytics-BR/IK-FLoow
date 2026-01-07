import mysql.connector
from mysql.connector import Error

# Configurações do banco de dados
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'aritana'
DB_NAME = 'supply_chain_system'

def create_segments_table():
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Criar tabela de segmentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS segments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Verificar se a coluna segment_id já existe na tabela customers
            cursor.execute("SHOW COLUMNS FROM customers LIKE 'segment_id'")
            result = cursor.fetchone()
            if not result:
                # Adicionar coluna de segmento na tabela de clientes
                cursor.execute("""
                    ALTER TABLE customers
                    ADD COLUMN segment_id INT NULL
                """)
                
                # Adicionar a chave estrangeira
                cursor.execute("""
                    ALTER TABLE customers
                    ADD CONSTRAINT fk_customer_segment
                        FOREIGN KEY (segment_id)
                        REFERENCES segments(id)
                        ON DELETE SET NULL
                """)
                print("Coluna segment_id adicionada à tabela customers")
            else:
                print("Coluna segment_id já existe na tabela customers")
            
            # Verificar se a coluna segment_id já existe na tabela suppliers
            cursor.execute("SHOW COLUMNS FROM suppliers LIKE 'segment_id'")
            result = cursor.fetchone()
            if not result:
                # Adicionar coluna de segmento na tabela de fornecedores
                cursor.execute("""
                    ALTER TABLE suppliers
                    ADD COLUMN segment_id INT NULL
                """)
                
                # Adicionar a chave estrangeira
                cursor.execute("""
                    ALTER TABLE suppliers
                    ADD CONSTRAINT fk_supplier_segment
                        FOREIGN KEY (segment_id)
                        REFERENCES segments(id)
                        ON DELETE SET NULL
                """)
                print("Coluna segment_id adicionada à tabela suppliers")
            else:
                print("Coluna segment_id já existe na tabela suppliers")
            
            # Inserir alguns segmentos iniciais
            cursor.execute("SELECT COUNT(*) FROM segments")
            count = cursor.fetchone()[0]
            
            if count == 0:
                segments = [
                    ('Indústria', 'Empresas do setor industrial'),
                    ('Comércio', 'Empresas do setor comercial'),
                    ('Serviços', 'Empresas do setor de serviços'),
                    ('Agronegócio', 'Empresas do setor agrícola'),
                    ('Tecnologia', 'Empresas do setor de tecnologia'),
                    ('Saúde', 'Empresas do setor de saúde'),
                    ('Educação', 'Empresas do setor educacional'),
                    ('Construção', 'Empresas do setor de construção civil'),
                    ('Transporte', 'Empresas do setor de transporte e logística'),
                    ('Alimentação', 'Empresas do setor alimentício')
                ]
                
                cursor.executemany("""
                    INSERT INTO segments (name, description) VALUES (%s, %s)
                """, segments)
                
                connection.commit()
                print(f"{len(segments)} segmentos inseridos com sucesso!")
            else:
                print(f"Tabela segments já contém {count} registros")
            
            print("Tabela segments criada com sucesso!")
            
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão com MySQL fechada")

if __name__ == "__main__":
    create_segments_table()
