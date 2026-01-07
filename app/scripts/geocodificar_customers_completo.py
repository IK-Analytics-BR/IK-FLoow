"""
Script Otimizado para Geocodificar Clientes
Usa TODOS os campos de endereço para máxima acertividade
"""

import os
import sys
import mysql.connector
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configurações
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'aritana'),
    'database': os.getenv('DB_NAME', 'supply_chain_system')
}

HERE_MAPS_API_KEY = "elCXcTWBwxAD1S9YY1ZgiBXDO3v7cfHHqg_VyJCgOak"
LIMITE_MAXIMO_GEOCODIFICACOES = 1000

ESTADOS_BBOX = {
    'SP': {'min_lat': -25.3, 'max_lat': -19.8, 'min_lng': -53.1, 'max_lng': -44.2},
    'RJ': {'min_lat': -23.4, 'max_lat': -20.8, 'min_lng': -44.9, 'max_lng': -40.9},
    'MG': {'min_lat': -22.9, 'max_lat': -14.2, 'min_lng': -51.1, 'max_lng': -39.9},
    'ES': {'min_lat': -21.3, 'max_lat': -17.9, 'min_lng': -41.9, 'max_lng': -39.7},
    'PR': {'min_lat': -26.7, 'max_lat': -22.5, 'min_lng': -54.6, 'max_lng': -48.0},
    'SC': {'min_lat': -29.4, 'max_lat': -25.9, 'min_lng': -53.8, 'max_lng': -48.3},
    'RS': {'min_lat': -33.8, 'max_lat': -27.1, 'min_lng': -57.6, 'max_lng': -49.7},
    'BA': {'min_lat': -18.5, 'max_lat': -8.5, 'min_lng': -46.6, 'max_lng': -37.3},
    'PE': {'min_lat': -9.5, 'max_lat': -7.2, 'min_lng': -41.4, 'max_lng': -34.8},
    'CE': {'min_lat': -7.9, 'max_lat': -2.8, 'min_lng': -41.4, 'max_lng': -37.3},
    'AL': {'min_lat': -10.5, 'max_lat': -8.8, 'min_lng': -38.3, 'max_lng': -35.1},
    'GO': {'min_lat': -19.5, 'max_lat': -12.4, 'min_lng': -53.3, 'max_lng': -45.9},
    'DF': {'min_lat': -16.1, 'max_lat': -15.5, 'min_lng': -48.3, 'max_lng': -47.3}
}

geocode_cache = {}
cache_hits = 0
requisicoes_feitas = 0


def limpar(val):
    if not val or str(val).strip() in ['None', 'nan', '', 'null']:
        return None
    return str(val).strip()


def montar_endereco(c):
    parts = []
    city = limpar(c.get('city'))
    state = limpar(c.get('state'))
    cep = limpar(c.get('cep'))
    address = limpar(c.get('address'))
    number = limpar(c.get('number'))
    complement = limpar(c.get('complement'))
    neighborhood = limpar(c.get('neighborhood'))
    
    if not city or not state:
        return None
    
    parts.append(f"{city}, {state}")
    
    if cep:
        cep_limpo = cep.replace('-', '').replace('.', '')
        parts.append(f"CEP {cep_limpo}")
    
    if address:
        if number:
            parts.append(f"{address}, {number}")
        else:
            parts.append(address)
    
    if complement:
        parts.append(complement)
    
    if neighborhood:
        parts.append(neighborhood)
    
    return ", ".join(parts) + ", Brasil"


def geocode(customer):
    global requisicoes_feitas, cache_hits
    
    full_address = montar_endereco(customer)
    if not full_address:
        return (None, None)
    
    if full_address in geocode_cache:
        cache_hits += 1
        return geocode_cache[full_address]
    
    if requisicoes_feitas >= LIMITE_MAXIMO_GEOCODIFICACOES:
        return (None, None)
    
    try:
        url = 'https://geocode.search.hereapi.com/v1/geocode'
        params = {'q': full_address, 'apiKey': HERE_MAPS_API_KEY, 'limit': 1}
        
        time.sleep(0.05)
        response = requests.get(url, params=params, timeout=10)
        requisicoes_feitas += 1
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items') and len(data['items']) > 0:
                pos = data['items'][0]['position']
                lat, lng = pos['lat'], pos['lng']
                
                state = limpar(customer.get('state'))
                if state and state in ESTADOS_BBOX:
                    bbox = ESTADOS_BBOX[state]
                    if not (bbox['min_lat'] <= lat <= bbox['max_lat'] and bbox['min_lng'] <= lng <= bbox['max_lng']):
                        geocode_cache[full_address] = (None, None)
                        return (None, None)
                
                geocode_cache[full_address] = (lat, lng)
                return (lat, lng)
        
        geocode_cache[full_address] = (None, None)
        return (None, None)
    except:
        return (None, None)


def main(limit=None):
    print("=" * 80)
    print("GEOCODIFICACAO DE CLIENTES")
    print("=" * 80)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print(f"\nConectado ao banco: {DB_CONFIG['database']}")
        
        query = """
            SELECT id, name, address, number, complement, neighborhood, 
                   city, state, cep
            FROM customers
            WHERE active = TRUE
              AND (latitude IS NULL OR longitude IS NULL)
              AND city IS NOT NULL
              AND state IS NOT NULL
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        customers = cursor.fetchall()
        
        total = len(customers)
        
        if total == 0:
            print("\nTodos os clientes ja estao geocodificados!")
            return
        
        print(f"\nTotal a processar: {total} clientes")
        print(f"Limite de requisicoes: {LIMITE_MAXIMO_GEOCODIFICACOES}\n")
        
        sucesso = 0
        falhas = 0
        
        print("Processando...")
        
        for i, customer in enumerate(customers, 1):
            if i % 10 == 0 or i == total:
                print(f"  [{i}/{total}] Sucesso: {sucesso}, Falhas: {falhas}, Cache: {cache_hits}")
            
            lat, lng = geocode(customer)
            
            if lat and lng:
                cursor.execute("""
                    UPDATE customers
                    SET latitude = %s, longitude = %s
                    WHERE id = %s
                """, (lat, lng, customer['id']))
                sucesso += 1
            else:
                falhas += 1
            
            if i % 10 == 0:
                conn.commit()
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("CONCLUIDO!")
        print("=" * 80)
        print(f"\nTotal processado: {total}")
        print(f"Sucesso: {sucesso} ({sucesso*100//total if total > 0 else 0}%)")
        print(f"Falhas: {falhas}")
        print(f"Cache hits: {cache_hits}")
        print(f"Requisicoes API: {requisicoes_feitas}")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(latitude) as com_geo,
                COUNT(*) - COUNT(latitude) as sem_geo
            FROM customers
            WHERE active = TRUE
        """)
        stats = cursor.fetchone()
        
        print(f"\nStatus Geral:")
        print(f"  Total ativos: {stats['total']}")
        print(f"  Com geocoding: {stats['com_geo']}")
        print(f"  Sem geocoding: {stats['sem_geo']}")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"\nERRO DE CONEXAO: {err}")
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Geocodificar clientes')
    parser.add_argument('--limit', type=int, help='Numero maximo de clientes')
    parser.add_argument('--all', action='store_true', help='Processar todos')
    
    args = parser.parse_args()
    
    limit = None if args.all else (args.limit or 100)
    
    if not args.all and not args.limit:
        print(f"\nModo padrao: 100 clientes")
        print(f"Use --limit N para N clientes")
        print(f"Use --all para todos\n")
    
    main(limit=limit)
