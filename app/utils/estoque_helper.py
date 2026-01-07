"""
Helper para operações de estoque com Kardex.
Centraliza todas as movimentações de estoque com histórico completo.
"""

from flask import session, request
from database import get_db


def registrar_movimentacao(
    produto_id: int,
    tipo: str,
    quantidade: float,
    origem_tela: str,
    referencia_tipo: str = None,
    referencia_id: int = None,
    referencia_codigo: str = None,
    observacao: str = None,
    custo_unitario: float = None,
    local_id: int = 1,
    empresa_id: int = None
):
    """
    Registra uma movimentação de estoque no Kardex.
    
    Args:
        produto_id: ID do produto
        tipo: Tipo de movimentação (entrada, saida, ajuste_positivo, ajuste_negativo, 
              reserva, liberacao_reserva, baixa_producao, entrada_producao, venda, devolucao)
        quantidade: Quantidade movimentada (sempre positiva)
        origem_tela: Nome da tela/módulo que originou (ex: 'PDV', 'Orçamento', 'OP', 'Ajuste Manual')
        referencia_tipo: Tipo do documento (orcamento, op, venda, compra, ajuste, pdv, nfe)
        referencia_id: ID do documento
        referencia_codigo: Código legível (ex: ORC-0049, OP-123)
        observacao: Observação adicional
        custo_unitario: Custo unitário no momento
        local_id: ID do local de estoque (default 1)
        empresa_id: ID da empresa (se None, usa session ou 1)
    
    Returns:
        dict: Resultado da operação com estoque anterior e posterior
    """
    db = get_db()
    
    try:
        # Obter empresa_id da sessão se não fornecido
        if empresa_id is None:
            empresa_id = session.get('empresa_id', 1)
        
        # Buscar dados do produto
        produto = db.fetch_one("""
            SELECT id, name, stock_quantity, cost_price 
            FROM products WHERE id = %s
        """, (produto_id,))
        
        if not produto:
            return {'success': False, 'error': f'Produto {produto_id} não encontrado'}
        
        # Buscar estoque atual da empresa (tabela estoque_empresa)
        estoque_emp = db.fetch_one("""
            SELECT quantidade FROM estoque_empresa 
            WHERE empresa_id = %s AND produto_id = %s AND local_id = %s
        """, (empresa_id, produto_id, local_id))
        
        if estoque_emp:
            estoque_anterior = float(estoque_emp.get('quantidade') or 0)
        else:
            # Fallback para products.stock_quantity se não existir registro por empresa
            estoque_anterior = float(produto.get('stock_quantity') or 0)
        
        custo = custo_unitario or float(produto.get('cost_price') or 0)
        
        # Calcular novo estoque baseado no tipo
        tipos_entrada = ['entrada', 'ajuste_positivo', 'liberacao_reserva', 'entrada_producao', 'devolucao']
        tipos_saida = ['saida', 'ajuste_negativo', 'reserva', 'baixa_producao', 'venda', 'transferencia']
        
        if tipo in tipos_entrada:
            estoque_posterior = estoque_anterior + abs(quantidade)
        elif tipo in tipos_saida:
            estoque_posterior = estoque_anterior - abs(quantidade)
        else:
            estoque_posterior = estoque_anterior
        
        # Dados do usuário
        usuario_id = session.get('user_id', 1)
        usuario_nome = session.get('username', 'Sistema')
        ip_address = request.remote_addr if request else None
        origem_rota = request.endpoint if request else None
        
        # Buscar nome do local
        local = db.fetch_one("SELECT name FROM stock_locations WHERE id = %s", (local_id,))
        local_nome = local.get('name', 'Principal') if local else 'Principal'
        
        # Inserir movimentação no Kardex (com empresa_id)
        mov_id = db.insert("""
            INSERT INTO estoque_movimentacoes (
                empresa_id, produto_id, tipo, quantidade,
                estoque_anterior, estoque_posterior,
                origem_tela, origem_rota,
                referencia_tipo, referencia_id, referencia_codigo,
                custo_unitario, valor_total,
                local_id, local_nome,
                observacao,
                usuario_id, usuario_nome, ip_address,
                created_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s,
                %s, %s, %s,
                NOW()
            )
        """, (
            empresa_id, produto_id, tipo, abs(quantidade),
            estoque_anterior, estoque_posterior,
            origem_tela, origem_rota,
            referencia_tipo, referencia_id, referencia_codigo,
            custo, custo * abs(quantidade),
            local_id, local_nome,
            observacao,
            usuario_id, usuario_nome, ip_address
        ))
        
        # Atualizar estoque da empresa (tabela estoque_empresa)
        operacao_tipo = 'entrada' if tipo in tipos_entrada else 'saida'
        try:
            db.execute("""
                INSERT INTO estoque_empresa (empresa_id, produto_id, quantidade, ultimo_custo, local_id)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    quantidade = %s,
                    ultimo_custo = COALESCE(%s, ultimo_custo),
                    updated_at = NOW()
            """, (empresa_id, produto_id, estoque_posterior, custo, local_id,
                  estoque_posterior, custo))
            
            # Atualizar data de entrada/saída
            if operacao_tipo == 'entrada':
                db.execute("""
                    UPDATE estoque_empresa SET ultima_entrada = NOW()
                    WHERE empresa_id = %s AND produto_id = %s AND local_id = %s
                """, (empresa_id, produto_id, local_id))
            else:
                db.execute("""
                    UPDATE estoque_empresa SET ultima_saida = NOW()
                    WHERE empresa_id = %s AND produto_id = %s AND local_id = %s
                """, (empresa_id, produto_id, local_id))
        except Exception as e:
            print(f"[KARDEX] Aviso estoque_empresa: {e}")
        
        # Atualizar products.stock_quantity (compatibilidade - soma de todas empresas)
        try:
            db.execute("""
                UPDATE products p
                SET stock_quantity = (
                    SELECT COALESCE(SUM(ee.quantidade), 0)
                    FROM estoque_empresa ee
                    WHERE ee.produto_id = p.id
                )
                WHERE p.id = %s
            """, (produto_id,))
        except Exception:
            # Fallback: atualização direta
            db.execute("""
                UPDATE products SET stock_quantity = %s WHERE id = %s
            """, (estoque_posterior, produto_id))
        
        # Sincronizar current_stock para compatibilidade
        try:
            db.execute("""
                INSERT INTO current_stock (product_id, location_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = %s
            """, (produto_id, local_id, estoque_posterior, estoque_posterior))
        except Exception:
            pass
        
        print(f"[KARDEX] Empresa {empresa_id} | {origem_tela}: {tipo} de {quantidade} un. do produto {produto_id} | "
              f"Estoque: {estoque_anterior} -> {estoque_posterior}")
        
        return {
            'success': True,
            'movimentacao_id': mov_id,
            'estoque_anterior': estoque_anterior,
            'estoque_posterior': estoque_posterior,
            'tipo': tipo,
            'quantidade': quantidade
        }
        
    except Exception as e:
        print(f"[KARDEX] ERRO ao registrar movimentação: {e}")
        return {'success': False, 'error': str(e)}


def atualizar_estoque(
    produto_id: int,
    quantidade: float,
    operacao: str,
    origem_tela: str,
    referencia_tipo: str = None,
    referencia_id: int = None,
    referencia_codigo: str = None,
    observacao: str = None
):
    """
    Função simplificada para atualizar estoque.
    
    Args:
        produto_id: ID do produto
        quantidade: Quantidade a adicionar (positivo) ou subtrair (negativo)
        operacao: 'adicionar' ou 'subtrair'
        origem_tela: Nome da tela que originou
        ...demais parâmetros opcionais
    
    Returns:
        dict: Resultado da operação
    """
    if operacao == 'adicionar' or quantidade > 0:
        tipo = 'entrada'
    else:
        tipo = 'saida'
    
    return registrar_movimentacao(
        produto_id=produto_id,
        tipo=tipo,
        quantidade=abs(quantidade),
        origem_tela=origem_tela,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        referencia_codigo=referencia_codigo,
        observacao=observacao
    )


def obter_kardex_produto(produto_id: int, limite: int = 100):
    """
    Obtém o histórico Kardex de um produto.
    
    Args:
        produto_id: ID do produto
        limite: Quantidade máxima de registros
    
    Returns:
        list: Lista de movimentações
    """
    db = get_db()
    
    movimentacoes = db.fetch_all("""
        SELECT 
            em.id,
            em.tipo,
            CASE em.tipo
                WHEN 'entrada' THEN 'Entrada'
                WHEN 'saida' THEN 'Saída'
                WHEN 'ajuste_positivo' THEN 'Ajuste (+)'
                WHEN 'ajuste_negativo' THEN 'Ajuste (-)'
                WHEN 'reserva' THEN 'Reserva'
                WHEN 'liberacao_reserva' THEN 'Liberação Reserva'
                WHEN 'baixa_producao' THEN 'Baixa Produção'
                WHEN 'entrada_producao' THEN 'Entrada Produção'
                WHEN 'venda' THEN 'Venda'
                WHEN 'devolucao' THEN 'Devolução'
                WHEN 'transferencia' THEN 'Transferência'
                ELSE em.tipo
            END AS tipo_descricao,
            em.quantidade,
            em.estoque_anterior,
            em.estoque_posterior,
            em.origem_tela,
            em.referencia_tipo,
            em.referencia_id,
            em.referencia_codigo,
            em.observacao,
            em.usuario_nome,
            em.created_at
        FROM estoque_movimentacoes em
        WHERE em.produto_id = %s
        ORDER BY em.created_at DESC
        LIMIT %s
    """, (produto_id, limite))
    
    return movimentacoes or []


def obter_saldo_atual(produto_id: int):
    """
    Obtém o saldo atual de estoque de um produto.
    
    Returns:
        dict: Informações do estoque
    """
    db = get_db()
    
    produto = db.fetch_one("""
        SELECT 
            p.id,
            p.name,
            p.internal_code,
            COALESCE(p.stock_quantity, 0) as estoque_atual,
            (SELECT COUNT(*) FROM estoque_movimentacoes em WHERE em.produto_id = p.id) as total_movimentacoes,
            (SELECT MAX(created_at) FROM estoque_movimentacoes em WHERE em.produto_id = p.id) as ultima_movimentacao
        FROM products p
        WHERE p.id = %s
    """, (produto_id,))
    
    return produto
