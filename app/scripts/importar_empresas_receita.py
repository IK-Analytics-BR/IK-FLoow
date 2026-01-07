"""
Script para importar arquivo EMPRESAS.CSV da Receita Federal
Este arquivo contém a RAZÃO SOCIAL oficial das empresas
"""
import csv
import mysql.connector
import os
from datetime import datetime

# =========================================
# CONFIGURAÇÕES
# =========================================
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "aritana",
    "database": "supply_chain_system"
}

# Caminho para os arquivos CSV (ajustar conforme necessário)
CSV_DIR = "C:/Users/arita/CascadeProjects/SupplyChainSystem/app/scripts/downloads_receita"

# =========================================
# FUNÇÃO - IMPORTAR ARQUIVO EMPRESAS
# =========================================
def importar_arquivo_empresas(arquivo_csv):
    """
    Importa um arquivo Empresas*.csv da Receita Federal
    
    Layout do arquivo Empresas:
    0 - CNPJ_BASICO (8 dígitos)
    1 - RAZAO_SOCIAL
    2 - NATUREZA_JURIDICA
    3 - QUALIFICACAO_RESPONSAVEL
    4 - CAPITAL_SOCIAL
    5 - PORTE_EMPRESA
    6 - ENTE_FEDERATIVO
    """
    print(f"\n[IMPORTANDO] {arquivo_csv}")
    
    if not os.path.exists(arquivo_csv):
        print(f"[ERRO] Arquivo não encontrado: {arquivo_csv}")
        return 0
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        total_lidos = 0
        total_inseridos = 0
        total_erros = 0
        
        with open(arquivo_csv, 'r', encoding='latin1') as f:
            reader = csv.reader(f, delimiter=';', quotechar='"')
            
            batch = []
            batch_size = 1000
            
            for row in reader:
                try:
                    total_lidos += 1
                    
                    # Extrair campos
                    cnpj_basico = row[0].strip() if len(row) > 0 else None
                    razao_social = row[1].strip() if len(row) > 1 else None
                    natureza_juridica = row[2].strip() if len(row) > 2 else None
                    qualificacao_resp = row[3].strip() if len(row) > 3 else None
                    
                    # Capital social (converter para decimal)
                    try:
                        capital_social = float(row[4].replace(',', '.')) if len(row) > 4 and row[4].strip() else None
                    except:
                        capital_social = None
                    
                    porte_empresa = row[5].strip() if len(row) > 5 else None
                    ente_federativo = row[6].strip() if len(row) > 6 else None
                    
                    # Validações básicas
                    if not cnpj_basico or len(cnpj_basico) != 8:
                        total_erros += 1
                        continue
                    
                    if not razao_social:
                        total_erros += 1
                        continue
                    
                    # Adicionar ao batch
                    batch.append((
                        cnpj_basico,
                        razao_social[:150],  # Limitar tamanho
                        natureza_juridica,
                        qualificacao_resp,
                        capital_social,
                        porte_empresa,
                        ente_federativo
                    ))
                    
                    # Inserir batch quando atingir o tamanho
                    if len(batch) >= batch_size:
                        cursor.executemany("""
                            INSERT INTO empresas_receita (
                                CNPJ_BASICO,
                                RAZAO_SOCIAL,
                                NATUREZA_JURIDICA,
                                QUALIFICACAO_RESPONSAVEL,
                                CAPITAL_SOCIAL,
                                PORTE_EMPRESA,
                                ENTE_FEDERATIVO
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                RAZAO_SOCIAL = VALUES(RAZAO_SOCIAL),
                                NATUREZA_JURIDICA = VALUES(NATUREZA_JURIDICA),
                                CAPITAL_SOCIAL = VALUES(CAPITAL_SOCIAL),
                                PORTE_EMPRESA = VALUES(PORTE_EMPRESA)
                        """, batch)
                        
                        total_inseridos += len(batch)
                        conn.commit()
                        
                        print(f"[PROGRESSO] {total_lidos:,} lidos | {total_inseridos:,} inseridos | {total_erros:,} erros")
                        
                        batch = []
                
                except Exception as e:
                    total_erros += 1
                    if total_erros <= 10:  # Mostrar apenas primeiros 10 erros
                        print(f"[ERRO LINHA] {e}")
            
            # Inserir batch final
            if batch:
                cursor.executemany("""
                    INSERT INTO empresas_receita (
                        CNPJ_BASICO,
                        RAZAO_SOCIAL,
                        NATUREZA_JURIDICA,
                        QUALIFICACAO_RESPONSAVEL,
                        CAPITAL_SOCIAL,
                        PORTE_EMPRESA,
                        ENTE_FEDERATIVO
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        RAZAO_SOCIAL = VALUES(RAZAO_SOCIAL),
                        NATUREZA_JURIDICA = VALUES(NATUREZA_JURIDICA),
                        CAPITAL_SOCIAL = VALUES(CAPITAL_SOCIAL),
                        PORTE_EMPRESA = VALUES(PORTE_EMPRESA)
                """, batch)
                
                total_inseridos += len(batch)
                conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"\n[CONCLUÍDO] Arquivo: {os.path.basename(arquivo_csv)}")
        print(f"  Total lidos: {total_lidos:,}")
        print(f"  Total inseridos: {total_inseridos:,}")
        print(f"  Total erros: {total_erros:,}")
        
        return total_inseridos
        
    except Exception as e:
        print(f"[ERRO FATAL] {e}")
        return 0

# =========================================
# FUNÇÃO - ATUALIZAR EMPRESAS_FILTRADAS
# =========================================
def atualizar_empresas_filtradas_com_razao_social():
    """
    Atualiza tabela empresas_filtradas com RAZAO_SOCIAL
    fazendo JOIN com empresas_receita por CNPJ_BASICO
    """
    print("\n[ATUALIZANDO] empresas_filtradas com Razão Social...")
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Atualizar empresas_filtradas
        cursor.execute("""
            UPDATE empresas_filtradas ef
            INNER JOIN empresas_receita er ON ef.CNPJ_BASICO = er.CNPJ_BASICO
            SET 
                ef.RAZAO_SOCIAL = er.RAZAO_SOCIAL,
                ef.PORTE_EMPRESA = er.PORTE_EMPRESA,
                ef.NATUREZA_JURIDICA = er.NATUREZA_JURIDICA
        """)
        
        total_atualizados = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"[CONCLUÍDO] {total_atualizados:,} registros atualizados em empresas_filtradas")
        
        return total_atualizados
        
    except Exception as e:
        print(f"[ERRO] {e}")
        return 0

# =========================================
# FUNÇÃO - IMPORTAR TODOS OS ARQUIVOS
# =========================================
def importar_todos_arquivos_empresas(diretorio=CSV_DIR):
    """
    Importa todos os arquivos Empresas*.csv de um diretório
    """
    print("\n" + "="*60)
    print("IMPORTAÇÃO DE ARQUIVOS EMPRESAS DA RECEITA FEDERAL")
    print("="*60)
    
    if not os.path.exists(diretorio):
        print(f"[ERRO] Diretório não encontrado: {diretorio}")
        print("\nConfigure o caminho correto na variável CSV_DIR")
        return
    
    # Listar arquivos Empresas*.csv
    arquivos = [
        os.path.join(diretorio, f) 
        for f in os.listdir(diretorio) 
        if f.startswith('Empresas') and f.endswith('.csv')
    ]
    
    if not arquivos:
        print(f"[ERRO] Nenhum arquivo Empresas*.csv encontrado em {diretorio}")
        return
    
    arquivos.sort()
    
    print(f"\n[ENCONTRADOS] {len(arquivos)} arquivo(s):")
    for arq in arquivos:
        print(f"  - {os.path.basename(arq)}")
    
    # Importar cada arquivo
    total_geral = 0
    inicio = datetime.now()
    
    for arquivo in arquivos:
        total = importar_arquivo_empresas(arquivo)
        total_geral += total
    
    fim = datetime.now()
    duracao = (fim - inicio).total_seconds()
    
    print("\n" + "="*60)
    print(f"[RESUMO FINAL]")
    print(f"  Arquivos processados: {len(arquivos)}")
    print(f"  Total de empresas importadas: {total_geral:,}")
    print(f"  Tempo de execução: {duracao:.2f} segundos")
    print("="*60)
    
    # Atualizar empresas_filtradas
    input("\n[CONFIRMAR] Pressione ENTER para atualizar empresas_filtradas com Razão Social...")
    atualizar_empresas_filtradas_com_razao_social()

# =========================================
# EXECUÇÃO PRINCIPAL
# =========================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SCRIPT DE IMPORTAÇÃO - EMPRESAS RECEITA FEDERAL")
    print("="*60)
    print("\nEste script importa os arquivos Empresas*.csv da Receita Federal")
    print("que contém a RAZÃO SOCIAL oficial das empresas.\n")
    print(f"Diretório configurado: {CSV_DIR}")
    print("\nATENÇÃO: Este processo pode demorar vários minutos!")
    print("Os arquivos Empresas*.csv são grandes (milhões de registros)")
    print("="*60)
    
    opcao = input("\nDeseja continuar? (s/n): ").strip().lower()
    
    if opcao == 's':
        importar_todos_arquivos_empresas()
    else:
        print("\n[CANCELADO] Importação cancelada pelo usuário")
