"""
Script para Geocodificar Clientes Importados das NF-e
Adiciona latitude e longitude aos clientes da tabela customers
"""

import os
import sys
import mysql.connector
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Carregar variáveis de ambiente
load_dotenv()

# =========================================
# CONFIGURAÇÕES DO BANCO
# =========================================
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')

# =========================================
# CONFIGURAÇÃO DA API DE GEOCODIFICAÇÃO
# =========================================
# HERE MAPS API - 250.000 geocodificações/mês GRÁTIS
HERE_MAPS_API_KEY = "elCXcTWBwxAD1S9YY1ZgiBXDO3v7cfHHqg_VyJCgOak"

# Limite de segurança por execução
LIMITE_MAXIMO_GEOCODIFICACOES = 1000  # Ajuste conforme necessário

# =========================================
# VALIDAÇÃO GEOGRÁFICA - BOUNDING BOX
# =========================================
ESTADOS_BBOX = {
    'AC': {'min_lat': -11.2, 'max_lat': -7.0, 'min_lng': -74.0, 'max_lng': -66.5},
    'AL': {'min_lat': -10.5, 'max_lat': -8.8, 'min_lng': -38.3, 'max_lng': -35.1},
    'AP': {'min_lat': -4.5, 'max_lat': 2.5, 'min_lng': -54.9, 'max_lng': -49.8},
    'AM': {'min_lat': -9.8, 'max_lat': 2.3, 'min_lng': -73.8, 'max_lng': -56.1},
    'BA': {'min_lat': -18.5, 'max_lat': -8.5, 'min_lng': -46.6, 'max_lng': -37.3},
    'CE': {'min_lat': -7.9, 'max_lat': -2.8, 'min_lng': -41.4, 'max_lng': -37.3},
    'DF': {'min_lat': -16.1, 'max_lat': -15.5, 'min_lng': -48.3, 'max_lng': -47.3},
    'ES': {'min_lat': -21.3, 'max_lat': -17.9, 'min_lng': -41.9, 'max_lng': -39.7},
    'GO': {'min_lat': -19.5, 'max_lat': -12.4, 'min_lng': -53.3, 'max_lng': -45.9},
    'MA': {'min_lat': -10.3, 'max_lat': -1.0, 'min_lng': -48.6, 'max_lng': -41.8},
    'MT': {'min_lat': -18.1, 'max_lat': -7.3, 'min_lng': -61.6, 'max_lng': -50.2},
    'MS': {'min_lat': -24.1, 'max_lat': -17.2, 'min_lng': -58.2, 'max_lng': -50.9},
    'MG': {'min_lat': -22.9, 'max_lat': -14.2, 'min_lng': -51.1, 'max_lng': -39.9},
    'PA': {'min_lat': -9.9, 'max_lat': 2.6, 'min_lng': -58.9, 'max_lng': -46.0},
    'PB': {'min_lat': -8.3, 'max_lat': -6.0, 'min_lng': -38.8, 'max_lng': -34.8},
    'PR': {'min_lat': -26.7, 'max_lat': -22.5, 'min_lng': -54.6, 'max_lng': -48.0},
    'PE': {'min_lat': -9.5, 'max_lat': -7.2, 'min_lng': -41.4, 'max_lng': -34.8},
    'PI': {'min_lat': -10.9, 'max_lat': -2.7, 'min_lng': -45.9, 'max_lng': -40.4},
    'RJ': {'min_lat': -23.4, 'max_lat': -20.8, 'min_lng': -44.9, 'max_lng': -40.9},
    'RN': {'min_lat': -6.9, 'max_lat': -4.8, 'min_lng': -38.6, 'max_lng': -34.9},
    'RS': {'min_lat': -33.8, 'max_lat': -27.1, 'min_lng': -57.6, 'max_lng': -49.7},
    'RO': {'min_lat': -13.7, 'max_lat': -7.9, 'min_lng': -66.0, 'max_lng': -59.8},
    'RR': {'min_lat': -5.3, 'max_lat': 5.3, 'min_lng': -64.8, 'max_lng': -59.0},
    'SC': {'min_lat': -29.4, 'max_lat': -25.9, 'min_lng': -53.8, 'max_lng': -48.3},
    'SP': {'min_lat': -25.3, 'max_lat': -19.8, 'min_lng': -53.1, 'max_lng': -44.2},
    'SE': {'min_lat': -11.6, 'max_lat': -9.5, 'min_lng': -38.2, 'max_lng': -36.4},
    'TO': {'min_lat': -13.5, 'max_lat': -5.2, 'min_lng': -50.8, 'max_lng': -45.7}
}

# =========================================
# VARIÁVEIS GLOBAIS
# =========================================
geocode_cache = {}
cache_hits = 0
requisicoes_feitas = 0


def geocode_address(logradouro, numero, bairro, municipio, uf, cep):
    """
    Geocodifica um endereço usando Here Maps API
    
    Returns:
        tuple: (latitude, longitude) ou (None, None) se não encontrado
    """
    global requisicoes_feitas, cache_hits
    
    try:
        # Validar API Key
        if not HERE_MAPS_API_KEY or HERE_MAPS_API_KEY == "COLE_SUA_API_KEY_AQUI":
            print("⚠️  ERRO: API Key do Here Maps não configurada!")
            return (None, None)
        
        # Validação mínima de dados
        tem_municipio = municipio and str(municipio) not in ['None', 'nan', '']
        tem_uf = uf and str(uf) not in ['None', 'nan', '']
        tem_cep = cep and str(cep) not in ['None', 'nan', '']
        
        if not ((tem_municipio and tem_uf) or tem_cep):
            return (None, None)
        
        # Montar endereço otimizado
        parts = []
        
        # 1. MUNICÍPIO + UF (contexto)
        if tem_municipio and tem_uf:
            parts.append(f"{str(municipio)}, {str(uf)}")
        
        # 2. CEP (precisão)
        if tem_cep:
            cep_limpo = str(cep).replace('-', '').replace('.', '')
            parts.append(f"CEP {cep_limpo}")
        
        # 3. LOGRADOURO + NÚMERO
        if logradouro and str(logradouro) not in ['None', 'nan', '']:
            if numero and str(numero) not in ['None', 'nan', '']:
                parts.append(f"{str(logradouro)}, {str(numero)}")
            else:
                parts.append(str(logradouro))
        
        # 4. BAIRRO
        if bairro and str(bairro) not in ['None', 'nan', '']:
            parts.append(str(bairro))
        
        full_address = ", ".join(parts) + ", Brasil"
        
        # Verificar cache
        if full_address in geocode_cache:
            cache_hits += 1
            return geocode_cache[full_address]
        
        # Verificar limite
        if requisicoes_feitas >= LIMITE_MAXIMO_GEOCODIFICACOES:
            print(f"🛑 LIMITE ATINGIDO! {requisicoes_feitas}/{LIMITE_MAXIMO_GEOCODIFICACOES} requisições")
            return (None, None)
        
        # Chamar API Here Maps
        url = 'https://geocode.search.hereapi.com/v1/geocode'
        params = {
            'q': full_address,
            'apiKey': HERE_MAPS_API_KEY,
            'limit': 1
        }
        
        # Rate limiting: 20 req/seg
        time.sleep(0.05)
        
        response = requests.get(url, params=params, timeout=10)
        requisicoes_feitas += 1
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('items') and len(data['items']) > 0:
                position = data['items'][0]['position']
                lat = position['lat']
                lng = position['lng']
                
                # Validação BBOX
                if tem_uf and uf in ESTADOS_BBOX:
                    bbox = ESTADOS_BBOX[uf]
                    
                    dentro_bbox = (
                        bbox['min_lat'] <= lat <= bbox['max_lat'] and
                        bbox['min_lng'] <= lng <= bbox['max_lng']
                    )
                    
                    if not dentro_bbox:
                        print(f"⚠️  Coordenadas fora de {uf}: {full_address}")
                        geocode_cache[full_address] = (None, None)
                        return (None, None)
                
                # Coordenadas válidas
                result = (lat, lng)
                geocode_cache[full_address] = result
                return result
            else:
                geocode_cache[full_address] = (None, None)
                return (None, None)
        else:
            print(f"⚠️  Erro HTTP {response.status_code}")
            return (None, None)
            
    except requests.exceptions.Timeout:
        print(f"⚠️  Timeout ao geocodificar: {full_address}")
        return (None, None)
    except Exception as e:
        print(f"⚠️  Erro inesperado: {e}")
        return (None, None)


def geocodificar_customers(limit=None):
    """
    Geocodifica clientes sem coordenadas
    
    Args:
        limit: Número máximo de clientes a processar (None = todos)
    """
    print("\n" + "="*80)
    print("🗺️  GEOCODIFICAÇÃO DE CLIENTES")
    print("="*80)
    
    try:
        # Conectar ao banco
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        
        print(f"\n✓ Conectado ao banco: {DB_NAME}@{DB_HOST}")
        
        # Verificar se colunas existem
        cursor.execute("""
            SELECT COUNT(*) as existe
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME IN ('latitude', 'longitude')
        """, (DB_NAME,))
        
        if cursor.fetchone()['existe'] < 2:
            print("\n❌ ERRO: Colunas latitude/longitude não existem!")
            print("Execute primeiro: database/migrations/adicionar_geocoding_customers.sql")
            return
        
        # Buscar clientes sem geocodificação
        query = """
            SELECT id, name, address, number, neighborhood, city, uf, cep
            FROM customers
            WHERE active = TRUE
              AND (latitude IS NULL OR longitude IS NULL)
              AND city IS NOT NULL
              AND uf IS NOT NULL
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        customers = cursor.fetchall()
        
        total = len(customers)
        
        if total == 0:
            print("\n✓ Todos os clientes ativos já estão geocodificados!")
            return
        
        print(f"\n📊 Encontrados {total} clientes para geocodificar")
        print(f"⚠️  Limite por execução: {LIMITE_MAXIMO_GEOCODIFICACOES} requisições")
        
        # Processar
        sucesso = 0
        falhas = 0
        
        print("\n🔄 Processando...")
        
        for i, customer in enumerate(customers, 1):
            # Progresso
            if i % 10 == 0 or i == total:
                print(f"   [{i}/{total}] Processados: {sucesso} sucesso, {falhas} falhas, {cache_hits} cache hits")
            
            # Geocodificar
            lat, lng = geocode_address(
                customer.get('address'),
                customer.get('number'),
                customer.get('neighborhood'),
                customer.get('city'),
                customer.get('uf'),
                customer.get('cep')
            )
            
            # Atualizar banco
            if lat and lng:
                cursor.execute("""
                    UPDATE customers
                    SET latitude = %s, longitude = %s
                    WHERE id = %s
                """, (lat, lng, customer['id']))
                sucesso += 1
            else:
                falhas += 1
            
            # Commit a cada 10 registros
            if i % 10 == 0:
                conn.commit()
        
        # Commit final
        conn.commit()
        
        # Estatísticas finais
        print("\n" + "="*80)
        print("✅ GEOCODIFICAÇÃO CONCLUÍDA!")
        print("="*80)
        print(f"\n📊 Estatísticas:")
        print(f"   • Total processado: {total}")
        print(f"   • Sucesso: {sucesso} ({sucesso*100//total if total > 0 else 0}%)")
        print(f"   • Falhas: {falhas}")
        print(f"   • Cache hits: {cache_hits}")
        print(f"   • Requisições à API: {requisicoes_feitas}")
        
        # Status geral
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(latitude) as com_geocoding,
                COUNT(*) - COUNT(latitude) as sem_geocoding
            FROM customers
            WHERE active = TRUE
        """)
        stats = cursor.fetchone()
        
        print(f"\n📍 Status Geral:")
        print(f"   • Total de clientes ativos: {stats['total']}")
        print(f"   • Com geocoding: {stats['com_geocoding']}")
        print(f"   • Sem geocoding: {stats['sem_geocoding']}")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"\n❌ ERRO DE CONEXÃO: {err}")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Geocodificar clientes')
    parser.add_argument('--limit', type=int, help='Número máximo de clientes a processar')
    parser.add_argument('--all', action='store_true', help='Processar todos os clientes')
    
    args = parser.parse_args()
    
    limit = None if args.all else (args.limit or 100)
    
    if not args.all and not args.limit:
        print(f"\n⚠️  Modo padrão: Processar apenas 100 clientes")
        print(f"   Use --limit N para processar N clientes")
        print(f"   Use --all para processar todos\n")
    
    geocodificar_customers(limit=limit)
