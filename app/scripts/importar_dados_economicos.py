"""
Script de Importação de Dados Econômicos Reais para o Portal
Fontes: IBGE API, IPEA Data API, arquivos CSV

Uso:
    python scripts/importar_dados_economicos.py --todos
    python scripts/importar_dados_economicos.py --municipios
    python scripts/importar_dados_economicos.py --pib
    python scripts/importar_dados_economicos.py --ipea
"""
import sys
import os
import json
import argparse
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import get_db_connection

# ============================================================
# Configurações
# ============================================================
IBGE_API = "https://servicodados.ibge.gov.br/api/v3"
IPEA_API = "http://www.ipeadata.gov.br/api/odata4"
UF_MS = "50"  # Código IBGE de MS

# ============================================================
# Importar Municípios de MS (IBGE API)
# ============================================================
def importar_municipios():
    """Importa todos os 79 municípios de MS via API do IBGE"""
    print("\n[MUNICIPIOS] Buscando municípios de MS na API do IBGE...")
    
    url = f"{IBGE_API}/malhas/estados/{UF_MS}?formato=application/vnd.geo+json&qualidade=minima"
    url_municipios = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF_MS}/municipios"
    
    try:
        resp = requests.get(url_municipios, timeout=30)
        resp.raise_for_status()
        municipios = resp.json()
        print(f"[MUNICIPIOS] {len(municipios)} municípios encontrados")
    except Exception as e:
        print(f"[MUNICIPIOS] Erro ao buscar municípios: {e}")
        return
    
    # Buscar população estimada
    print("[MUNICIPIOS] Buscando população estimada...")
    try:
        url_pop = f"{IBGE_API}/agregados/6579/periodos/-1/variaveis/9324?localidades=N6[N3[{UF_MS}]]"
        resp_pop = requests.get(url_pop, timeout=60)
        pop_data = resp_pop.json()
        populacao_map = {}
        if pop_data and len(pop_data) > 0:
            for resultado in pop_data[0].get('resultados', []):
                for serie in resultado.get('series', []):
                    cod = serie['localidade']['id']
                    valores = serie.get('serie', {})
                    ultimo_valor = list(valores.values())[-1] if valores else '0'
                    populacao_map[cod] = int(ultimo_valor.replace('.', '').replace('-', '0'))
        print(f"[MUNICIPIOS] População obtida para {len(populacao_map)} municípios")
    except Exception as e:
        print(f"[MUNICIPIOS] Erro ao buscar população: {e}")
        populacao_map = {}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inseridos = 0
    for m in municipios:
        codigo = str(m['id'])
        nome = m['nome']
        micro = m.get('microrregiao', {}).get('nome', '')
        meso = m.get('microrregiao', {}).get('mesorregiao', {}).get('nome', '')
        pop = populacao_map.get(codigo, 0)
        
        # Determinar região macro
        regiao = 'Campo Grande'
        if meso in ['Sudoeste de Mato Grosso do Sul']:
            regiao = 'Dourados'
        elif meso in ['Leste de Mato Grosso do Sul']:
            regiao = 'Tres Lagoas'
        elif meso in ['Pantanais Sul Mato-grossense']:
            regiao = 'Corumba'
        
        try:
            cursor.execute("""
                INSERT INTO dev_eco_municipios (codigo_ibge, nome, microrregiao, mesorregiao, populacao, regiao_macro)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    nome = VALUES(nome),
                    microrregiao = VALUES(microrregiao),
                    mesorregiao = VALUES(mesorregiao),
                    populacao = VALUES(populacao),
                    regiao_macro = VALUES(regiao_macro)
            """, (codigo, nome, micro, meso, pop, regiao))
            inseridos += 1
        except Exception as e:
            print(f"[MUNICIPIOS] Erro ao inserir {nome}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[MUNICIPIOS] {inseridos} municípios inseridos/atualizados")

# ============================================================
# Importar PIB Municipal (IBGE SIDRA)
# ============================================================
def importar_pib():
    """Importa PIB municipal via API SIDRA/IBGE"""
    print("\n[PIB] Buscando PIB municipal na API do IBGE...")
    
    # Tabela 5938 - PIB dos Municípios
    # Variável 37 = PIB a preços correntes (R$ 1.000)
    url = f"{IBGE_API}/agregados/5938/periodos/2020|2021/variaveis/37|513|517|521|525|543?localidades=N6[N3[{UF_MS}]]"
    
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        dados = resp.json()
        print(f"[PIB] Dados recebidos: {len(dados)} variáveis")
    except Exception as e:
        print(f"[PIB] Erro ao buscar PIB: {e}")
        print("[PIB] Tente acessar manualmente: https://sidra.ibge.gov.br/tabela/5938")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Mapear códigos IBGE para IDs internos
    cursor.execute("SELECT id, codigo_ibge FROM dev_eco_municipios")
    mapa_ids = {row['codigo_ibge']: row['id'] for row in cursor.fetchall()}
    
    inseridos = 0
    for variavel in dados:
        var_id = variavel.get('id')
        for resultado in variavel.get('resultados', []):
            for serie in resultado.get('series', []):
                cod_ibge = serie['localidade']['id']
                municipio_id = mapa_ids.get(cod_ibge)
                if not municipio_id:
                    continue
                
                for ano, valor in serie.get('serie', {}).items():
                    if valor == '-' or valor == '...':
                        continue
                    valor_num = float(valor.replace('.', '').replace(',', '.')) if valor else 0
                    
                    try:
                        # Mapear variável IBGE para coluna
                        col_map = {
                            '37': 'pib_total',
                            '513': 'pib_agropecuaria',
                            '517': 'pib_industria', 
                            '521': 'pib_servicos',
                            '525': 'pib_administracao',
                            '543': 'pib_per_capita'
                        }
                        coluna = col_map.get(str(var_id), 'pib_total')
                        
                        cursor.execute(f"""
                            INSERT INTO dev_eco_pib_municipal (municipio_id, ano, {coluna}, fonte)
                            VALUES (%s, %s, %s, 'IBGE')
                            ON DUPLICATE KEY UPDATE {coluna} = VALUES({coluna})
                        """, (municipio_id, int(ano), valor_num))
                        inseridos += 1
                    except Exception as e:
                        pass
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[PIB] {inseridos} registros inseridos/atualizados")

# ============================================================
# Importar Dados IPEA
# ============================================================
def importar_ipea():
    """Importa séries do IPEA Data via API OData"""
    print("\n[IPEA] Buscando dados do IPEA Data...")
    
    series = [
        ('BM12_PIB12', 'PIB mensal - valores correntes'),
        ('PREAM_IPCAG', 'IPCA - variação mensal'),
        ('BM12_TJOVER12', 'Taxa de juros - Over / Selic'),
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for codigo, nome in series:
        print(f"[IPEA] Buscando série: {nome} ({codigo})")
        try:
            url = f"{IPEA_API}/Metadados('{codigo}')/Valores?$top=60&$orderby=VALDATA desc"
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            dados = resp.json()
            
            valores = dados.get('value', [])
            for v in valores:
                data = v.get('VALDATA', '')[:10]  # YYYY-MM-DD
                valor = v.get('VALVALOR')
                if data and valor is not None:
                    try:
                        cursor.execute("""
                            INSERT INTO dev_eco_ipea_cache (serie_codigo, serie_nome, data_referencia, valor)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE valor = VALUES(valor)
                        """, (codigo, nome, data, float(valor)))
                    except:
                        pass
            
            print(f"[IPEA] {len(valores)} valores importados para {codigo}")
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"[IPEA] Erro na série {codigo}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()

# ============================================================
# Importar CSV genérico
# ============================================================
def importar_csv(arquivo, tabela, mapeamento):
    """Importa dados de um arquivo CSV para uma tabela MySQL"""
    import csv
    
    print(f"\n[CSV] Importando {arquivo} para {tabela}...")
    
    if not os.path.exists(arquivo):
        print(f"[CSV] Arquivo não encontrado: {arquivo}")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open(arquivo, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        inseridos = 0
        for row in reader:
            valores = {}
            for col_csv, col_db in mapeamento.items():
                valores[col_db] = row.get(col_csv, '')
            
            colunas = ', '.join(valores.keys())
            placeholders = ', '.join(['%s'] * len(valores))
            updates = ', '.join([f"{k} = VALUES({k})" for k in valores.keys()])
            
            try:
                cursor.execute(
                    f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}",
                    list(valores.values())
                )
                inseridos += 1
            except Exception as e:
                if inseridos == 0:
                    print(f"[CSV] Erro: {e}")
        
        conn.commit()
        print(f"[CSV] {inseridos} registros importados")
    
    cursor.close()
    conn.close()

# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Importar dados econômicos reais para o portal')
    parser.add_argument('--todos', action='store_true', help='Importar todos os dados')
    parser.add_argument('--municipios', action='store_true', help='Importar municípios do IBGE')
    parser.add_argument('--pib', action='store_true', help='Importar PIB municipal do IBGE')
    parser.add_argument('--ipea', action='store_true', help='Importar séries do IPEA Data')
    parser.add_argument('--csv', type=str, help='Importar arquivo CSV')
    
    args = parser.parse_args()
    
    if args.todos or args.municipios:
        importar_municipios()
    
    if args.todos or args.pib:
        importar_pib()
    
    if args.todos or args.ipea:
        importar_ipea()
    
    if args.csv:
        print(f"Para importar CSV, use a função importar_csv() diretamente no código")
    
    if not any([args.todos, args.municipios, args.pib, args.ipea, args.csv]):
        parser.print_help()
        print("\nExemplos:")
        print("  python scripts/importar_dados_economicos.py --todos")
        print("  python scripts/importar_dados_economicos.py --municipios")
        print("  python scripts/importar_dados_economicos.py --pib")
