"""
SCRIPT INTEGRADO - IMPORTAÇÃO RECEITA FEDERAL V2
Importa Estabelecimentos + Empresas (com RAZÃO SOCIAL)
Com download automático e filtros de UF/CNAE
"""
import os
import requests
import pandas as pd
import mysql.connector
from io import BytesIO
from zipfile import ZipFile
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

# =========================================
# CONFIGURAÇÕES
# =========================================
BASE_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/2025-11/"
CHUNK_SIZE = 200000

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "aritana",
    "database": "supply_chain_system",
    "connection_timeout": 60,
    "autocommit": False,
    "use_pure": True,
    "sql_mode": "TRADITIONAL",
    "charset": "utf8mb4"
}

# Diretório para download dos arquivos
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads_receita')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

STATUS_FILE = os.path.join(os.path.dirname(__file__), 'importacao_status.json')

# =========================================
# FUNÇÕES AUXILIARES
# =========================================
def update_status(status_data):
    """Atualiza arquivo JSON com status"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

def verificar_arquivo_local(nome_arquivo):
    """Verifica se arquivo já existe localmente"""
    caminho = os.path.join(DOWNLOAD_DIR, nome_arquivo)
    return os.path.exists(caminho)

def baixar_arquivo(url, nome_arquivo, status):
    """Baixa arquivo se não existir localmente"""
    caminho = os.path.join(DOWNLOAD_DIR, nome_arquivo)
    
    if verificar_arquivo_local(nome_arquivo):
        print(f"[DEBUG] OK: Arquivo já existe: {nome_arquivo}")
        return caminho
    
    print(f"[DEBUG] Baixando: {nome_arquivo}")
    status['etapa'] = f'Baixando {nome_arquivo}...'
    update_status(status)
    
    try:
        r = requests.get(url, timeout=300, stream=True)
        r.raise_for_status()
        
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(caminho, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                
                if total_size > 0 and downloaded % (10 * 1024 * 1024) == 0:  # A cada 10MB
                    progresso = int((downloaded / total_size) * 100)
                    print(f"[DEBUG] {nome_arquivo}: {progresso}% baixado")
        
        print(f"[DEBUG] OK: Download concluído: {nome_arquivo}")
        return caminho
        
    except Exception as e:
        print(f"[DEBUG] ERRO: Erro ao baixar {nome_arquivo}: {e}")
        return None

def listar_arquivos_disponiveis(base_url, tipo="estabelecimento"):
    """Lista arquivos disponíveis no site da Receita Federal"""
    try:
        print(f"[DEBUG] Listando arquivos de {tipo} em {base_url}")
        r = requests.get(base_url, timeout=30)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        all_links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
        
        arquivos = []
        for href in all_links:
            if not href:
                continue
            href_lower = href.lower()
            
            if tipo == "estabelecimento":
                if "estabelecimento" in href_lower and href.endswith(".zip"):
                    arquivos.append(href)
            elif tipo == "empresa":
                if "empresa" in href_lower and href.endswith(".zip") and "estabelecimento" not in href_lower:
                    arquivos.append(href)
        
        arquivos.sort()
        print(f"[DEBUG] OK: Encontrados {len(arquivos)} arquivos de {tipo}")
        return arquivos
        
    except Exception as e:
        print(f"[DEBUG] ERRO: Erro ao listar arquivos: {e}")
        return []

# =========================================
# IMPORTAR EMPRESAS FILTRADAS (APENAS CNPJ_BASICO ESPECÍFICOS)
# =========================================
def importar_empresas_filtradas(conn, cnpjs_filtrados, status):
    """
    Importa APENAS empresas cujo CNPJ_BASICO está na lista de filtrados
    
    Args:
        conn: Conexão MySQL
        cnpjs_filtrados: Lista de CNPJ_BASICO (8 dígitos) para importar
        status: Dicionário de status
    
    Returns:
        Total de empresas importadas
    """
    if not cnpjs_filtrados:
        print("[DEBUG] AVISO: Lista de CNPJ_BASICO vazia. Nenhuma empresa para importar.")
        return 0
    
    cursor = conn.cursor()
    
    # Criar tabela empresas_receita se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas_receita (
            id INT AUTO_INCREMENT PRIMARY KEY,
            CNPJ_BASICO VARCHAR(8) NOT NULL,
            RAZAO_SOCIAL VARCHAR(150) NOT NULL,
            NATUREZA_JURIDICA VARCHAR(4) NULL,
            QUALIFICACAO_RESPONSAVEL VARCHAR(2) NULL,
            CAPITAL_SOCIAL DECIMAL(15,2) NULL,
            PORTE_EMPRESA VARCHAR(2) NULL COMMENT '01=ME, 03=EPP, 05=Demais',
            ENTE_FEDERATIVO VARCHAR(50) NULL,
            data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_cnpj_basico (CNPJ_BASICO),
            INDEX idx_razao_social (RAZAO_SOCIAL(50))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("[DEBUG] OK: Tabela empresas_receita verificada")
    
    # Converter lista para set (busca mais rápida)
    cnpjs_set = set(cnpjs_filtrados)
    print(f"[DEBUG] Buscando empresas para {len(cnpjs_set):,} CNPJ_BASICO únicos")
    
    # Verificar quais CNPJ_BASICO já existem (em lotes para evitar timeout)
    cnpjs_existentes = set()
    batch_size = 10000  # Processar 10k por vez
    
    print(f"[DEBUG] Verificando CNPJs existentes em lotes de {batch_size:,}...")
    
    for i in range(0, len(cnpjs_filtrados), batch_size):
        batch = cnpjs_filtrados[i:i + batch_size]
        placeholders = ','.join(['%s'] * len(batch))
        
        try:
            cursor.execute(f"SELECT CNPJ_BASICO FROM empresas_receita WHERE CNPJ_BASICO IN ({placeholders})", batch)
            batch_existentes = set(row[0] for row in cursor.fetchall())
            cnpjs_existentes.update(batch_existentes)
            
            if (i + batch_size) % 50000 == 0:  # Log a cada 50k
                print(f"[DEBUG] Verificados: {i + batch_size:,}/{len(cnpjs_filtrados):,} CNPJs")
                
        except Exception as e:
            print(f"[DEBUG] Erro ao verificar lote {i//batch_size + 1}: {e}")
            # Reconectar se necessário
            try:
                conn.ping(reconnect=True)
            except:
                pass
    
    cnpjs_faltantes = cnpjs_set - cnpjs_existentes
    
    if not cnpjs_faltantes:
        print(f"[DEBUG] OK: Todos os {len(cnpjs_set):,} CNPJ_BASICO já têm empresa cadastrada")
        return len(cnpjs_existentes)
    
    print(f"[DEBUG] AVISO: Faltam {len(cnpjs_faltantes):,} empresas. Buscando nos arquivos...")
    
    # Listar arquivos Empresas disponíveis
    arquivos_empresa = []
    
    # Tentar arquivos locais primeiro
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith('Empresas') and f.endswith('.csv'):
            arquivos_empresa.append(f)
    
    if not arquivos_empresa:
        # Tentar arquivos ZIP locais
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith('Empresas') and f.endswith('.zip'):
                arquivos_empresa.append(f)
    
    if not arquivos_empresa:
        # Buscar online
        arquivos_empresa = listar_arquivos_disponiveis(BASE_URL, tipo="empresa")
    
    if not arquivos_empresa:
        print("[DEBUG] ERRO: Nenhum arquivo Empresas encontrado")
        return len(cnpjs_existentes)
    
    arquivos_empresa.sort()
    print(f"[DEBUG] OK: {len(arquivos_empresa)} arquivo(s) Empresas encontrado(s)")
    
    total_inseridos = 0
    cnpjs_encontrados = set()
    
    for i, arquivo in enumerate(arquivos_empresa, 1):
        # Parar se já encontrou todos
        if len(cnpjs_faltantes - cnpjs_encontrados) == 0:
            print(f"[DEBUG] OK: Todos os CNPJ_BASICO foram encontrados!")
            break
        
        try:
            # Determinar caminho do CSV
            if arquivo.endswith('.csv'):
                caminho_csv = os.path.join(DOWNLOAD_DIR, arquivo)
                nome_exibicao = arquivo
            else:
                # É ZIP, baixar se necessário
                url_arquivo = BASE_URL + arquivo
                caminho_zip = baixar_arquivo(url_arquivo, arquivo, status)
                if not caminho_zip:
                    continue
                
                # ✅ VERIFICAR SE JÁ FOI EXTRAÍDO
                with ZipFile(caminho_zip, 'r') as zip_ref:
                    nomes = zip_ref.namelist()
                    if not nomes:
                        continue
                    nome_csv_interno = nomes[0]
                
                caminho_csv = os.path.join(DOWNLOAD_DIR, nome_csv_interno)
                
                # Se o CSV já existe, pular extração
                if os.path.exists(caminho_csv):
                    print(f"[DEBUG] OK: CSV já extraído: {nome_csv_interno}")
                else:
                    # Descompactar
                    print(f"[DEBUG] Descompactando {arquivo}...")
                    with ZipFile(caminho_zip, 'r') as zip_ref:
                        zip_ref.extractall(DOWNLOAD_DIR)
                    print(f"[DEBUG] OK: Extraído: {nome_csv_interno}")
                
                nome_exibicao = arquivo
            
            status['etapa'] = f'Buscando empresas em {nome_exibicao} ({i}/{len(arquivos_empresa)})...'
            status['arquivo_atual'] = i
            status['arquivos_total'] = len(arquivos_empresa)
            status['percentual'] = int((i / len(arquivos_empresa)) * 100)
            update_status(status)
            
            print(f"\n[DEBUG] Processando: {nome_exibicao}")
            print(f"[DEBUG] Ainda faltam: {len(cnpjs_faltantes - cnpjs_encontrados):,} empresas")
            
            # Ler CSV em chunks e filtrar
            chunk_count = 0
            for chunk in pd.read_csv(caminho_csv, sep=';', encoding='latin1', header=None,
                                     dtype=str, chunksize=CHUNK_SIZE, on_bad_lines='skip'):
                
                chunk_count += 1
                
                # Nomear colunas
                chunk.columns = [
                    'CNPJ_BASICO', 'RAZAO_SOCIAL', 'NATUREZA_JURIDICA',
                    'QUALIFICACAO_RESPONSAVEL', 'CAPITAL_SOCIAL',
                    'PORTE_EMPRESA', 'ENTE_FEDERATIVO'
                ]
                
                # ✅ FILTRAR: Apenas CNPJ_BASICO que estão na lista
                chunk = chunk[chunk['CNPJ_BASICO'].isin(cnpjs_faltantes)]
                
                if len(chunk) == 0:
                    continue
                
                print(f"[DEBUG] Chunk {chunk_count}: {len(chunk)} empresa(s) encontrada(s)")
                
                # Limpar dados
                chunk = chunk.fillna('')
                chunk['RAZAO_SOCIAL'] = chunk['RAZAO_SOCIAL'].str[:150]
                chunk['CAPITAL_SOCIAL'] = pd.to_numeric(chunk['CAPITAL_SOCIAL'].str.replace(',', '.'), errors='coerce')
                
                # Inserir
                for _, row in chunk.iterrows():
                    try:
                        cursor.execute("""
                            INSERT INTO empresas_receita (
                                CNPJ_BASICO, RAZAO_SOCIAL, NATUREZA_JURIDICA,
                                QUALIFICACAO_RESPONSAVEL, CAPITAL_SOCIAL,
                                PORTE_EMPRESA, ENTE_FEDERATIVO
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                RAZAO_SOCIAL = VALUES(RAZAO_SOCIAL),
                                PORTE_EMPRESA = VALUES(PORTE_EMPRESA)
                        """, (
                            row['CNPJ_BASICO'],
                            row['RAZAO_SOCIAL'],
                            row['NATUREZA_JURIDICA'] or None,
                            row['QUALIFICACAO_RESPONSAVEL'] or None,
                            row['CAPITAL_SOCIAL'] if pd.notna(row['CAPITAL_SOCIAL']) else None,
                            row['PORTE_EMPRESA'] or None,
                            row['ENTE_FEDERATIVO'] or None
                        ))
                        
                        cnpjs_encontrados.add(row['CNPJ_BASICO'])
                        total_inseridos += 1
                        
                        if total_inseridos % 1000 == 0:
                            conn.commit()
                            faltam = len(cnpjs_faltantes - cnpjs_encontrados)
                            print(f"[DEBUG] Progresso: {total_inseridos:,} inseridas | Faltam: {faltam:,}")
                            
                    except Exception as e:
                        if 'Duplicate entry' not in str(e):
                            print(f"[DEBUG] Erro ao inserir: {e}")
                
                conn.commit()
            
            print(f"[DEBUG] OK: {nome_exibicao} processado")
            
        except Exception as e:
            print(f"[DEBUG] ERRO: Erro ao processar {arquivo}: {e}")
    
    conn.commit()
    
    total_final = len(cnpjs_existentes) + total_inseridos
    print(f"\n[DEBUG] OK: Total de empresas: {total_final:,}")
    print(f"[DEBUG]   - Já existentes: {len(cnpjs_existentes):,}")
    print(f"[DEBUG]   - Recém importadas: {total_inseridos:,}")
    
    if len(cnpjs_faltantes - cnpjs_encontrados) > 0:
        print(f"[DEBUG] AVISO: Não encontradas: {len(cnpjs_faltantes - cnpjs_encontrados):,} empresas")
    
    return total_final

# =========================================
# ETAPA 1: IMPORTAR EMPRESAS (RAZÃO SOCIAL) - FUNÇÃO ANTIGA (NÃO USAR)
# =========================================
def importar_empresas_para_tabela(conn, status):
    """
    [DEPRECATED] Importa TODAS as empresas (50M registros)
    NÃO USE ESTA FUNÇÃO! Use importar_empresas_filtradas() ao invés
    """
    print("\n" + "="*60)
    print("[AVISO] Esta função não deve ser usada!")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Criar tabela empresas_receita se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas_receita (
            id INT AUTO_INCREMENT PRIMARY KEY,
            CNPJ_BASICO VARCHAR(8) NOT NULL,
            RAZAO_SOCIAL VARCHAR(150) NOT NULL,
            NATUREZA_JURIDICA VARCHAR(4) NULL,
            QUALIFICACAO_RESPONSAVEL VARCHAR(2) NULL,
            CAPITAL_SOCIAL DECIMAL(15,2) NULL,
            PORTE_EMPRESA VARCHAR(2) NULL COMMENT '01=ME, 03=EPP, 05=Demais',
            ENTE_FEDERATIVO VARCHAR(50) NULL,
            data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_cnpj_basico (CNPJ_BASICO),
            INDEX idx_razao_social (RAZAO_SOCIAL(50))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("[DEBUG] OK: Tabela empresas_receita verificada")
    
    # Verificar quantas empresas já estão importadas
    cursor.execute("SELECT COUNT(*) FROM empresas_receita")
    empresas_existentes = cursor.fetchone()[0]
    
    if empresas_existentes > 0:
        print(f"[DEBUG] AVISO: Já existem {empresas_existentes:,} empresas na tabela")
        print(f"[DEBUG] Pulando importação de Empresas (já foi feita)")
        return empresas_existentes
    
    # Listar arquivos Empresas
    status['etapa'] = 'Listando arquivos Empresas...'
    update_status(status)
    
    arquivos_empresa = listar_arquivos_disponiveis(BASE_URL, tipo="empresa")
    
    if not arquivos_empresa:
        print("[DEBUG] AVISO: Nenhum arquivo Empresas encontrado online")
        # Tentar usar arquivos locais
        arquivos_locais = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith('Empresas') and f.endswith('.csv')]
        if not arquivos_locais:
            print("[DEBUG] ERRO: Nenhum arquivo Empresas local encontrado")
            return 0
        print(f"[DEBUG] OK: Usando {len(arquivos_locais)} arquivo(s) local(is)")
        arquivos_empresa = arquivos_locais
    
    total_inseridos = 0
    
    for i, arquivo in enumerate(arquivos_empresa, 1):
        try:
            # Verificar se é arquivo local ou precisa baixar
            if arquivo.endswith('.csv'):
                # Arquivo local
                caminho_csv = os.path.join(DOWNLOAD_DIR, arquivo)
                nome_exibicao = arquivo
            else:
                # Arquivo online (.zip)
                url_arquivo = BASE_URL + arquivo
                nome_zip = arquivo
                nome_exibicao = nome_zip
                
                # Baixar se não existir
                caminho_zip = baixar_arquivo(url_arquivo, nome_zip, status)
                if not caminho_zip:
                    continue
                
                # Descompactar
                status['etapa'] = f'Descompactando {nome_zip}...'
                update_status(status)
                
                with ZipFile(caminho_zip, 'r') as zip_ref:
                    nomes = zip_ref.namelist()
                    if not nomes:
                        continue
                    
                    # Extrair primeiro arquivo
                    zip_ref.extractall(DOWNLOAD_DIR)
                    caminho_csv = os.path.join(DOWNLOAD_DIR, nomes[0])
            
            # Processar CSV
            status['etapa'] = f'Importando {nome_exibicao} ({i}/{len(arquivos_empresa)})...'
            status['arquivo_atual'] = i
            status['arquivos_total'] = len(arquivos_empresa)
            update_status(status)
            
            print(f"\n[DEBUG] Processando: {nome_exibicao}")
            
            # Ler CSV em chunks
            chunk_count = 0
            for chunk in pd.read_csv(caminho_csv, sep=';', encoding='latin1', header=None, 
                                     dtype=str, chunksize=CHUNK_SIZE, on_bad_lines='skip'):
                
                chunk_count += 1
                print(f"[DEBUG] Chunk {chunk_count}: {len(chunk)} registros")
                
                # Nomear colunas
                chunk.columns = [
                    'CNPJ_BASICO', 'RAZAO_SOCIAL', 'NATUREZA_JURIDICA',
                    'QUALIFICACAO_RESPONSAVEL', 'CAPITAL_SOCIAL',
                    'PORTE_EMPRESA', 'ENTE_FEDERATIVO'
                ]
                
                # Limpar dados
                chunk = chunk.fillna('')
                chunk['RAZAO_SOCIAL'] = chunk['RAZAO_SOCIAL'].str[:150]
                
                # Converter capital social
                chunk['CAPITAL_SOCIAL'] = pd.to_numeric(chunk['CAPITAL_SOCIAL'].str.replace(',', '.'), errors='coerce')
                
                # Inserir no MySQL
                for _, row in chunk.iterrows():
                    try:
                        cursor.execute("""
                            INSERT INTO empresas_receita (
                                CNPJ_BASICO, RAZAO_SOCIAL, NATUREZA_JURIDICA,
                                QUALIFICACAO_RESPONSAVEL, CAPITAL_SOCIAL,
                                PORTE_EMPRESA, ENTE_FEDERATIVO
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                RAZAO_SOCIAL = VALUES(RAZAO_SOCIAL),
                                PORTE_EMPRESA = VALUES(PORTE_EMPRESA)
                        """, (
                            row['CNPJ_BASICO'],
                            row['RAZAO_SOCIAL'],
                            row['NATUREZA_JURIDICA'] or None,
                            row['QUALIFICACAO_RESPONSAVEL'] or None,
                            row['CAPITAL_SOCIAL'] if pd.notna(row['CAPITAL_SOCIAL']) else None,
                            row['PORTE_EMPRESA'] or None,
                            row['ENTE_FEDERATIVO'] or None
                        ))
                        total_inseridos += 1
                        
                        if total_inseridos % 1000 == 0:
                            conn.commit()
                            print(f"[DEBUG] Progresso: {total_inseridos:,} empresas inseridas")
                            
                    except Exception as e:
                        if 'Duplicate entry' not in str(e):
                            print(f"[DEBUG] Erro ao inserir: {e}")
                
                conn.commit()
            
            print(f"[DEBUG] OK: {nome_exibicao} concluído")
            
        except Exception as e:
            print(f"[DEBUG] ERRO: Erro ao processar {arquivo}: {e}")
    
    print(f"\n[DEBUG] OK: Total de empresas importadas: {total_inseridos:,}")
    return total_inseridos

# =========================================
# ETAPA 2: IMPORTAR ESTABELECIMENTOS (FILTRADO)
# =========================================
def importar_estabelecimentos_filtrado(conn, cnaes, ufs, limpar, status):
    """
    Importa arquivos Estabelecimentos*.csv filtrados por UF, CNAE e ATIVAS
    """
    print("\n" + "="*60)
    print("ETAPA 2: IMPORTAR ESTABELECIMENTOS (FILTRADO)")
    print(f"Filtros: UF={ufs}, CNAE={cnaes}, ATIVAS=Sim")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Criar/limpar tabela empresas_filtradas
    if limpar:
        print("[DEBUG] AVISO: LIMPANDO tabela empresas_filtradas...")
        cursor.execute("DROP TABLE IF EXISTS empresas_filtradas")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas_filtradas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            CNPJ_BASICO VARCHAR(8),
            CNPJ_COMPLETO VARCHAR(14),
            RAZAO_SOCIAL VARCHAR(150) NULL,
            NOME_FANTASIA VARCHAR(55),
            MATRIZ_FILIAL VARCHAR(1),
            SITUACAO_CADASTRAL VARCHAR(2),
            DATA_SITUACAO_CADASTRAL DATE NULL,
            DATA_INICIO_ATIVIDADE DATE NULL,
            CNAE_FISCAL_PRINCIPAL VARCHAR(7),
            CNAE_FISCAL_SECUNDARIA TEXT,
            TIPO_LOGRADOURO VARCHAR(20),
            LOGRADOURO VARCHAR(255),
            NUMERO VARCHAR(10),
            COMPLEMENTO VARCHAR(255),
            BAIRRO VARCHAR(150),
            CEP VARCHAR(8),
            UF VARCHAR(2),
            MUNICIPIO VARCHAR(50),
            DDD1 VARCHAR(4),
            TELEFONE1 VARCHAR(8),
            DDD2 VARCHAR(4),
            TELEFONE2 VARCHAR(8),
            DDD_FAX VARCHAR(4),
            FAX VARCHAR(8),
            EMAIL VARCHAR(115),
            LATITUDE DECIMAL(10, 7) NULL,
            LONGITUDE DECIMAL(10, 7) NULL,
            PORTE_EMPRESA VARCHAR(2) NULL,
            NATUREZA_JURIDICA VARCHAR(4) NULL,
            INDEX idx_cnpj_basico (CNPJ_BASICO),
            INDEX idx_cnpj_completo (CNPJ_COMPLETO),
            INDEX idx_uf (UF),
            INDEX idx_cnae (CNAE_FISCAL_PRINCIPAL)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("[DEBUG] OK: Tabela empresas_filtradas verificada")
    
    # Listar arquivos Estabelecimentos
    status['etapa'] = 'Listando arquivos Estabelecimentos...'
    update_status(status)
    
    arquivos_estabelecimento = listar_arquivos_disponiveis(BASE_URL, tipo="estabelecimento")
    
    if not arquivos_estabelecimento:
        print("[DEBUG] AVISO: Tentando usar arquivos locais...")
        arquivos_locais = [f for f in os.listdir(DOWNLOAD_DIR) if 'Estabelecimento' in f and (f.endswith('.csv') or f.endswith('.zip'))]
        if not arquivos_locais:
            print("[DEBUG] ERRO: Nenhum arquivo Estabelecimentos encontrado")
            return 0
        arquivos_estabelecimento = arquivos_locais
    
    total_inseridos = 0
    
    for i, arquivo in enumerate(arquivos_estabelecimento, 1):
        try:
            # Determinar se é arquivo local ou online
            if arquivo.endswith('.csv'):
                caminho_csv = os.path.join(DOWNLOAD_DIR, arquivo)
                nome_exibicao = arquivo
            else:
                url_arquivo = BASE_URL + arquivo
                caminho_zip = baixar_arquivo(url_arquivo, arquivo, status)
                
                if not caminho_zip:
                    continue
                
                # ✅ VERIFICAR SE JÁ FOI EXTRAÍDO
                # Tentar descobrir o nome do CSV dentro do ZIP
                with ZipFile(caminho_zip, 'r') as zip_ref:
                    nomes = zip_ref.namelist()
                    if not nomes:
                        continue
                    nome_csv_interno = nomes[0]
                
                caminho_csv = os.path.join(DOWNLOAD_DIR, nome_csv_interno)
                
                # Se o CSV já existe, pular extração
                if os.path.exists(caminho_csv):
                    print(f"[DEBUG] OK: CSV já extraído: {nome_csv_interno}")
                    nome_exibicao = arquivo
                else:
                    # Descompactar
                    print(f"[DEBUG] Descompactando {arquivo}...")
                    status['etapa'] = f'Descompactando {arquivo}...'
                    update_status(status)
                    
                    with ZipFile(caminho_zip, 'r') as zip_ref:
                        zip_ref.extractall(DOWNLOAD_DIR)
                    
                    print(f"[DEBUG] OK: Extraído: {nome_csv_interno}")
                    nome_exibicao = arquivo
            
            # Processar CSV
            status['etapa'] = f'Processando {nome_exibicao} ({i}/{len(arquivos_estabelecimento)})...'
            status['arquivo_atual'] = i
            status['arquivos_total'] = len(arquivos_estabelecimento)
            status['registros_lidos'] = 0
            status['percentual'] = int((i / len(arquivos_estabelecimento)) * 100)
            update_status(status)
            
            print(f"\n[DEBUG] Processando: {nome_exibicao}")
            
            # ✅ DEBUG: Mostrar CNAEs que estamos buscando
            if i == 1:  # Apenas no primeiro arquivo
                print(f"[DEBUG] Buscando CNAEs (total: {len(cnaes)}):")
                for cnae in cnaes[:10]:  # Mostrar primeiros 10
                    print(f"  - '{cnae}' (tipo: {type(cnae).__name__}, len: {len(cnae)})")
            
            # Ler e filtrar CSV
            chunk_count = 0
            for chunk in pd.read_csv(caminho_csv, sep=';', encoding='latin1', header=None,
                                     dtype=str, chunksize=CHUNK_SIZE, on_bad_lines='skip'):
                
                chunk_count += 1
                
                # Nomear colunas
                chunk.columns = [
                    'CNPJ_BASICO', 'CNPJ_ORDEM', 'CNPJ_DV', 'MATRIZ_FILIAL',
                    'NOME_FANTASIA', 'SITUACAO_CADASTRAL', 'DATA_SITUACAO_CADASTRAL',
                    'MOTIVO_SITUACAO_CADASTRAL', 'NOME_CIDADE_EXTERIOR', 'PAIS',
                    'DATA_INICIO_ATIVIDADE', 'CNAE_FISCAL_PRINCIPAL', 'CNAE_FISCAL_SECUNDARIA',
                    'TIPO_LOGRADOURO', 'LOGRADOURO', 'NUMERO', 'COMPLEMENTO',
                    'BAIRRO', 'CEP', 'UF', 'MUNICIPIO', 'DDD1', 'TELEFONE1',
                    'DDD2', 'TELEFONE2', 'DDD_FAX', 'FAX', 'EMAIL',
                    'SITUACAO_ESPECIAL', 'DATA_SITUACAO_ESPECIAL'
                ]
                
                # ✅ DEBUG: Contar ANTES do filtro
                chunk_original = chunk.copy()  # Salvar para debug
                total_antes = len(chunk)
                
                # ✅ FILTRO CNAE: Buscar em PRINCIPAL **E** SECUNDÁRIA
                # Criar filtro OR para todos os CNAEs (igual versão antiga)
                cnae_filter = pd.Series([False] * len(chunk), index=chunk.index)
                for cnae in cnaes:
                    # CNAE Principal - começa com o código
                    cnae_principal = chunk['CNAE_FISCAL_PRINCIPAL'].astype(str).str.startswith(str(cnae), na=False)
                    
                    # CNAE Secundária - contém o código (separados por vírgula)
                    cnae_secundaria = chunk['CNAE_FISCAL_SECUNDARIA'].astype(str).str.contains(str(cnae), na=False, regex=False)
                    
                    # Aceitar se está no principal OU na secundária
                    cnae_filter = cnae_filter | cnae_principal | cnae_secundaria
                
                # ✅ FILTRO UF
                uf_filter = chunk['UF'].isin(ufs)
                
                # ✅ FILTRO ATIVAS
                # Converter para INT e comparar (igual versão antiga faz no SQL)
                chunk['SITUACAO_CADASTRAL_INT'] = pd.to_numeric(chunk['SITUACAO_CADASTRAL'], errors='coerce').fillna(0).astype(int)
                ativas_filter = (chunk['SITUACAO_CADASTRAL_INT'] == 2)
                
                # DEBUG: Ver distribuição
                if chunk_count == 1:
                    print(f"\n[DEBUG] Valores de SITUACAO_CADASTRAL (convertido para INT):")
                    situacoes = chunk['SITUACAO_CADASTRAL_INT'].value_counts().head(10)
                    for situacao, count in situacoes.items():
                        print(f"    {situacao}: {count:,} registros")
                    print(f"  Total ATIVAS (==2): {ativas_filter.sum():,}")
                
                # ✅ DEBUG: Contar matches
                uf_match = uf_filter.sum()
                cnae_match = cnae_filter.sum()
                ativas_match = ativas_filter.sum()
                
                # ✅ APLICAR FILTROS COMBINADOS
                chunk = chunk[cnae_filter & uf_filter & ativas_filter]
                
                # ✅ DEBUG: Mostrar estatísticas do filtro (apenas primeiros chunks)
                if chunk_count <= 2:
                    print(f"\n[DEBUG] ========== CHUNK {chunk_count} ==========")
                    print(f"  Total no chunk: {total_antes:,}")
                    print(f"  Match UF {ufs}: {uf_match:,}")
                    print(f"  Match CNAE (buscando {len(cnaes)} CNAEs): {cnae_match:,}")
                    print(f"  Match ATIVAS (SITUACAO=2): {ativas_match:,}")
                    print(f"  Após filtro combinado: {len(chunk):,}")
                    
                    # Mostrar amostra de CNAEs no chunk
                    print(f"\n  CNAES ENCONTRADOS no arquivo (amostra de 15):")
                    cnaes_unicos = chunk_original['CNAE_FISCAL_PRINCIPAL'].value_counts().head(15)
                    for idx, (cnae, count) in enumerate(cnaes_unicos.items(), 1):
                        tipo = type(cnae).__name__
                        print(f"    [{idx:2d}] '{cnae}' | tipo: {tipo} | len: {len(str(cnae))} | count: {count:,}")
                    
                    print(f"\n  CNAEs que VOCE ESTA BUSCANDO (primeiros 5):")
                    for idx, cnae in enumerate(cnaes[:5], 1):
                        tipo = type(cnae).__name__
                        print(f"    [{idx}] '{cnae}' | tipo: {tipo} | len: {len(str(cnae))}")
                    
                    # Comparação específica
                    if cnae_match == 0:
                        print(f"\n  AVISO COMPARAÇÃO:")
                        print(f"    Primeiro CNAE do arquivo: '{list(cnaes_unicos.keys())[0]}'")
                        print(f"    Primeiro CNAE buscado:    '{cnaes[0]}'")
                        print(f"    São iguais? {list(cnaes_unicos.keys())[0] == cnaes[0]}")
                    
                    if uf_match == 0:
                        print(f"\n  AVISO: NENHUMA UF correspondeu! Amostra:")
                        ufs_unicas = chunk_original['UF'].value_counts().head(10)
                        for uf, count in ufs_unicas.items():
                            print(f"    UF: '{uf}' | tipo: {type(uf).__name__} | count: {count:,}")
                    print(f"[DEBUG] ========================================\n")
                
                if len(chunk) == 0:
                    continue
                
                print(f"[DEBUG] OK: Filtrado: {len(chunk)} registros - Inserindo no banco...")
                
                # Processar dados
                chunk = chunk.fillna('')
                chunk['CNPJ_COMPLETO'] = chunk['CNPJ_BASICO'] + chunk['CNPJ_ORDEM'] + chunk['CNPJ_DV']
                chunk['LOGRADOURO'] = chunk['LOGRADOURO'].str[:255]
                chunk['COMPLEMENTO'] = chunk['COMPLEMENTO'].str[:255]
                chunk['BAIRRO'] = chunk['BAIRRO'].str[:150]
                
                # Tratar datas inválidas (converter '0', '', ou valores inválidos para None)
                for col in ['DATA_SITUACAO_CADASTRAL', 'DATA_INICIO_ATIVIDADE']:
                    chunk[col] = chunk[col].replace(['0', '00000000', ''], None)
                
                # Inserir (row by row para capturar erros)
                chunk_inseridos = 0
                for idx, row in chunk.iterrows():
                    try:
                        cursor.execute("""
                            INSERT INTO empresas_filtradas (
                                CNPJ_BASICO, CNPJ_COMPLETO, NOME_FANTASIA, MATRIZ_FILIAL,
                                SITUACAO_CADASTRAL, DATA_SITUACAO_CADASTRAL, DATA_INICIO_ATIVIDADE,
                                CNAE_FISCAL_PRINCIPAL, CNAE_FISCAL_SECUNDARIA,
                                TIPO_LOGRADOURO, LOGRADOURO, NUMERO, COMPLEMENTO,
                                BAIRRO, CEP, UF, MUNICIPIO,
                                DDD1, TELEFONE1, DDD2, TELEFONE2, DDD_FAX, FAX, EMAIL
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            row['CNPJ_BASICO'], row['CNPJ_COMPLETO'], row['NOME_FANTASIA'],
                            row['MATRIZ_FILIAL'], row['SITUACAO_CADASTRAL'],
                            row['DATA_SITUACAO_CADASTRAL'] or None,
                            row['DATA_INICIO_ATIVIDADE'] or None,
                            row['CNAE_FISCAL_PRINCIPAL'], row['CNAE_FISCAL_SECUNDARIA'],
                            row['TIPO_LOGRADOURO'], row['LOGRADOURO'], row['NUMERO'],
                            row['COMPLEMENTO'], row['BAIRRO'], row['CEP'], row['UF'],
                            row['MUNICIPIO'], row['DDD1'], row['TELEFONE1'], row['DDD2'],
                            row['TELEFONE2'], row['DDD_FAX'], row['FAX'], row['EMAIL']
                        ))
                        chunk_inseridos += 1
                        total_inseridos += 1
                            
                    except Exception as e:
                        print(f"[DEBUG] ERRO: Erro ao inserir registro {idx}: {e}")
                
                # Commit após cada chunk
                conn.commit()
                print(f"[DEBUG] OK: Chunk inserido: {chunk_inseridos}/{len(chunk)} registros | Total geral: {total_inseridos:,}")
                
                # Atualizar status
                status['registros_inseridos'] = total_inseridos
                status['registros_lidos'] = status.get('registros_lidos', 0) + len(chunk_original)
                update_status(status)
            
            print(f"[DEBUG] OK: {nome_exibicao} concluído")
            
        except Exception as e:
            print(f"[DEBUG] ERRO: Erro ao processar {arquivo}: {e}")
    
    print(f"\n[DEBUG] OK: Total de estabelecimentos importados: {total_inseridos:,}")
    return total_inseridos

# =========================================
# ETAPA 3: ATUALIZAR COM RAZÃO SOCIAL
# =========================================
def atualizar_razao_social(conn, status):
    """Atualiza empresas_filtradas com RAZAO_SOCIAL via JOIN"""
    print("\n" + "="*60)
    print("ETAPA 3: ATUALIZAR RAZÃO SOCIAL")
    print("="*60)
    
    status['etapa'] = 'Atualizando Razão Social...'
    update_status(status)
    
    cursor = conn.cursor()
    
    # DEBUG: Ver quantas empresas têm RAZAO_SOCIAL vazio
    cursor.execute("SELECT COUNT(*) FROM empresas_receita WHERE RAZAO_SOCIAL = '' OR RAZAO_SOCIAL IS NULL")
    vazios = cursor.fetchone()[0]
    if vazios > 0:
        print(f"[DEBUG] AVISO: ATENÇÃO: {vazios:,} empresas com RAZAO_SOCIAL vazia!")
        
        # Mostrar exemplos
        cursor.execute("SELECT CNPJ_BASICO, RAZAO_SOCIAL FROM empresas_receita WHERE RAZAO_SOCIAL = '' OR RAZAO_SOCIAL IS NULL LIMIT 5")
        exemplos = cursor.fetchall()
        print(f"[DEBUG] Exemplos de CNPJ sem RAZAO_SOCIAL:")
        for cnpj, razao in exemplos:
            print(f"  - {cnpj}: '{razao}'")
    
    cursor.execute("""
        UPDATE empresas_filtradas ef
        INNER JOIN empresas_receita er ON ef.CNPJ_BASICO = er.CNPJ_BASICO
        SET 
            ef.RAZAO_SOCIAL = er.RAZAO_SOCIAL,
            ef.PORTE_EMPRESA = er.PORTE_EMPRESA,
            ef.NATUREZA_JURIDICA = er.NATUREZA_JURIDICA
        WHERE er.RAZAO_SOCIAL IS NOT NULL AND er.RAZAO_SOCIAL != ''
    """)
    
    total_atualizados = cursor.rowcount
    conn.commit()
    
    # Verificar quantos estabelecimentos ficaram SEM Razão Social
    cursor.execute("SELECT COUNT(*) FROM empresas_filtradas WHERE RAZAO_SOCIAL IS NULL OR RAZAO_SOCIAL = ''")
    sem_razao = cursor.fetchone()[0]
    
    cursor.close()
    
    print(f"[DEBUG] OK: {total_atualizados:,} registros atualizados com Razão Social")
    if sem_razao > 0:
        print(f"[DEBUG] AVISO: {sem_razao:,} estabelecimentos ficaram SEM Razão Social")
    
    return total_atualizados

# =========================================
# FUNÇÃO PRINCIPAL
# =========================================
def process_and_insert(cnaes, ufs, table_name="empresas_filtradas", limpar=False):
    """
    Função principal - Importação integrada
    
    Args:
        cnaes: Lista de códigos CNAE
        ufs: Lista de UFs
        table_name: Nome da tabela (empresas_filtradas)
        limpar: Se True, apaga tabela antes
    """
    # Garantir listas
    if isinstance(cnaes, str):
        cnaes = [cnaes]
    if isinstance(ufs, str):
        ufs = [ufs]
    
    status = {
        'status': 'processando',
        'etapa': 'Iniciando importação integrada...',
        'arquivos_total': 0,
        'arquivo_atual': 0,
        'registros_inseridos': 0,
        'percentual': 0,
        'inicio': datetime.now().isoformat()
    }
    update_status(status)
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        
        # ✅ ETAPA 1: Importar Estabelecimentos (FILTRADO por UF + CNAE + ATIVAS)
        print("\n" + "="*60)
        print("ETAPA 1: IMPORTAR ESTABELECIMENTOS (FILTRADO)")
        print(f"Filtros: UF={ufs}, CNAE={cnaes}")
        print("="*60)
        total_estabelecimentos = importar_estabelecimentos_filtrado(conn, cnaes, ufs, limpar, status)
        
        if total_estabelecimentos == 0:
            print("[AVISO] Nenhum estabelecimento importado. Encerrando.")
            status['status'] = 'concluido'
            status['etapa'] = 'Nenhum estabelecimento encontrado com os filtros aplicados'
            update_status(status)
            return
        
        # ✅ ETAPA 2: Extrair CNPJ_BASICO únicos dos estabelecimentos filtrados
        print("\n" + "="*60)
        print("ETAPA 2: EXTRAIR CNPJ_BASICO ÚNICOS")
        print("="*60)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT CNPJ_BASICO FROM empresas_filtradas")
        cnpjs_filtrados = [row[0] for row in cursor.fetchall()]
        cursor.close()
        print(f"[DEBUG] OK: {len(cnpjs_filtrados):,} CNPJ_BASICO únicos encontrados")
        
        # ✅ ETAPA 3: Importar APENAS Empresas com CNPJ_BASICO filtrado
        print("\n" + "="*60)
        print("ETAPA 3: IMPORTAR EMPRESAS (APENAS FILTRADAS)")
        print("="*60)
        total_empresas = importar_empresas_filtradas(conn, cnpjs_filtrados, status)
        
        # ✅ ETAPA 4: Atualizar RAZAO_SOCIAL
        print("\n" + "="*60)
        print("ETAPA 4: ATUALIZAR RAZÃO SOCIAL")
        print("="*60)
        total_atualizados = atualizar_razao_social(conn, status)
        
        conn.close()
        
        status['status'] = 'concluido'
        status['etapa'] = f'OK: Importação concluída! {total_estabelecimentos} estabelecimentos importados'
        status['fim'] = datetime.now().isoformat()
        update_status(status)
        
        print("\n" + "="*60)
        print("RESUMO FINAL")
        print("="*60)
        print(f"Estabelecimentos (filtrados): {total_estabelecimentos:,}")
        print(f"CNPJ_BASICO únicos: {len(cnpjs_filtrados):,}")
        print(f"Empresas (filtradas): {total_empresas:,}")
        print(f"Registros com Razão Social: {total_atualizados:,}")
        print("="*60)
        
    except Exception as e:
        print(f"[DEBUG] ERRO: {e}")
        status['status'] = 'erro'
        status['erro'] = str(e)
        update_status(status)
        raise

# =========================================
# TESTE
# =========================================
if __name__ == "__main__":
    # BAIXAR TODAS AS EMPRESAS DO BRASIL
    # Lista de todos os estados brasileiros
    todos_ufs = [
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", 
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
    ]
    
    # CNAEs mais comuns (você pode adicionar mais se quiser filtrar por setor)
    # Para TODAS as empresas, use uma lista com CNAEs principais
    principais_cnaes = [
        "4781400",  # Comércio varejista de artigos do vestuário e acessórios
        "4711301",  # Comércio varejista de mercadorias em geral
        "6201501",  # Desenvolvimento de programas de computador
        "4120400",  # Construção de edifícios
        "8630501",  # Atividade médica ambulatorial
        "9602501",  # Cabeleireiros
        "5611201",  # Restaurantes e similares
        "4744099",  # Comércio varejista de materiais de construção
        "7020400",  # Atividades de consultoria em gestão empresarial
        "4930202"   # Transporte rodoviário de carga
    ]
    
    print("="*60)
    print("IMPORTANDO TODAS AS EMPRESAS DO BRASIL")
    print(f"Estados: {len(todos_ufs)} UFs")
    print(f"CNAEs: {len(principais_cnaes)} setores principais")
    print("="*60)
    
    process_and_insert(
        cnaes=principais_cnaes,
        ufs=todos_ufs,
        limpar=True
    )
