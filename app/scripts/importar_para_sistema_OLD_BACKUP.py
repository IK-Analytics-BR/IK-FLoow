"""
Script para importar dados de empresas_filtradas para a tabela clientes do sistema
"""
import mysql.connector
import json
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

STATUS_FILE = os.path.join(os.path.dirname(__file__), 'importacao_sistema_status.json')

# =========================================
# FUNÇÃO - ATUALIZAR STATUS
# =========================================
def update_status(status_data):
    """Atualiza arquivo JSON com status da importação"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

# =========================================
# FUNÇÃO PRINCIPAL - IMPORTAR PARA SISTEMA
# =========================================
def importar_empresas_para_sistema(modo='substituir', apenas_ativas=True):
    """
    Importa empresas da tabela empresas_filtradas para clientes
    
    Args:
        modo: 'substituir' (apaga tudo) ou 'mesclar' (adiciona aos existentes)
        apenas_ativas: Se True, importa apenas empresas com SITUACAO_CADASTRAL = 2
    
    Returns:
        dict: Status da importação
    """
    print(f"[DEBUG] Iniciando importação para sistema")
    print(f"[DEBUG] Modo: {modo}")
    print(f"[DEBUG] Apenas ativas: {apenas_ativas}")
    
    status = {
        'status': 'processando',
        'etapa': 'Conectando ao banco de dados...',
        'modo': modo,
        'total_registros': 0,
        'registros_processados': 0,
        'registros_importados': 0,
        'registros_duplicados': 0,
        'registros_erro': 0,
        'percentual': 0,
        'inicio': datetime.now().isoformat()
    }
    update_status(status)
    
    try:
        # Conectar ao MySQL
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # PASSO 1: Se modo = 'substituir', apagar todos os clientes
        if modo == 'substituir':
            status['etapa'] = '⚠️ Apagando clientes existentes...'
            update_status(status)
            
            cursor.execute("DELETE FROM customers WHERE origem_cadastro = 'receita_federal'")
            deletados = cursor.rowcount
            conn.commit()
            print(f"[DEBUG] ✓ {deletados} clientes da Receita Federal apagados")
        
        # PASSO 2: Contar registros a importar
        status['etapa'] = 'Contando registros para importação...'
        update_status(status)
        
        where_clause = "WHERE SITUACAO_CADASTRAL = 2" if apenas_ativas else ""
        
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM empresas_filtradas 
            {where_clause}
        """)
        total = cursor.fetchone()[0]
        status['total_registros'] = total
        
        print(f"[DEBUG] Total de registros para importar: {total}")
        
        if total == 0:
            status['status'] = 'concluido'
            status['etapa'] = 'Nenhum registro para importar'
            status['percentual'] = 100
            update_status(status)
            cursor.close()
            conn.close()
            return status
        
        # PASSO 3: Buscar e importar registros
        status['etapa'] = 'Importando registros...'
        update_status(status)
        
        batch_size = 1000
        offset = 0
        
        while offset < total:
            # Buscar lote
            cursor.execute(f"""
                SELECT 
                    CNPJ_COMPLETO,
                    CNPJ_BASICO,
                    NOME_FANTASIA,
                    MATRIZ_FILIAL,
                    SITUACAO_CADASTRAL,
                    DATA_SITUACAO_CADASTRAL,
                    DATA_INICIO_ATIVIDADE,
                    CNAE_FISCAL_PRINCIPAL,
                    CNAE_FISCAL_SECUNDARIA,
                    TIPO_LOGRADOURO,
                    LOGRADOURO,
                    NUMERO,
                    COMPLEMENTO,
                    BAIRRO,
                    CEP,
                    UF,
                    MUNICIPIO,
                    DDD1,
                    TELEFONE1,
                    DDD2,
                    TELEFONE2,
                    DDD_FAX,
                    FAX,
                    EMAIL,
                    LATITUDE,
                    LONGITUDE
                FROM empresas_filtradas
                {where_clause}
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            batch = cursor.fetchall()
            
            if not batch:
                break
            
            print(f"[DEBUG] Processando lote {offset}-{offset+len(batch)} de {total}")
            
            # Processar cada registro do lote
            for row in batch:
                try:
                    (cnpj_completo, cnpj_basico, nome_fantasia, matriz_filial, 
                     situacao_cadastral, data_situacao, data_inicio, cnae_principal, 
                     cnae_secundaria, tipo_logradouro, logradouro, numero, complemento,
                     bairro, cep, uf, municipio, ddd1, tel1, ddd2, tel2, ddd_fax, 
                     fax, email, latitude, longitude) = row
                    
                    # Verificar se já existe (por CNPJ)
                    if modo == 'mesclar' and cnpj_completo:
                        cursor.execute("SELECT id FROM customers WHERE cnpj = %s", (cnpj_completo,))
                        if cursor.fetchone():
                            status['registros_duplicados'] += 1
                            status['registros_processados'] += 1
                            continue
                    
                    # Preparar dados para inserção
                    nome = nome_fantasia or 'Sem nome fantasia'
                    telefone = f"{ddd1 or ''}{tel1 or ''}".strip() or None
                    
                    # INSERT na tabela customers
                    cursor.execute("""
                        INSERT INTO customers (
                            name, razao_social, cnpj, cnpj_basico,
                            email, phone, phone2, ddd, ddd2, ddd_fax, fax,
                            cep, tipo_logradouro, address, number, complement, 
                            neighborhood, city, state,
                            latitude, longitude,
                            situacao_cadastral, data_situacao_cadastral, data_inicio_atividade,
                            cnae_fiscal_principal, cnae_fiscal_secundaria, matriz_filial,
                            active, origem_cadastro, created_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s
                        )
                    """, (
                        nome[:100], nome_fantasia, cnpj_completo, cnpj_basico,
                        email, telefone, tel2, ddd1, ddd2, ddd_fax, fax,
                        cep, tipo_logradouro, logradouro, numero, complemento,
                        bairro, municipio, uf,
                        latitude, longitude,
                        situacao_cadastral, data_situacao, data_inicio,
                        cnae_principal, cnae_secundaria, matriz_filial,
                        True if situacao_cadastral == 2 else False,  # active
                        'receita_federal',
                        datetime.now()
                    ))
                    
                    status['registros_importados'] += 1
                    
                except Exception as e:
                    print(f"[DEBUG] ✗ Erro ao importar registro: {e}")
                    status['registros_erro'] += 1
                
                status['registros_processados'] += 1
                status['percentual'] = int((status['registros_processados'] / total) * 100)
                
                # Atualizar status a cada 100 registros
                if status['registros_processados'] % 100 == 0:
                    status['etapa'] = f'Importando {status["registros_processados"]}/{total} registros...'
                    update_status(status)
            
            # Commit do lote
            conn.commit()
            print(f"[DEBUG] ✓ Lote {offset}-{offset+len(batch)} commitado")
            
            offset += batch_size
        
        # Finalizar
        status['status'] = 'concluido'
        status['etapa'] = f'✓ Importação concluída! {status["registros_importados"]} registros importados'
        status['percentual'] = 100
        status['fim'] = datetime.now().isoformat()
        update_status(status)
        
        cursor.close()
        conn.close()
        
        print(f"[DEBUG] ✓ Importação concluída!")
        print(f"[DEBUG] Total importados: {status['registros_importados']}")
        print(f"[DEBUG] Duplicados ignorados: {status['registros_duplicados']}")
        print(f"[DEBUG] Erros: {status['registros_erro']}")
        
        return status
        
    except Exception as e:
        status['status'] = 'erro'
        status['etapa'] = f'Erro na importação: {str(e)}'
        status['erro'] = str(e)
        update_status(status)
        print(f"[DEBUG] ✗ ERRO: {e}")
        return status

# =========================================
# EXECUÇÃO DIRETA (para testes)
# =========================================
if __name__ == "__main__":
    # Teste: importar substituindo
    resultado = importar_empresas_para_sistema(modo='substituir', apenas_ativas=True)
    print(f"\n[RESULTADO]: {resultado}")
