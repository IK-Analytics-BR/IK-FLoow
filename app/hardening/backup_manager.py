import os
import shutil
import datetime
import tarfile
import gzip
import logging
import schedule
import time
import threading
import json
import sqlite3
from pathlib import Path
import subprocess

# Configuração do logger
logger = logging.getLogger('backup')
logger.setLevel(logging.INFO)

# Garantir que o diretório de logs existe
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurar handler para arquivo de log
backup_file_handler = logging.FileHandler(os.path.join(log_dir, 'backup.log'))
backup_file_handler.setLevel(logging.INFO)

# Configurar formato do log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
backup_file_handler.setFormatter(formatter)
logger.addHandler(backup_file_handler)

class BackupManager:
    """Classe para gerenciar backups automáticos."""
    
    def __init__(self, app_root, db_uri, backup_dir=None, retention_days=30):
        """
        Inicializa o gerenciador de backup.
        
        Args:
            app_root (str): Diretório raiz da aplicação
            db_uri (str): URI de conexão com o banco de dados
            backup_dir (str, optional): Diretório para armazenar backups
            retention_days (int, optional): Número de dias para manter backups
        """
        self.app_root = Path(app_root)
        self.db_uri = db_uri
        
        # Configurar diretório de backup
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = self.app_root / 'backups'
        
        # Criar diretório de backup se não existir
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
        
        self.retention_days = retention_days
        self.scheduler_thread = None
        self.stop_event = threading.Event()
    
    def start_scheduler(self):
        """Inicia o agendador de backups."""
        # Agendar backup diário às 2:00 AM
        schedule.every().day.at("02:00").do(self.create_backup)
        
        # Agendar limpeza de backups antigos às 3:00 AM
        schedule.every().day.at("03:00").do(self.cleanup_old_backups)
        
        # Iniciar thread do agendador
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Agendador de backups iniciado")
    
    def stop_scheduler(self):
        """Para o agendador de backups."""
        if self.scheduler_thread:
            self.stop_event.set()
            self.scheduler_thread.join(timeout=5)
            logger.info("Agendador de backups parado")
    
    def _run_scheduler(self):
        """Executa o agendador em loop."""
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
    
    def create_backup(self):
        """Cria um backup completo do sistema."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            
            # Criar diretório temporário para o backup
            if not backup_path.exists():
                backup_path.mkdir()
            
            # Backup do banco de dados
            self._backup_database(backup_path)
            
            # Backup dos arquivos de configuração
            self._backup_config_files(backup_path)
            
            # Backup dos arquivos de upload
            self._backup_uploads(backup_path)
            
            # Criar arquivo compactado
            archive_path = self._create_archive(backup_path, timestamp)
            
            # Remover diretório temporário
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup criado com sucesso: {archive_path}")
            return archive_path
        
        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}")
            return None
    
    def _backup_database(self, backup_path):
        """Realiza backup do banco de dados."""
        db_backup_path = backup_path / "database"
        db_backup_path.mkdir()
        
        # Extrair informações da URI do banco de dados
        if self.db_uri.startswith('sqlite:///'):
            # SQLite
            db_path = self.db_uri.replace('sqlite:///', '')
            db_file = Path(db_path)
            
            if db_file.exists():
                # Conectar ao banco de dados
                conn = sqlite3.connect(db_path)
                
                # Backup para arquivo SQL
                with open(db_backup_path / "backup.sql", 'w') as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\n")
                
                conn.close()
                logger.info("Backup do SQLite concluído")
            else:
                logger.error(f"Arquivo de banco de dados não encontrado: {db_path}")
        
        elif self.db_uri.startswith('mysql://'):
            # MySQL
            # Extrair credenciais da URI
            # Formato: mysql://username:password@host:port/database
            parts = self.db_uri.replace('mysql://', '').split('@')
            credentials = parts[0].split(':')
            host_db = parts[1].split('/')
            
            username = credentials[0]
            password = credentials[1] if len(credentials) > 1 else ''
            host = host_db[0].split(':')[0]
            port = host_db[0].split(':')[1] if ':' in host_db[0] else '3306'
            database = host_db[1]
            
            # Criar arquivo de configuração temporário para mysqldump
            config_path = backup_path / "mysql.cnf"
            with open(config_path, 'w') as f:
                f.write(f"[client]\n")
                f.write(f"user={username}\n")
                f.write(f"password={password}\n")
                f.write(f"host={host}\n")
                f.write(f"port={port}\n")
            
            # Executar mysqldump
            output_file = db_backup_path / f"{database}.sql"
            try:
                subprocess.run(
                    [
                        "mysqldump",
                        f"--defaults-file={config_path}",
                        "--single-transaction",
                        "--routines",
                        "--triggers",
                        "--events",
                        database
                    ],
                    stdout=open(output_file, 'w'),
                    check=True
                )
                logger.info("Backup do MySQL concluído")
            except Exception as e:
                logger.error(f"Erro ao executar mysqldump: {str(e)}")
            
            # Remover arquivo de configuração temporário
            config_path.unlink()
        
        else:
            # Outros bancos de dados não suportados
            logger.warning(f"Tipo de banco de dados não suportado para backup: {self.db_uri}")
    
    def _backup_config_files(self, backup_path):
        """Realiza backup dos arquivos de configuração."""
        config_backup_path = backup_path / "config"
        config_backup_path.mkdir()
        
        # Listar arquivos de configuração para backup
        config_files = [
            self.app_root / "config.py",
            self.app_root / ".env",
            self.app_root / "instance" / "config.py"
        ]
        
        # Copiar arquivos de configuração
        for config_file in config_files:
            if config_file.exists():
                shutil.copy2(config_file, config_backup_path)
        
        logger.info("Backup dos arquivos de configuração concluído")
    
    def _backup_uploads(self, backup_path):
        """Realiza backup dos arquivos de upload."""
        uploads_dir = self.app_root / "app" / "static" / "uploads"
        if uploads_dir.exists():
            uploads_backup_path = backup_path / "uploads"
            shutil.copytree(uploads_dir, uploads_backup_path)
            logger.info("Backup dos arquivos de upload concluído")
    
    def _create_archive(self, backup_path, timestamp):
        """Cria arquivo compactado do backup."""
        archive_path = self.backup_dir / f"backup_{timestamp}.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=os.path.basename(backup_path))
        
        return archive_path
    
    def cleanup_old_backups(self):
        """Remove backups antigos com base na política de retenção."""
        try:
            # Calcular data limite
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
            
            # Listar arquivos de backup
            backup_files = list(self.backup_dir.glob("backup_*.tar.gz"))
            
            # Verificar cada arquivo
            for backup_file in backup_files:
                # Extrair timestamp do nome do arquivo
                try:
                    filename = backup_file.name
                    timestamp_str = filename.replace("backup_", "").replace(".tar.gz", "")
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Remover se for mais antigo que a data limite
                    if timestamp < cutoff_date:
                        backup_file.unlink()
                        logger.info(f"Backup antigo removido: {filename}")
                except Exception as e:
                    logger.warning(f"Erro ao processar arquivo de backup {backup_file}: {str(e)}")
            
            logger.info("Limpeza de backups antigos concluída")
        
        except Exception as e:
            logger.error(f"Erro ao limpar backups antigos: {str(e)}")
    
    def restore_backup(self, backup_file):
        """
        Restaura um backup.
        
        Args:
            backup_file (str): Caminho para o arquivo de backup
        
        Returns:
            bool: True se a restauração foi bem-sucedida, False caso contrário
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Arquivo de backup não encontrado: {backup_file}")
                return False
            
            # Criar diretório temporário para extração
            temp_dir = self.backup_dir / "temp_restore"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
            # Extrair arquivo
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=temp_dir)
            
            # Encontrar diretório de backup dentro do arquivo
            backup_dirs = [d for d in temp_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            if not backup_dirs:
                logger.error("Estrutura de backup inválida: diretório de backup não encontrado")
                shutil.rmtree(temp_dir)
                return False
            
            extracted_dir = backup_dirs[0]
            
            # Restaurar banco de dados
            self._restore_database(extracted_dir / "database")
            
            # Restaurar arquivos de configuração
            self._restore_config_files(extracted_dir / "config")
            
            # Restaurar arquivos de upload
            self._restore_uploads(extracted_dir / "uploads")
            
            # Limpar diretório temporário
            shutil.rmtree(temp_dir)
            
            logger.info(f"Backup restaurado com sucesso: {backup_file}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {str(e)}")
            return False
    
    def _restore_database(self, db_backup_path):
        """Restaura o banco de dados a partir do backup."""
        if not db_backup_path.exists():
            logger.warning("Diretório de backup do banco de dados não encontrado")
            return
        
        # Extrair informações da URI do banco de dados
        if self.db_uri.startswith('sqlite:///'):
            # SQLite
            db_path = self.db_uri.replace('sqlite:///', '')
            db_file = Path(db_path)
            
            # Criar backup do banco atual antes de restaurar
            if db_file.exists():
                backup_file = f"{db_file}.bak"
                shutil.copy2(db_file, backup_file)
                logger.info(f"Backup do banco de dados atual criado: {backup_file}")
            
            # Restaurar a partir do arquivo SQL
            sql_file = db_backup_path / "backup.sql"
            if sql_file.exists():
                # Criar novo banco de dados
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Executar script SQL
                with open(sql_file, 'r') as f:
                    script = f.read()
                    cursor.executescript(script)
                
                conn.commit()
                conn.close()
                logger.info("Banco de dados SQLite restaurado com sucesso")
            else:
                logger.error("Arquivo de backup SQL não encontrado")
        
        elif self.db_uri.startswith('mysql://'):
            # MySQL
            # Extrair credenciais da URI
            parts = self.db_uri.replace('mysql://', '').split('@')
            credentials = parts[0].split(':')
            host_db = parts[1].split('/')
            
            username = credentials[0]
            password = credentials[1] if len(credentials) > 1 else ''
            host = host_db[0].split(':')[0]
            port = host_db[0].split(':')[1] if ':' in host_db[0] else '3306'
            database = host_db[1]
            
            # Procurar arquivo SQL de backup
            sql_files = list(db_backup_path.glob("*.sql"))
            if sql_files:
                sql_file = sql_files[0]
                
                # Criar arquivo de configuração temporário para mysql
                config_path = db_backup_path / "mysql.cnf"
                with open(config_path, 'w') as f:
                    f.write(f"[client]\n")
                    f.write(f"user={username}\n")
                    f.write(f"password={password}\n")
                    f.write(f"host={host}\n")
                    f.write(f"port={port}\n")
                
                try:
                    # Restaurar banco de dados
                    subprocess.run(
                        [
                            "mysql",
                            f"--defaults-file={config_path}",
                            database
                        ],
                        stdin=open(sql_file, 'r'),
                        check=True
                    )
                    logger.info("Banco de dados MySQL restaurado com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao restaurar banco de dados MySQL: {str(e)}")
                
                # Remover arquivo de configuração temporário
                config_path.unlink()
            else:
                logger.error("Arquivo de backup SQL não encontrado")
        
        else:
            # Outros bancos de dados não suportados
            logger.warning(f"Tipo de banco de dados não suportado para restauração: {self.db_uri}")
    
    def _restore_config_files(self, config_backup_path):
        """Restaura os arquivos de configuração a partir do backup."""
        if not config_backup_path.exists():
            logger.warning("Diretório de backup de configuração não encontrado")
            return
        
        # Restaurar arquivos de configuração
        for config_file in config_backup_path.iterdir():
            if config_file.is_file():
                # Determinar destino
                if config_file.name == "config.py":
                    dest = self.app_root / "config.py"
                elif config_file.name == ".env":
                    dest = self.app_root / ".env"
                else:
                    # Criar diretório instance se não existir
                    instance_dir = self.app_root / "instance"
                    if not instance_dir.exists():
                        instance_dir.mkdir()
                    dest = instance_dir / config_file.name
                
                # Criar backup do arquivo atual
                if dest.exists():
                    backup_file = f"{dest}.bak"
                    shutil.copy2(dest, backup_file)
                
                # Copiar arquivo de backup
                shutil.copy2(config_file, dest)
        
        logger.info("Arquivos de configuração restaurados com sucesso")
    
    def _restore_uploads(self, uploads_backup_path):
        """Restaura os arquivos de upload a partir do backup."""
        if not uploads_backup_path.exists():
            logger.warning("Diretório de backup de uploads não encontrado")
            return
        
        # Diretório de destino
        uploads_dir = self.app_root / "app" / "static" / "uploads"
        
        # Criar backup do diretório atual
        if uploads_dir.exists():
            backup_dir = uploads_dir.with_name(f"uploads_bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.move(uploads_dir, backup_dir)
        
        # Copiar diretório de backup
        shutil.copytree(uploads_backup_path, uploads_dir)
        
        logger.info("Arquivos de upload restaurados com sucesso")
    
    def list_backups(self):
        """Lista todos os backups disponíveis."""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
            try:
                # Extrair timestamp do nome do arquivo
                filename = backup_file.name
                timestamp_str = filename.replace("backup_", "").replace(".tar.gz", "")
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # Obter tamanho do arquivo
                size_bytes = backup_file.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                
                backups.append({
                    "filename": filename,
                    "path": str(backup_file),
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "size_bytes": size_bytes,
                    "size_mb": round(size_mb, 2)
                })
            except Exception as e:
                logger.warning(f"Erro ao processar arquivo de backup {backup_file}: {str(e)}")
        
        # Ordenar por timestamp (mais recente primeiro)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return backups
