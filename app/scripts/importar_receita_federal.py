import os
import requests
import pandas as pd
import mysql.connector
from io import BytesIO
from zipfile import ZipFile
from bs4 import BeautifulSoup
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# =========================================
# CONFIGURAÇÕES INICIAIS
# =========================================
BASE_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/"
CHUNK_SIZE = 200000  # Tamanho do chunk (ajuste conforme memória disponível)

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "aritana",
    "database": "supply_chain_system"
}

# Diretório para download dos arquivos
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads_receita')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

STATUS_FILE = os.path.join(os.path.dirname(__file__), 'importacao_status.json')

# Inicializar geocoder (OpenStreetMap Nominatim - gratuito)
geolocator = Nominatim(user_agent="supply_chain_system_v1", timeout=10)

# Cache de geocodificação (endereço -> lat/lng)
geocode_cache = {}

# =========================================
# FUNÇÃO - ATUALIZAR STATUS
# =========================================
def update_status(status_data):
    """Atualiza arquivo JSON com status atual da importação"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

# =========================================
# FUNÇÃO 1 - BUSCAR ÚLTIMO DIRETÓRIO
# =========================================
def get_latest_directory(base_url):
    """Busca o diretório mais recente no site da Receita Federal"""
    try:
        r = requests.get(base_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Buscar diretórios (links que terminam com /)
        dirs = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if href and href.endswith("/") and href != "../":
                dirs.append(href.strip("/"))
        
        if not dirs:
            print("[DEBUG] Nenhum diretório encontrado, usando URL base")
            return base_url
        
        latest = sorted(dirs)[-1]
        print(f"[DEBUG] Diretórios encontrados: {dirs}")
        print(f"[DEBUG] Diretório mais recente: {latest}")
        return base_url + latest + "/"
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar diretório: {e}")
        return base_url

# =========================================
# FUNÇÃO 2 - CRIAR TABELA AUTOMÁTICA NO MYSQL
# =========================================
def create_mysql_table_if_not_exists(conn, table_name, limpar=False):
    """Cria tabela empresas_filtradas se não existir
    
    Args:
        conn: Conexão MySQL
        table_name: Nome da tabela
        limpar: Se True, apaga a tabela e recria do zero. Se False, mantém dados existentes.
    """
    cursor = conn.cursor()
    
    if limpar:
        # Limpar tabela se já existir
        print(f"[DEBUG] ⚠️ LIMPANDO tabela {table_name}...")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            CNPJ_BASICO VARCHAR(8),
            CNPJ_ORDEM VARCHAR(4),
            CNPJ_DV VARCHAR(2),
            CNPJ_COMPLETO VARCHAR(14),
            MATRIZ_FILIAL VARCHAR(1),
            NOME_FANTASIA VARCHAR(255),
            SITUACAO_CADASTRAL INT,
            DATA_SITUACAO_CADASTRAL DATE NULL,
            MOTIVO_SITUACAO_CADASTRAL INT NULL,
            NOME_CIDADE_EXTERIOR VARCHAR(100) NULL,
            PAIS VARCHAR(100) NULL,
            DATA_INICIO_ATIVIDADE DATE NULL,
            CNAE_FISCAL_PRINCIPAL VARCHAR(10),
            CNAE_FISCAL_SECUNDARIA TEXT,
            TIPO_LOGRADOURO VARCHAR(50),
            LOGRADOURO VARCHAR(255),
            NUMERO VARCHAR(50),
            COMPLEMENTO VARCHAR(255),
            BAIRRO VARCHAR(150),
            CEP VARCHAR(10),
            UF VARCHAR(2),
            MUNICIPIO VARCHAR(100),
            DDD1 VARCHAR(4),
            TELEFONE1 VARCHAR(15),
            DDD2 VARCHAR(4),
            TELEFONE2 VARCHAR(15),
            DDD_FAX VARCHAR(4),
            FAX VARCHAR(15),
            EMAIL VARCHAR(255),
            SITUACAO_ESPECIAL VARCHAR(100) NULL,
            DATA_SITUACAO_ESPECIAL DATE NULL,
            LATITUDE DECIMAL(10, 8) NULL,
            LONGITUDE DECIMAL(11, 8) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    conn.commit()
    cursor.close()

# =========================================
# FUNÇÃO 2.5 - GEOCODIFICAÇÃO
# =========================================
def geocode_address(logradouro, numero, bairro, municipio, uf, cep):
    """
    Geocodifica um endereço e retorna latitude e longitude
    
    Args:
        logradouro, numero, bairro, municipio, uf, cep: Componentes do endereço
        
    Returns:
        tuple: (latitude, longitude) ou (None, None) se não encontrado
    """
    try:
        # Montar endereço completo
        parts = []
        if logradouro and str(logradouro) != 'nan':
            parts.append(str(logradouro))
        if numero and str(numero) != 'nan':
            parts.append(str(numero))
        if bairro and str(bairro) != 'nan':
            parts.append(str(bairro))
        if municipio and str(municipio) != 'nan':
            parts.append(str(municipio))
        if uf and str(uf) != 'nan':
            parts.append(str(uf))
        if cep and str(cep) != 'nan':
            parts.append(f"CEP {str(cep)}")
        
        full_address = ", ".join(parts) + ", Brasil"
        
        # Verificar cache
        if full_address in geocode_cache:
            return geocode_cache[full_address]
        
        # Geocodificar
        time.sleep(1)  # Respeitar rate limit do Nominatim (1 req/sec)
        location = geolocator.geocode(full_address)
        
        if location:
            result = (location.latitude, location.longitude)
            geocode_cache[full_address] = result
            return result
        else:
            geocode_cache[full_address] = (None, None)
            return (None, None)
            
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"[DEBUG] ⚠️ Erro ao geocodificar: {e}")
        return (None, None)
    except Exception as e:
        print(f"[DEBUG] ⚠️ Erro inesperado na geocodificação: {e}")
        return (None, None)

# =========================================
# FUNÇÃO 3 - INSERÇÃO EM LOTES NO MYSQL
# =========================================
def insert_chunk_into_mysql(conn, df, table_name):
    """Insere chunk de dados filtrados no MySQL"""
    print(f"[DEBUG] Iniciando inserção de {len(df)} registros...")
    cursor = conn.cursor()
    
    try:
        # Fazer cópia explícita para evitar SettingWithCopyWarning
        df = df.copy()
        
        # Adicionar coluna CNPJ_COMPLETO
        df['CNPJ_COMPLETO'] = df['CNPJ_BASICO'].astype(str) + df['CNPJ_ORDEM'].astype(str) + df['CNPJ_DV'].astype(str)
        
        # Limitar tamanho de campos VARCHAR para evitar erros
        df['COMPLEMENTO'] = df['COMPLEMENTO'].astype(str).str[:255]
        df['BAIRRO'] = df['BAIRRO'].astype(str).str[:150]
        df['LOGRADOURO'] = df['LOGRADOURO'].astype(str).str[:255]
        
        # Tratar datas inválidas (converter '0', '', ou valores inválidos para None)
        date_columns = ['DATA_SITUACAO_CADASTRAL', 'DATA_INICIO_ATIVIDADE', 'DATA_SITUACAO_ESPECIAL']
        for col in date_columns:
            if col in df.columns:
                # Substituir valores inválidos por None
                df[col] = df[col].replace(['0', '', 'nan', 'None'], None)
                # Converter valores que não são datas válidas para None
                df[col] = df[col].apply(lambda x: None if pd.isna(x) or str(x).strip() == '' or str(x) == '0' else x)
        
        # GEOCODIFICAÇÃO DESABILITADA (muito lenta - ~2h para importação completa)
        # Para habilitar, remova os comentários abaixo e comente as linhas de LATITUDE/LONGITUDE NULL
        
        # Adicionar colunas vazias (sem geocodificação)
        print(f"[DEBUG] ⚠️ Geocodificação DESABILITADA - adicionando lat/lng como NULL")
        df['LATITUDE'] = None
        df['LONGITUDE'] = None
        
        # ============================================================================
        # CÓDIGO DE GEOCODIFICAÇÃO (COMENTADO - descomente para habilitar)
        # ============================================================================
        # print(f"[DEBUG] Preparando geocodificação de {len(df)} registros...")
        # df['_endereco_key'] = (
        #     df['LOGRADOURO'].astype(str) + '|' +
        #     df['NUMERO'].astype(str) + '|' +
        #     df['MUNICIPIO'].astype(str) + '|' +
        #     df['UF'].astype(str) + '|' +
        #     df['CEP'].astype(str)
        # )
        # unique_addresses = df['_endereco_key'].unique()
        # print(f"[DEBUG] Total de endereços únicos: {len(unique_addresses)}")
        # geocoded_results = {}
        # for i, addr_key in enumerate(unique_addresses, 1):
        #     if i % 5 == 0:
        #         print(f"[DEBUG] Geocodificando {i}/{len(unique_addresses)} endereços únicos...")
        #     parts = addr_key.split('|')
        #     lat, lng = geocode_address(parts[0], parts[1], '', parts[2], parts[3], parts[4])
        #     geocoded_results[addr_key] = (lat, lng)
        # df['LATITUDE'] = df['_endereco_key'].map(lambda x: geocoded_results[x][0])
        # df['LONGITUDE'] = df['_endereco_key'].map(lambda x: geocoded_results[x][1])
        # df = df.drop(columns=['_endereco_key'])
        # geocoded_count = df['LATITUDE'].notna().sum()
        # print(f"[DEBUG] ✓ {geocoded_count}/{len(df)} registros geocodificados com sucesso")
        # ============================================================================
        
        cols = list(df.columns)
        placeholders = ", ".join(["%s"] * len(cols))
        colnames = ", ".join(cols)
        insert_stmt = f"INSERT INTO {table_name} ({colnames}) VALUES ({placeholders})"
        
        print(f"[DEBUG] Preparando {len(df)} registros para inserção...")
        data = [tuple(row) for row in df.to_numpy()]
        
        print(f"[DEBUG] Executando INSERT...")
        cursor.executemany(insert_stmt, data)
        
        print(f"[DEBUG] Fazendo COMMIT...")
        conn.commit()
        
        print(f"[DEBUG] ✓ COMMIT realizado com sucesso!")
        
        # Verificar se foi inserido
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = cursor.fetchone()[0]
        print(f"[DEBUG] Total de registros na tabela agora: {total}")
        
        cursor.close()
        return len(data)
    except Exception as e:
        print(f"[DEBUG] ✗ ERRO na inserção: {e}")
        conn.rollback()
        cursor.close()
        raise

# =========================================
# FUNÇÃO 4 - PROCESSAMENTO PRINCIPAL
# =========================================
def process_and_insert(cnaes, ufs, table_name="empresas_filtradas", limpar=False):
    """
    Processa importação da Receita Federal
    
    Args:
        cnaes: Lista de códigos CNAE para filtrar (ex: ["4781400", "1510600"])
        ufs: Lista de estados para filtrar (ex: ["MS", "MT", "GO"])
        table_name: Nome da tabela (padrão: empresas_filtradas)
        limpar: Se True, apaga a tabela antes. Se False, adiciona aos dados existentes. (padrão: False)
    """
    # Garantir que cnaes e ufs são listas
    if isinstance(cnaes, str):
        cnaes = [cnaes]
    if isinstance(ufs, str):
        ufs = [ufs]
    
    status = {
        'status': 'iniciando',
        'etapa': 'Buscando diretório mais recente...',
        'arquivos_total': 0,
        'arquivo_atual': 0,
        'arquivo_nome': '',
        'registros_lidos': 0,
        'registros_inseridos': 0,
        'percentual': 0,
        'erro': None,
        'inicio': datetime.now().isoformat(),
        'fim': None
    }
    update_status(status)
    
    try:
        # 1. Usar diretório fixo (mais confiável)
        latest_url = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/2025-09/"
        print(f"[DEBUG] Usando diretório: {latest_url}")
        status['etapa'] = f'Diretório: {latest_url}'
        update_status(status)
        
        # 2. Listar arquivos ZIP de estabelecimentos
        status['etapa'] = 'Listando arquivos disponíveis...'
        update_status(status)
        
        print(f"[DEBUG] Fazendo requisição para: {latest_url}")
        r = requests.get(latest_url, timeout=30)
        print(f"[DEBUG] Status code: {r.status_code}")
        print(f"[DEBUG] Tamanho da resposta: {len(r.text)} bytes")
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Buscar por diferentes padrões de nome
        all_links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
        links = []
        
        print(f"[DEBUG] Total de links na página: {len(all_links)}")
        print(f"[DEBUG] Primeiros 15 links: {all_links[:15]}")
        
        for href in all_links:
            if not href:
                continue
            href_lower = href.lower()
            # Aceitar: Estabelecimentos0.zip, Estabelecimentos1.zip, etc.
            if "estabelecimento" in href_lower and href.endswith(".zip"):
                full_url = latest_url + href if not href.startswith("http") else href
                links.append(full_url)
                print(f"[DEBUG] ✓ Arquivo encontrado: {href}")
        
        # Debug: mostrar todos os arquivos ZIP encontrados
        print(f"[DEBUG] Total de links encontrados: {len(all_links)}")
        print(f"[DEBUG] Arquivos ZIP de estabelecimentos: {len(links)}")
        if len(links) > 0:
            print(f"[DEBUG] Primeiro arquivo: {links[0]}")
        
        if not links:
            # Listar todos os ZIPs para debug
            all_zips = []
            for a in soup.find_all("a"):
                href = a.get("href")
                if href and href.endswith(".zip"):
                    all_zips.append(href)
            
            status['status'] = 'erro'
            status['erro'] = f'Nenhum arquivo de estabelecimentos encontrado. Total de ZIPs no diretório: {len(all_zips)}'
            if len(all_zips) > 0:
                status['erro'] += f'. Exemplos: {", ".join(all_zips[:5])}'
            else:
                status['erro'] += f'. Total de links na página: {len(all_links)}'
            update_status(status)
            print(f"[DEBUG] Todos os ZIPs encontrados: {all_zips[:10]}")
            print(f"[DEBUG] HTML snippet: {r.text[:500]}")
            return
        
        status['arquivos_total'] = len(links)
        status['etapa'] = f'{len(links)} arquivos encontrados'
        update_status(status)
        
        # 3. Conectar ao MySQL e criar tabela
        status['etapa'] = 'Criando tabela no banco de dados...'
        update_status(status)
        
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        create_mysql_table_if_not_exists(conn, table_name, limpar=limpar)
        
        # Verificar se tabela foi criada
        cursor = conn.cursor()
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if cursor.fetchone():
            print(f"[DEBUG] ✓ Tabela '{table_name}' criada com sucesso")
        else:
            print(f"[DEBUG] ✗ ERRO: Tabela '{table_name}' não foi criada!")
        cursor.close()
        
        status['etapa'] = 'Tabela criada com sucesso'
        update_status(status)
        
        # 4. Processar cada arquivo ZIP
        for idx, link in enumerate(links, 1):
            arquivo_nome = link.split('/')[-1]
            arquivo_path = os.path.join(DOWNLOAD_DIR, arquivo_nome)
            
            status['arquivo_atual'] = idx
            status['arquivo_nome'] = arquivo_nome
            status['etapa'] = f'Baixando arquivo {idx}/{len(links)}: {arquivo_nome}'
            status['percentual'] = int((idx - 1) / len(links) * 100)
            update_status(status)
            
            # Verificar se já foi baixado
            if os.path.exists(arquivo_path):
                print(f"[DEBUG] ✓ Arquivo já existe: {arquivo_nome}")
            else:
                # Download do arquivo
                print(f"[DEBUG] Baixando {arquivo_nome}...")
                response = requests.get(link, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(arquivo_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                if percent % 10 == 0:
                                    print(f"[DEBUG] Download: {percent}%")
                
                print(f"[DEBUG] ✓ Download concluído: {arquivo_nome}")
            
            status['etapa'] = f'Processando {arquivo_nome}...'
            update_status(status)
            
            # Processar ZIP do disco
            print(f"[DEBUG] Abrindo ZIP: {arquivo_nome}")
            try:
                with ZipFile(arquivo_path, 'r') as zf:
                    print(f"[DEBUG] ZIP aberto com sucesso. Listando arquivos...")
                    file_list = zf.namelist()
                    print(f"[DEBUG] Arquivos no ZIP: {file_list}")
                    
                    for name in file_list:
                        print(f"[DEBUG] Verificando arquivo: {name}")
                        # Processar qualquer arquivo (não só .csv, pois os arquivos têm extensão .ESTABELE)
                        if True:  # Processar todos os arquivos do ZIP
                            print(f"[DEBUG] ✓ Arquivo CSV encontrado: {name}")
                            status['etapa'] = f'Lendo {name} em blocos...'
                            update_status(status)
                            
                            # Processar em chunks
                            chunk_num = 0
                            print(f"[DEBUG] Iniciando leitura em chunks de {CHUNK_SIZE} linhas...")
                            
                            for chunk in pd.read_csv(
                                zf.open(name),
                                sep=";",
                                encoding="latin1",
                                low_memory=False,
                                chunksize=CHUNK_SIZE,
                                dtype=str,
                                header=None  # CSVs da Receita não têm cabeçalho
                            ):
                                chunk_num += 1
                                print(f"[DEBUG] Lendo chunk {chunk_num}... ({len(chunk)} linhas)")
                                registros_lidos_chunk = len(chunk)
                                status['registros_lidos'] += registros_lidos_chunk
                            
                                # Debug: mostrar primeiras linhas do primeiro chunk
                                if chunk_num == 1:
                                    print(f"[DEBUG] Colunas do CSV: {chunk.shape[1]}")
                                    print(f"[DEBUG] Primeira linha (primeiras 10 colunas): {chunk.iloc[0].tolist()[:10]}")
                                    print(f"[DEBUG] Coluna 11 (CNAE Principal): {chunk.iloc[0, 11]}")
                                    print(f"[DEBUG] Coluna 12 (CNAE Secundária): {chunk.iloc[0, 12]}")
                                    print(f"[DEBUG] Coluna 19 (UF): {chunk.iloc[0, 19]}")
                                    print(f"[DEBUG] Filtrando por UFs={ufs} e CNAEs={cnaes}")
                                
                                # COM FILTRO - Múltiplas UFs e múltiplos CNAEs (Principal + Secundária)
                                # Criar filtro OR para todos os CNAEs (buscar em Principal E Secundária)
                                cnae_filter = False
                                for cnae in cnaes:
                                    # CNAE Principal (coluna 11) - começa com o código
                                    cnae_principal = chunk.iloc[:, 11].astype(str).str.startswith(str(cnae), na=False)
                                    
                                    # CNAE Secundária (coluna 12) - contém o código (separados por vírgula)
                                    cnae_secundaria = chunk.iloc[:, 12].astype(str).str.contains(str(cnae), na=False, regex=False)
                                    
                                    # Aceitar se está no principal OU na secundária
                                    cnae_filter = cnae_filter | cnae_principal | cnae_secundaria
                                
                                # Criar filtro OR para todas as UFs
                                uf_filter = chunk.iloc[:, 19].isin(ufs)
                                
                                filtrado = chunk[
                                    cnae_filter &
                                    uf_filter
                                ]
                                
                                # Debug: mostrar quantos passaram no filtro
                                if chunk_num == 1:
                                    print(f"[DEBUG] Registros no chunk: {len(chunk)}")
                                    print(f"[DEBUG] Registros filtrados (UFs={ufs} + CNAEs Principal+Secundária={cnaes}): {len(filtrado)}")
                                
                                # Pular se não há registros filtrados
                                if len(filtrado) == 0:
                                    if chunk_num <= 3:
                                        print(f"[DEBUG] Bloco {chunk_num}: 0 registros passaram no filtro")
                                    status['etapa'] = f'Bloco {chunk_num}: Nenhum registro correspondente'
                                    update_status(status)
                                    continue
                                
                                # Renomear colunas de acordo com o número real de colunas
                                num_cols = filtrado.shape[1]
                                if num_cols == 30:
                                    # Padrão da Receita Federal (30 colunas)
                                    filtrado.columns = [
                                        'CNPJ_BASICO', 'CNPJ_ORDEM', 'CNPJ_DV', 'MATRIZ_FILIAL',
                                        'NOME_FANTASIA', 'SITUACAO_CADASTRAL', 'DATA_SITUACAO_CADASTRAL',
                                        'MOTIVO_SITUACAO_CADASTRAL', 'NOME_CIDADE_EXTERIOR', 'PAIS',
                                        'DATA_INICIO_ATIVIDADE', 'CNAE_FISCAL_PRINCIPAL', 'CNAE_FISCAL_SECUNDARIA',
                                        'TIPO_LOGRADOURO', 'LOGRADOURO', 'NUMERO', 'COMPLEMENTO',
                                        'BAIRRO', 'CEP', 'UF', 'MUNICIPIO', 'DDD1', 'TELEFONE1',
                                        'DDD2', 'TELEFONE2', 'DDD_FAX', 'FAX',
                                        'EMAIL', 'SITUACAO_ESPECIAL', 'DATA_SITUACAO_ESPECIAL'
                                    ]
                                else:
                                    print(f"[DEBUG] ✗ ERRO: Número inesperado de colunas: {num_cols}")
                                    # Usar nomes genéricos
                                    filtrado.columns = [f'COL_{i}' for i in range(num_cols)]
                                
                                # INSERIR NO BANCO (dentro do loop!)
                                print(f"[DEBUG] Inserindo {len(filtrado)} registros do bloco {chunk_num}...")
                                try:
                                    inseridos = insert_chunk_into_mysql(conn, filtrado, table_name)
                                    status['registros_inseridos'] += inseridos
                                    status['etapa'] = f'Bloco {chunk_num}: {inseridos} registros inseridos'
                                    print(f"[DEBUG] ✓ {inseridos} registros inseridos com sucesso!")
                                except Exception as e:
                                    print(f"[DEBUG] ✗ Erro ao inserir: {e}")
                                    status['etapa'] = f'Bloco {chunk_num}: Erro ao inserir - {str(e)}'
                                
                                update_status(status)
            except Exception as e:
                print(f"[DEBUG] ✗ Erro ao processar ZIP {arquivo_nome}: {e}")
                status['status'] = 'erro'
                status['erro'] = f'Erro ao processar {arquivo_nome}: {str(e)}'
                update_status(status)
                raise
        
        # Finalizar
        conn.close()
        status['status'] = 'concluido'
        status['etapa'] = 'Importação concluída com sucesso!'
        status['percentual'] = 100
        status['fim'] = datetime.now().isoformat()
        update_status(status)
        
    except Exception as e:
        status['status'] = 'erro'
        status['erro'] = str(e)
        status['etapa'] = f'Erro: {str(e)}'
        update_status(status)
        raise

# =========================================
# EXECUÇÃO DIRETA (para testes)
# =========================================
if __name__ == "__main__":
    # Exemplo de uso
    process_and_insert(
        cnae="4781400",
        uf="MS",
        table_name="empresas_filtradas"
    )
