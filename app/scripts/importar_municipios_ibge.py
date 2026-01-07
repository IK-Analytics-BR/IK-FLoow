#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para importar municípios IBGE para o banco de dados
Busca dados oficiais do IBGE e insere na tabela municipios_ibge

Uso:
    python app/scripts/importar_municipios_ibge.py
"""

import sys
import os
import requests
import mysql.connector
from mysql.connector import Error

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config_local import DB_CONFIG

# URL da API do IBGE para municípios
IBGE_API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

# Mapeamento de códigos UF
CODIGO_UF = {
    'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29',
    'CE': '23', 'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21',
    'MT': '51', 'MS': '50', 'MG': '31', 'PA': '15', 'PB': '25',
    'PR': '41', 'PE': '26', 'PI': '22', 'RJ': '33', 'RN': '24',
    'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42', 'SP': '35',
    'SE': '28', 'TO': '17'
}

def conectar_banco():
    """Conecta ao banco de dados MySQL"""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        if connection.is_connected():
            print("✅ Conectado ao banco de dados MySQL")
            return connection
    except Error as e:
        print(f"❌ Erro ao conectar ao MySQL: {e}")
        return None

def buscar_municipios_ibge():
    """Busca todos os municípios da API do IBGE"""
    print("\n📡 Buscando municípios da API do IBGE...")
    print(f"URL: {IBGE_API_URL}")
    
    try:
        response = requests.get(IBGE_API_URL, timeout=30)
        response.raise_for_status()
        
        municipios = response.json()
        print(f"✅ {len(municipios)} municípios encontrados")
        return municipios
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar dados do IBGE: {e}")
        return None

def limpar_tabela(connection):
    """Limpa a tabela de municípios antes de inserir"""
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM municipios_ibge")
        connection.commit()
        print("🗑️  Tabela municipios_ibge limpa")
        cursor.close()
    except Error as e:
        print(f"⚠️  Aviso ao limpar tabela: {e}")

def inserir_municipios(connection, municipios):
    """Insere os municípios no banco de dados"""
    if not municipios:
        print("❌ Nenhum município para inserir")
        return False
    
    print(f"\n💾 Inserindo {len(municipios)} municípios no banco...")
    
    cursor = connection.cursor()
    
    sql = """
        INSERT INTO municipios_ibge (codigo_ibge, nome, uf, codigo_uf)
        VALUES (%s, %s, %s, %s)
    """
    
    sucesso = 0
    erro = 0
    
    for i, municipio in enumerate(municipios, 1):
        try:
            # Extrair dados do JSON
            codigo_ibge = str(municipio['id'])
            nome = municipio['nome']
            uf = municipio['microrregiao']['mesorregiao']['UF']['sigla']
            codigo_uf = CODIGO_UF.get(uf, '00')
            
            # Inserir no banco
            cursor.execute(sql, (codigo_ibge, nome, uf, codigo_uf))
            sucesso += 1
            
            # Mostrar progresso a cada 500 municípios
            if i % 500 == 0:
                print(f"   Processados: {i}/{len(municipios)} ({(i/len(municipios)*100):.1f}%)")
                connection.commit()  # Commit parcial
                
        except Exception as e:
            erro += 1
            print(f"⚠️  Erro ao inserir {nome} ({codigo_ibge}): {e}")
    
    # Commit final
    connection.commit()
    cursor.close()
    
    print(f"\n✅ Importação concluída!")
    print(f"   Sucesso: {sucesso}")
    print(f"   Erros: {erro}")
    print(f"   Total: {len(municipios)}")
    
    return sucesso > 0

def verificar_importacao(connection):
    """Verifica se a importação foi bem-sucedida"""
    print("\n🔍 Verificando importação...")
    
    cursor = connection.cursor()
    
    # Total de municípios
    cursor.execute("SELECT COUNT(*) FROM municipios_ibge")
    total = cursor.fetchone()[0]
    print(f"   Total de municípios: {total}")
    
    # Municípios por UF
    cursor.execute("""
        SELECT uf, COUNT(*) as total 
        FROM municipios_ibge 
        GROUP BY uf 
        ORDER BY uf
    """)
    
    print("\n📊 Municípios por UF:")
    for uf, count in cursor.fetchall():
        print(f"   {uf}: {count}")
    
    # Exemplos de municípios
    print("\n📋 Exemplos de municípios:")
    cursor.execute("""
        SELECT codigo_ibge, nome, uf 
        FROM municipios_ibge 
        WHERE nome IN ('São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Brasília', 'Salvador')
        ORDER BY nome
    """)
    
    for codigo, nome, uf in cursor.fetchall():
        print(f"   {codigo} - {nome}/{uf}")
    
    cursor.close()

def main():
    """Função principal"""
    print("=" * 70)
    print("IMPORTAÇÃO DE MUNICÍPIOS IBGE")
    print("=" * 70)
    
    # Conectar ao banco
    connection = conectar_banco()
    if not connection:
        print("❌ Não foi possível conectar ao banco de dados")
        return
    
    try:
        # Buscar municípios da API do IBGE
        municipios = buscar_municipios_ibge()
        
        if not municipios:
            print("❌ Não foi possível buscar os municípios")
            return
        
        # Limpar tabela existente
        limpar_tabela(connection)
        
        # Inserir municípios
        if inserir_municipios(connection, municipios):
            # Verificar importação
            verificar_importacao(connection)
            print("\n✅ Importação concluída com sucesso!")
        else:
            print("\n❌ Falha na importação")
    
    except Exception as e:
        print(f"\n❌ Erro durante a importação: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n🔌 Conexão com o banco fechada")

if __name__ == "__main__":
    main()
