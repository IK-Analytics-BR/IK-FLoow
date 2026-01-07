"""
Script para adicionar campos NFC-e no banco de dados
Execute: python app/scripts/atualizar_campos_nfce.py
"""

import mysql.connector

# Configuração do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aritana',
    'database': 'supply_chain_system'
}

def main():
    print("=" * 60)
    print("ADICIONANDO CAMPOS NFC-e")
    print("=" * 60)
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Adicionar campos na tabela empresas
        print("\n[1] Adicionando campos na tabela empresas...")
        
        campos_empresas = [
            ("csc_nfce", "VARCHAR(50) NULL COMMENT 'CSC para NFC-e'"),
            ("id_csc_nfce", "VARCHAR(10) NULL COMMENT 'ID do CSC'"),
            ("ambiente_nfce", "INT DEFAULT 2 COMMENT '1=Producao, 2=Homologacao'"),
        ]
        
        for campo, definicao in campos_empresas:
            try:
                cursor.execute(f"ALTER TABLE empresas ADD COLUMN {campo} {definicao}")
                print(f"    [OK] Campo {campo} adicionado")
            except mysql.connector.Error as e:
                if 'Duplicate column' in str(e):
                    print(f"    [SKIP] Campo {campo} ja existe")
                else:
                    print(f"    [ERRO] {e}")
        
        # 2. Adicionar campos na tabela sales para NFC-e
        print("\n[2] Adicionando campos na tabela sales...")
        
        campos_sales = [
            ("numero_nfce", "INT NULL COMMENT 'Número da NFC-e'"),
            ("serie_nfce", "INT NULL DEFAULT 1 COMMENT 'Série da NFC-e'"),
            ("chave_acesso_nfce", "VARCHAR(44) NULL COMMENT 'Chave de acesso NFC-e'"),
            ("protocolo_nfce", "VARCHAR(20) NULL COMMENT 'Protocolo NFC-e'"),
            ("status_nfce", "VARCHAR(20) NULL COMMENT 'Status NFC-e'"),
            ("xml_nfce", "LONGTEXT NULL COMMENT 'XML da NFC-e'"),
            ("data_autorizacao_nfce", "DATETIME NULL COMMENT 'Data autorização NFC-e'"),
        ]
        
        for campo, definicao in campos_sales:
            try:
                cursor.execute(f"ALTER TABLE sales ADD COLUMN {campo} {definicao}")
                print(f"    [OK] Campo {campo} adicionado")
            except mysql.connector.Error as e:
                if 'Duplicate column' in str(e):
                    print(f"    [SKIP] Campo {campo} ja existe")
                else:
                    print(f"    [ERRO] {e}")
        
        # 3. Atualizar CSC da IK Analytics
        print("\n[3] Atualizando CSC da IK Analytics (empresa_id = 9)...")
        
        cursor.execute("""
            UPDATE empresas SET
                csc_nfce = '8b6c3d1d3b00be82fad2e68a03a5817688c2',
                id_csc_nfce = '000001',
                ambiente_nfce = 2
            WHERE id = 9
        """)
        
        if cursor.rowcount > 0:
            print("    [OK] CSC atualizado com sucesso!")
        else:
            print("    [AVISO] Empresa nao encontrada ou ja atualizada")
        
        conn.commit()
        
        # Verificar
        print("\n[4] Verificando configuração...")
        cursor.execute("""
            SELECT id, nome_fantasia, csc_nfce, id_csc_nfce, ambiente_nfce 
            FROM empresas WHERE id = 9
        """)
        empresa = cursor.fetchone()
        if empresa:
            print(f"    Empresa: {empresa['nome_fantasia']}")
            print(f"    CSC: {empresa['csc_nfce'][:20]}...")
            print(f"    ID CSC: {empresa['id_csc_nfce']}")
            print(f"    Ambiente NFC-e: {'Producao' if empresa['ambiente_nfce'] == 1 else 'Homologacao'}")
        
        print("\n" + "=" * 60)
        print("[OK] CONFIGURACAO NFC-e CONCLUIDA!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERRO] {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
