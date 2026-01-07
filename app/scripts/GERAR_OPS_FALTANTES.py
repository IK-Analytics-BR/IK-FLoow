# -*- coding: utf-8 -*-
"""
Gerar OPs faltantes para orçamentos aprovados
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database
from datetime import datetime, timedelta

def main():
    db = Database()
    
    print("=" * 80)
    print("GERANDO OPs FALTANTES PARA ORCAMENTOS APROVADOS")
    print("=" * 80)
    
    # 1. Buscar orçamentos aprovados sem OP
    orcs_sem_op = db.fetch_all("""
        SELECT 
            o.id AS orcamento_id, 
            o.numero AS orcamento_numero, 
            o.empresa_id,
            o.cliente_id,
            o.prazo_entrega,
            o.data_validade,
            oi.id AS item_id,
            oi.produto_id,
            oi.quantidade,
            p.name AS produto_nome,
            p.stock_quantity
        FROM orcamentos o 
        JOIN orcamento_itens oi ON oi.orcamento_id = o.id 
        JOIN products p ON p.id = oi.produto_id 
        LEFT JOIN orcamento_op_itens ooi ON ooi.orcamento_item_id = oi.id 
        WHERE ooi.id IS NULL 
          AND o.status IN ('aprovado', 'em_producao')
        ORDER BY o.id DESC
    """)
    
    if not orcs_sem_op:
        print("\nNenhum orcamento aprovado sem OP encontrado!")
        return
    
    print(f"\nEncontrados {len(orcs_sem_op)} itens de orcamentos sem OP")
    
    # Buscar etapas
    etapa_producao = db.fetch_one("""
        SELECT id FROM producao_etapas 
        WHERE ativo = 1 AND (tipo_etapa = 'producao' OR tipo_etapa IS NULL)
        ORDER BY ordem, id LIMIT 1
    """)
    etapa_separacao = db.fetch_one("""
        SELECT id FROM producao_etapas 
        WHERE ativo = 1 AND tipo_etapa = 'separacao'
        ORDER BY id DESC LIMIT 1
    """)
    
    etapa_producao_id = etapa_producao['id'] if etapa_producao else 8
    etapa_separacao_id = etapa_separacao['id'] if etapa_separacao else etapa_producao_id
    
    print(f"Etapa producao: {etapa_producao_id}")
    print(f"Etapa separacao: {etapa_separacao_id}")
    
    # 2. Criar grupo e OPs
    orcamentos_processados = {}  # {orcamento_id: grupo_id}
    ops_criadas = 0
    
    for item in orcs_sem_op:
        orc_id = item['orcamento_id']
        
        # Criar grupo se não existe
        if orc_id not in orcamentos_processados:
            grupo = db.fetch_one("""
                SELECT id FROM orcamento_op_grupos WHERE orcamento_id = %s
            """, (orc_id,))
            
            if not grupo:
                grupo_id = db.insert("""
                    INSERT INTO orcamento_op_grupos (orcamento_id, empresa_id, cliente_id)
                    VALUES (%s, %s, %s)
                """, (orc_id, item['empresa_id'], item['cliente_id']))
            else:
                grupo_id = grupo['id']
            
            orcamentos_processados[orc_id] = grupo_id
        
        # Verificar estoque
        estoque = float(item['stock_quantity'] or 0)
        quantidade = float(item['quantidade'])
        
        # Definir tipo de OP
        if estoque >= quantidade:
            tipo_op = 'separacao'
            etapa_id = etapa_separacao_id
            obs = f"PRODUTO EM ESTOQUE - Apenas separar e embalar. {quantidade} unidades."
        else:
            tipo_op = 'producao'
            etapa_id = etapa_producao_id
            obs = f"Producao de {quantidade} unidades"
        
        # Data prevista
        data_solicitacao = datetime.now().date()
        try:
            prazo = item.get('prazo_entrega')
            if prazo:
                data_prevista = data_solicitacao + timedelta(days=int(prazo))
            else:
                data_prevista = item.get('data_validade') or data_solicitacao + timedelta(days=30)
        except:
            data_prevista = data_solicitacao + timedelta(days=30)
        
        # Gerar número da OP
        ultimo = db.fetch_one("SELECT MAX(id) as max_id FROM ordens_producao")
        prox_id = (ultimo['max_id'] or 0) + 1
        numero_op = f"OP-2025-{prox_id:04d}"
        
        # Criar OP com a QUANTIDADE CORRETA do orçamento
        op_id = db.insert("""
            INSERT INTO ordens_producao (
                empresa_id, cliente_id, produto_id, quantidade,
                data_solicitacao, data_prevista, observacoes,
                etapa_atual_id, status, tipo_op, obs_estoque, numero_op
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendente', %s, %s, %s)
        """, (
            item['empresa_id'],
            item['cliente_id'],
            item['produto_id'],
            quantidade,  # QUANTIDADE CORRETA DO ORÇAMENTO
            data_solicitacao,
            data_prevista,
            f"Orcamento {item['orcamento_numero']} | {obs}",
            etapa_id,
            tipo_op,
            obs,
            numero_op
        ))
        
        # Criar lote com a QUANTIDADE CORRETA
        db.insert("""
            INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status)
            VALUES (%s, 1, %s, %s, 'pendente')
        """, (op_id, quantidade, etapa_id))
        
        # Vincular OP ao item do orçamento com a QUANTIDADE CORRETA
        grupo_id = orcamentos_processados[orc_id]
        db.insert("""
            INSERT INTO orcamento_op_itens (
                orcamento_id, orcamento_item_id, ordem_producao_id, 
                produto_id, quantidade, tem_template, grupo_id
            ) VALUES (%s, %s, %s, %s, %s, 0, %s)
        """, (orc_id, item['item_id'], op_id, item['produto_id'], quantidade, grupo_id))
        
        ops_criadas += 1
        print(f"  [OK] {item['orcamento_numero']} -> {numero_op} ({tipo_op}) - Qtd: {quantidade}")
    
    print("\n" + "=" * 80)
    print(f"CONCLUIDO! {ops_criadas} OPs criadas")
    print("=" * 80)

if __name__ == "__main__":
    main()
