# -*- coding: utf-8 -*-
"""
Script para adicionar colunas necessárias para o novo fluxo de OP com estoque
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=== Adicionando colunas para novo fluxo de OP ===\n")
    
    # 1. Adicionar coluna tipo_op
    print("1. Adicionando coluna tipo_op em ordens_producao...")
    try:
        db.execute("""
            ALTER TABLE ordens_producao 
            ADD COLUMN tipo_op ENUM('producao', 'separacao', 'mista') DEFAULT 'producao'
            COMMENT 'Tipo da OP: producao=fabricar, separacao=apenas separar do estoque'
        """)
        print("   [OK] Coluna tipo_op adicionada")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("   [JA EXISTE] Coluna tipo_op ja existe")
        else:
            print(f"   [ERRO] {e}")
    
    # 2. Adicionar coluna obs_estoque
    print("\n2. Adicionando coluna obs_estoque em ordens_producao...")
    try:
        db.execute("""
            ALTER TABLE ordens_producao 
            ADD COLUMN obs_estoque TEXT NULL
            COMMENT 'Informacoes sobre alocacao de estoque'
        """)
        print("   [OK] Coluna obs_estoque adicionada")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("   [JA EXISTE] Coluna obs_estoque ja existe")
        else:
            print(f"   [ERRO] {e}")
    
    # 3. Adicionar coluna tipo_etapa em producao_etapas
    print("\n3. Adicionando coluna tipo_etapa em producao_etapas...")
    try:
        db.execute("""
            ALTER TABLE producao_etapas 
            ADD COLUMN tipo_etapa ENUM('producao', 'separacao', 'embalagem', 'expedicao') DEFAULT 'producao'
            COMMENT 'Tipo da etapa'
        """)
        print("   [OK] Coluna tipo_etapa adicionada")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("   [JA EXISTE] Coluna tipo_etapa ja existe")
        else:
            print(f"   [ERRO] {e}")
    
    # 4. Criar etapa de Separacao/Embalagem se nao existir
    print("\n4. Verificando etapa de Separacao/Embalagem...")
    etapa = db.fetch_one("SELECT id FROM producao_etapas WHERE nome LIKE '%Separa%'")
    if not etapa:
        try:
            db.insert("""
                INSERT INTO producao_etapas (nome, descricao, ordem, ativo, tipo_etapa)
                VALUES ('Separacao e Embalagem', 'Separar produto do estoque e embalar para envio', 999, 1, 'separacao')
            """)
            print("   [OK] Etapa de Separacao/Embalagem criada")
        except Exception as e:
            print(f"   [ERRO] {e}")
    else:
        print(f"   [JA EXISTE] Etapa de separacao encontrada (ID: {etapa['id']})")
    
    # 5. Verificar tabela estoque_reservas
    print("\n5. Verificando tabela estoque_reservas...")
    try:
        db.fetch_one("SELECT 1 FROM estoque_reservas LIMIT 1")
        print("   [OK] Tabela estoque_reservas existe")
    except Exception as e:
        print(f"   [AVISO] Tabela estoque_reservas pode nao existir: {e}")
        print("   Execute o script 060_ORCAMENTO_DNA_ESTOQUE.sql")
    
    print("\n=== Concluido ===")

if __name__ == "__main__":
    main()
