#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cria a tabela nfe_numeracao"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import get_db

db = get_db()

# Primeiro dropar a tabela se existir (para recriar corretamente)
try:
    db.execute_query("DROP TABLE IF EXISTS nfe_numeracao")
    print("Tabela antiga removida (se existia)")
except:
    pass

sql = """
CREATE TABLE nfe_numeracao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    serie INT NOT NULL DEFAULT 1,
    ambiente VARCHAR(20) NOT NULL DEFAULT 'homologacao',
    ultimo_numero INT NOT NULL DEFAULT 0,
    observacao VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_empresa_serie_ambiente (empresa_id, serie, ambiente),
    INDEX idx_empresa (empresa_id),
    INDEX idx_ambiente (ambiente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

try:
    db.execute_query(sql)
    print("Tabela nfe_numeracao criada com sucesso!")
except Exception as e:
    print(f"Erro: {e}")
