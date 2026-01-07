"""Criar tabelas de pausas de produção"""
import sys
sys.path.insert(0, '.')
from app.database import Database

db = Database()

queries = [
    # Tabela de motivos
    """
    CREATE TABLE IF NOT EXISTS producao_pausas_motivos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        descricao TEXT,
        tipo ENUM('produtivo', 'improdutivo') NOT NULL DEFAULT 'improdutivo',
        icone VARCHAR(50) DEFAULT 'bi-pause-circle',
        cor_hex VARCHAR(7) DEFAULT '#6c757d',
        ativo TINYINT(1) DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_tipo (tipo),
        INDEX idx_ativo (ativo)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    
    # Tabela de pausas
    """
    CREATE TABLE IF NOT EXISTS producao_pausas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        lote_id INT NOT NULL,
        ordem_producao_id INT NOT NULL,
        operador_id INT NOT NULL,
        motivo_id INT NOT NULL,
        etapa_id INT,
        inicio DATETIME NOT NULL,
        fim DATETIME,
        duracao_minutos INT,
        observacao TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_lote (lote_id),
        INDEX idx_operador (operador_id),
        INDEX idx_motivo (motivo_id),
        INDEX idx_inicio (inicio),
        INDEX idx_fim (fim)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]

motivos = [
    ("Início de Jornada", "Início do expediente de trabalho", "produtivo", "bi-sunrise", "#28a745"),
    ("Fim de Jornada", "Encerramento do expediente", "improdutivo", "bi-sunset", "#dc3545"),
    ("Almoço", "Intervalo para almoço", "improdutivo", "bi-cup-hot", "#fd7e14"),
    ("Lanche/Café", "Intervalo para lanche ou café", "improdutivo", "bi-cup", "#ffc107"),
    ("Banheiro", "Necessidade pessoal", "improdutivo", "bi-door-open", "#6c757d"),
    ("Aguardando Material", "Esperando material para continuar", "improdutivo", "bi-box-seam", "#17a2b8"),
    ("Falta de Energia", "Queda ou falta de energia elétrica", "improdutivo", "bi-lightning", "#343a40"),
    ("Setup de Máquina", "Configuração/preparação da máquina", "produtivo", "bi-gear", "#0d6efd"),
    ("Troca de Ferramenta", "Troca de ferramenta ou molde", "produtivo", "bi-tools", "#6610f2"),
    ("Manutenção Preventiva", "Manutenção programada", "produtivo", "bi-wrench", "#20c997"),
    ("Manutenção Corretiva", "Correção de problema na máquina", "produtivo", "bi-exclamation-triangle", "#e83e8c"),
    ("Correção de Qualidade", "Ajuste para corrigir problema de qualidade", "produtivo", "bi-check2-square", "#6f42c1"),
    ("Limpeza de Máquina", "Limpeza necessária do equipamento", "produtivo", "bi-droplet", "#0dcaf0"),
]

print("Criando tabelas...")
for i, q in enumerate(queries):
    try:
        db.execute(q)
        print(f"  Query {i+1} OK")
    except Exception as e:
        print(f"  Query {i+1} erro: {e}")

print("\nInserindo motivos...")
for m in motivos:
    try:
        exists = db.fetch_one("SELECT id FROM producao_pausas_motivos WHERE nome = %s", (m[0],))
        if not exists:
            db.insert("""
                INSERT INTO producao_pausas_motivos (nome, descricao, tipo, icone, cor_hex) 
                VALUES (%s, %s, %s, %s, %s)
            """, m)
            print(f"  + {m[0]}")
        else:
            print(f"  = {m[0]} (já existe)")
    except Exception as e:
        print(f"  Erro {m[0]}: {e}")

print("\nVerificando...")
count = db.fetch_one("SELECT COUNT(*) as c FROM producao_pausas_motivos")
print(f"Total de motivos: {count['c']}")

print("\nTabelas criadas com sucesso!")
