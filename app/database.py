import mysql.connector
from mysql.connector import Error
import threading

# Importar configuração automática (detecta LOCAL vs AWS)
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from auto_config import config

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Estabelece conexão com o banco de dados MySQL - DETECÇÃO AUTOMÁTICA"""
        try:
            # Fechar conexão anterior se existir
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            thread_id = threading.current_thread().name
            print(f"\n[DATABASE-{thread_id}] Tentando conectar ao MySQL...")
            print(f"[DATABASE-{thread_id}] Ambiente: {config.ENVIRONMENT.upper()}")
            print(f"[DATABASE-{thread_id}] Host: {config.DB_CONFIG['host']}")
            
            # Configuração SIMPLES da conexão (SEM POOL para evitar problemas)
            db_config = {
                'host': config.DB_CONFIG.get('host', 'localhost'),
                'user': config.DB_CONFIG.get('user', 'root'),
                'password': config.DB_CONFIG.get('password', ''),
                'database': config.DB_CONFIG.get('database', 'supply_chain_system'),
                'port': config.DB_CONFIG.get('port', 3306),
                'autocommit': True,
                'connection_timeout': 60,
                'use_pure': True
            }
            
            self.connection = mysql.connector.connect(**db_config)
            
            # Verificação mais segura da conexão
            try:
                cursor_test = self.connection.cursor()
                cursor_test.execute("SELECT 1")
                cursor_test.fetchone()
                cursor_test.close()
                
                # HABILITAR AUTOCOMMIT (garante persistência imediata)
                self.connection.autocommit = True
                print(f"[DATABASE-{thread_id}] Conexão com o MySQL estabelecida com sucesso!")
                print(f"[DATABASE-{thread_id}] Autocommit HABILITADO")
                print(f"[DATABASE-{thread_id}] Modo: Conexão direta (sem pool)")
                return True
            except Exception as test_error:
                print(f"[DATABASE] Falha no teste de conexão: {test_error}")
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                return False
            
        except Error as e:
            print(f"[DATABASE] Erro ao conectar ao MySQL: {e}")
            # Tentar reconectar
            try:
                print("[DATABASE] Tentando reconectar...")
                if self.connection:
                    self.connection.close()
                self.connection = mysql.connector.connect(**db_config)
                # Testar conexão de forma segura
                try:
                    cursor_test = self.connection.cursor()
                    cursor_test.execute("SELECT 1")
                    cursor_test.fetchone()
                    cursor_test.close()
                    self.connection.autocommit = True
                    print("[DATABASE] Reconexão bem-sucedida!")
                    print("[DATABASE] Autocommit HABILITADO")
                except:
                    print("[DATABASE] Falha no teste de reconexão")
                    if self.connection:
                        self.connection.close()
                    self.connection = None
            except Error as e2:
                print(f"[DATABASE] Erro ao reconectar: {e2}")
    
    def check_connection(self):
        try:
            # Verificar se conexão existe e está ativa
            if self.connection is None:
                print("[DATABASE] Conexão não existe. Criando nova...")
                self.connect()
                return self.connection is not None
            
            # Testar conexão de forma segura sem usar is_connected()
            try:
                cursor_test = self.connection.cursor()
                cursor_test.execute("SELECT 1")
                cursor_test.fetchone()
                cursor_test.close()
                return True
            except Exception as conn_error:
                # Erro de conexão corrompida
                print(f"[DATABASE] Conexão corrompida ({type(conn_error).__name__}). Forçando reconexão...")
                
                # Forçar fechamento da conexão corrompida
                try:
                    if self.connection:
                        self.connection.close()
                except:
                    pass
                
                self.connection = None
                
                # Reconectar
                self.connect()
                return self.connection is not None
                
        except Exception as e:
            print(f"[DATABASE] Erro geral ao verificar conexão: {type(e).__name__}: {e}")
            # Última tentativa de reconexão
            try:
                if self.connection:
                    self.connection.close()
            except:
                pass
            self.connection = None
            self.connect()
            return self.connection is not None
    
    def execute_query(self, query, params=None, multi=False, max_retries=2):
        """Executa uma query e retorna o cursor com retry automático"""
        last_exception = None
        
        for tentativa in range(max_retries):
            try:
                # Verificação robusta de conexão
                if not self.connection:
                    print(f"[DATABASE] Sem conexão (tentativa {tentativa + 1}). Conectando...")
                    self.connect()
                
                # Testar se a conexão está realmente ativa
                try:
                    if self.connection and not self.connection.is_connected():
                        print(f"[DATABASE] Conexão perdida. Reconectando...")
                        self.connection = None
                        self.connect()
                except:
                    print(f"[DATABASE] Erro ao verificar conexão. Reconectando...")
                    self.connection = None
                    self.connect()
                
                # Verificar se a conexão foi estabelecida com sucesso
                if not self.connection:
                    raise Error("Falha ao estabelecer conexão com o banco de dados")
                
                # Executar query diretamente
                cursor = self.connection.cursor(dictionary=True)
                
                # Para procedures com múltiplos result sets
                if multi:
                    cursor.execute(query, params, multi=True) if params else cursor.execute(query, multi=True)
                else:
                    cursor.execute(query, params) if params else cursor.execute(query)
                
                return cursor
                
            except (Error, IndexError) as e:
                last_exception = e
                error_msg = str(e)
                
                # Detectar erros específicos de conexão corrompida
                if any(erro in error_msg.lower() for erro in [
                    'bytearray index out of range',
                    'connection lost',
                    'mysql server has gone away',
                    'lost connection',
                    'connection was killed'
                ]):
                    print(f"[DATABASE] Conexão corrompida ({error_msg}). Forçando reconexão...")
                    try:
                        if self.connection:
                            self.connection.close()
                    except:
                        pass
                    self.connection = None
                    
                    if tentativa < max_retries - 1:
                        print(f"[DATABASE] Tentativa {tentativa + 1} de {max_retries}. Aguardando 0.5s...")
                        import time
                        time.sleep(0.5)
                        continue
                else:
                    # Erro não relacionado à conexão, não tentar novamente
                    print(f"[DATABASE] Erro não relacionado à conexão: {e}")
                    raise e
        
        # Se chegou aqui, todas as tentativas falharam
        print(f"[DATABASE] Todas as {max_retries} tentativas falharam. Último erro: {last_exception}")
        raise last_exception
    
    def fetch_all(self, query, params=None):
        """Executa uma query e retorna todos os resultados"""
        cursor = self.execute_query(query, params)
        if cursor:
            result = cursor.fetchall()
            cursor.close()
            return result
        return []
    
    def fetch_one(self, query, params=None):
        """Executa uma query e retorna um único resultado"""
        cursor = self.execute_query(query, params)
        if cursor:
            result = cursor.fetchone()
            cursor.close()
            return result
        return None
    
    def call_procedure(self, procedure_name, params=None):
        """Chama uma stored procedure e retorna o resultado"""
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Executar procedure
            if params:
                cursor.callproc(procedure_name, params)
            else:
                cursor.callproc(procedure_name)
            
            # Obter resultados (procedures podem retornar múltiplos result sets)
            result = None
            for result_set in cursor.stored_results():
                result = result_set.fetchone()
                if result:
                    break
            
            self.connection.commit()
            cursor.close()
            
            print(f"[DEBUG] Resultado da procedure: {result}")
            return result
            
        except Error as e:
            print(f"[DATABASE] Erro ao chamar procedure: {e}")
            self.connection.rollback()
            raise e
    
    def insert(self, query, params=None):
        """Insere dados no banco e retorna o ID gerado"""
        print(f"\n[DEBUG] Executando INSERT: {query}")
        print(f"[DEBUG] Parâmetros: {params}")
        
        try:
            cursor = self.execute_query(query, params)
            if not cursor:
                # Se execute_query retornou None, lançar exceção para o chamador capturar
                raise Exception("Falha ao executar INSERT: cursor None")
            last_id = cursor.lastrowid
            self.connection.commit()  # Confirmar a transação
            print(f"[DATABASE] Inserção confirmada com ID: {last_id}")
            cursor.close()
            return last_id
        except Exception as e:
            print(f"[DATABASE] ERRO NA INSERÇÃO: {str(e)}")
            # Propagar para a camada superior exibir o motivo no modal
            raise
    
    def update(self, query, params=None):
        """Atualiza dados no banco e retorna o número de linhas afetadas"""
        cursor = self.execute_query(query, params)
        if cursor:
            affected_rows = cursor.rowcount
            self.connection.commit()  # Confirmar a transação
            print(f"[DATABASE] Atualização confirmada: {affected_rows} linhas afetadas")
            cursor.close()
            return affected_rows
        print("[DATABASE] Falha na atualização")
        return 0
    
    def delete(self, query, params=None):
        """Exclui dados do banco e retorna o número de linhas afetadas"""
        return self.update(query, params)
    
    def execute(self, query, params=None):
        """Executa um comando genérico (DDL/DML) e retorna lastrowid para INSERT ou linhas afetadas.
        Compatibilidade para rotas que usam db.execute().
        """
        cursor = self.execute_query(query, params)
        if cursor:
            # Para INSERT, retornar o ID da linha inserida (auto_increment)
            # Para UPDATE/DELETE, retornar número de linhas afetadas
            if query.strip().upper().startswith('INSERT'):
                result = cursor.lastrowid
            else:
                result = cursor.rowcount
            
            # Com autocommit=True, commit manual é redundante, mas mantido por segurança
            try:
                if not self.connection.autocommit:
                    self.connection.commit()
                    print(f"[DATABASE] Commit manual executado (autocommit OFF)")
            except Exception as e:
                print(f"[DATABASE] ❌ ERRO ao dar commit: {e}")
                raise  # Re-lança a exceção para não perder dados silenciosamente
            cursor.close()
            return result
        return 0
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        try:
            if self.connection:
                if self.connection.is_connected():
                    self.connection.close()
                    print("Conexão com o MySQL encerrada.")
                self.connection = None
        except:
            self.connection = None

# Thread-local storage para conexões independentes
_thread_local = threading.local()

def get_db():
    """Retorna uma instância de banco thread-safe"""
    if not hasattr(_thread_local, 'db'):
        _thread_local.db = Database()
        # Garantir que a conexão seja estabelecida
        if not _thread_local.db.connection:
            _thread_local.db.connect()
    return _thread_local.db
