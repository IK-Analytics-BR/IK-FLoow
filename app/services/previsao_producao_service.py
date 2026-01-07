"""
Serviço de Previsão de Produção
Calcula previsões de conclusão baseado em:
- Jornada de trabalho
- Tempo por produto/etapa
- Fila de produção atual
"""

from datetime import datetime, timedelta, date, time
from app.database import get_db


class PrevisaoProducaoService:
    """Serviço para cálculo de previsão de produção"""
    
    def __init__(self):
        self.db = get_db()
    
    # =========================================================
    # JORNADA DE TRABALHO
    # =========================================================
    
    def get_jornada_dia(self, dia_semana: int, empresa_id: int = None) -> list:
        """
        Retorna a jornada de trabalho de um dia específico
        dia_semana: 0=Dom, 1=Seg, ..., 6=Sab
        Usa tabelas existentes: jornadas_trabalho e jornada_horarios
        """
        # Mapear número para nome do dia
        dias_nomes = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        dia_nome = dias_nomes[dia_semana] if 0 <= dia_semana <= 6 else 'Segunda'
        
        query = """
            SELECT jh.turno, jh.hora_inicio, jh.hora_fim, 
                   NULL as intervalo_inicio, NULL as intervalo_fim,
                   1 as capacidade_operadores
            FROM jornada_horarios jh
            JOIN jornadas_trabalho jt ON jh.jornada_id = jt.id
            WHERE jt.ativo = 1
              AND jh.dia_semana = %s
              AND (jt.empresa_id = %s OR %s IS NULL)
            ORDER BY jh.hora_inicio
        """
        return self.db.fetch_all(query, [dia_nome, empresa_id, empresa_id]) or []
    
    def get_minutos_uteis_dia(self, dia_semana: int, empresa_id: int = None) -> int:
        """Calcula total de minutos úteis em um dia da semana"""
        jornadas = self.get_jornada_dia(dia_semana, empresa_id)
        total_minutos = 0
        
        for j in jornadas:
            inicio = j['hora_inicio']
            fim = j['hora_fim']
            
            # Converter timedelta para minutos se necessário
            if isinstance(inicio, timedelta):
                minutos_inicio = inicio.total_seconds() / 60
            else:
                minutos_inicio = inicio.hour * 60 + inicio.minute
                
            if isinstance(fim, timedelta):
                minutos_fim = fim.total_seconds() / 60
            else:
                minutos_fim = fim.hour * 60 + fim.minute
            
            minutos_turno = minutos_fim - minutos_inicio
            
            # Subtrair intervalo
            if j['intervalo_inicio'] and j['intervalo_fim']:
                int_inicio = j['intervalo_inicio']
                int_fim = j['intervalo_fim']
                
                if isinstance(int_inicio, timedelta):
                    minutos_int_inicio = int_inicio.total_seconds() / 60
                else:
                    minutos_int_inicio = int_inicio.hour * 60 + int_inicio.minute
                    
                if isinstance(int_fim, timedelta):
                    minutos_int_fim = int_fim.total_seconds() / 60
                else:
                    minutos_int_fim = int_fim.hour * 60 + int_fim.minute
                
                minutos_turno -= (minutos_int_fim - minutos_int_inicio)
            
            total_minutos += minutos_turno
        
        return int(total_minutos)
    
    def is_dia_util(self, data: date, empresa_id: int = None) -> bool:
        """Verifica se uma data é dia útil (tem jornada e não é feriado)"""
        # Verificar feriado (tabela config_feriados se existir)
        try:
            query = """
                SELECT COUNT(*) as cnt FROM config_feriados
                WHERE (empresa_id = %s OR empresa_id IS NULL)
                  AND (data = %s OR (recorrente_anual = 1 AND MONTH(data) = MONTH(%s) AND DAY(data) = DAY(%s)))
            """
            result = self.db.fetch_one(query, [empresa_id, data, data, data])
            if result and result['cnt'] > 0:
                return False
        except:
            pass  # Tabela pode não existir ainda
        
        # Verificar se tem jornada
        dia_semana = data.weekday()  # 0=Seg, 6=Dom em Python
        # Converter para nosso padrão (0=Dom, 1=Seg, ...)
        dia_semana = (dia_semana + 1) % 7
        
        jornadas = self.get_jornada_dia(dia_semana, empresa_id)
        return len(jornadas) > 0
    
    def get_proximos_dias_uteis(self, data_inicio: date, quantidade: int, empresa_id: int = None) -> list:
        """Retorna os próximos N dias úteis a partir de uma data"""
        dias = []
        data_atual = data_inicio
        
        while len(dias) < quantidade:
            if self.is_dia_util(data_atual, empresa_id):
                dias.append(data_atual)
            data_atual += timedelta(days=1)
            
            # Limite de segurança (máximo 365 dias no futuro)
            if (data_atual - data_inicio).days > 365:
                break
        
        return dias
    
    # =========================================================
    # TEMPO DE PRODUÇÃO POR PRODUTO/ETAPA
    # =========================================================
    
    def get_tempo_produto_etapa(self, produto_id: int, etapa_id: int) -> int:
        """
        Retorna tempo estimado (minutos) para um produto em uma etapa
        Prioridade: tempo_padrao (se ajuste_manual) > tempo_medio_historico > 30 (default)
        """
        query = """
            SELECT tempo_padrao_minutos, tempo_medio_historico, ajuste_manual
            FROM produtos_tempo_etapa
            WHERE produto_id = %s AND etapa_id = %s
        """
        result = self.db.fetch_one(query, [produto_id, etapa_id])
        
        if result:
            if result['ajuste_manual'] and result['tempo_padrao_minutos'] > 0:
                return result['tempo_padrao_minutos']
            if result['tempo_medio_historico'] > 0:
                return result['tempo_medio_historico']
        
        # Default: 30 minutos se não tiver histórico
        return 30
    
    def get_tempos_todas_etapas_produto(self, produto_id: int) -> dict:
        """Retorna dicionário {etapa_id: minutos} para um produto"""
        query = """
            SELECT e.id as etapa_id, e.nome as etapa_nome, e.ordem,
                   COALESCE(pt.tempo_padrao_minutos, 0) as tempo_padrao,
                   COALESCE(pt.tempo_medio_historico, 0) as tempo_historico,
                   COALESCE(pt.ajuste_manual, 0) as ajuste_manual
            FROM producao_etapas e
            LEFT JOIN produtos_tempo_etapa pt ON pt.etapa_id = e.id AND pt.produto_id = %s
            WHERE e.ativo = 1
            ORDER BY e.ordem
        """
        results = self.db.fetch_all(query, [produto_id]) or []
        
        tempos = {}
        for r in results:
            if r['ajuste_manual'] and r['tempo_padrao'] > 0:
                tempo = r['tempo_padrao']
            elif r['tempo_historico'] > 0:
                tempo = r['tempo_historico']
            else:
                tempo = 30  # Default
            
            tempos[r['etapa_id']] = {
                'minutos': tempo,
                'nome': r['etapa_nome'],
                'ordem': r['ordem']
            }
        
        return tempos
    
    def get_tempo_total_produto(self, produto_id: int) -> int:
        """Retorna tempo total estimado para produzir um produto (todas etapas)"""
        tempos = self.get_tempos_todas_etapas_produto(produto_id)
        return sum(t['minutos'] for t in tempos.values())
    
    # =========================================================
    # FILA DE PRODUÇÃO
    # =========================================================
    
    def get_fila_etapa(self, etapa_id: int) -> list:
        """Retorna lotes na fila de uma etapa, ordenados por prioridade"""
        query = """
            SELECT l.id as lote_id, l.op_id, l.numero_lote, l.quantidade,
                   l.prioridade, l.data_chegada_etapa, l.status_operador,
                   op.produto_id, p.name as produto_nome,
                   TIMESTAMPDIFF(MINUTE, l.data_chegada_etapa, NOW()) as minutos_na_fila
            FROM op_lotes l
            JOIN ordens_producao op ON l.op_id = op.id
            JOIN products p ON op.produto_id = p.id
            WHERE l.etapa_atual_id = %s
              AND l.status NOT IN ('concluido', 'cancelado')
            ORDER BY l.prioridade DESC, l.data_chegada_etapa ASC
        """
        return self.db.fetch_all(query, [etapa_id]) or []
    
    def get_posicao_na_fila(self, lote_id: int) -> dict:
        """Retorna posição do lote na fila da etapa atual"""
        # Primeiro, pegar a etapa atual do lote
        query = "SELECT etapa_atual_id, prioridade, data_chegada_etapa FROM op_lotes WHERE id = %s"
        lote = self.db.fetch_one(query, [lote_id])
        
        if not lote:
            return {'posicao': 0, 'lotes_na_frente': 0, 'tempo_estimado_espera': 0}
        
        # Contar quantos estão na frente
        query = """
            SELECT COUNT(*) as cnt FROM op_lotes
            WHERE etapa_atual_id = %s
              AND status NOT IN ('concluido', 'cancelado')
              AND (
                  prioridade > %s 
                  OR (prioridade = %s AND data_chegada_etapa < %s)
              )
        """
        result = self.db.fetch_one(query, [
            lote['etapa_atual_id'], 
            lote['prioridade'], 
            lote['prioridade'],
            lote['data_chegada_etapa']
        ])
        
        posicao = (result['cnt'] if result else 0) + 1
        
        return {
            'posicao': posicao,
            'lotes_na_frente': posicao - 1,
            'etapa_id': lote['etapa_atual_id']
        }
    
    def get_tempo_fila_estimado(self, lote_id: int, produto_id: int) -> int:
        """
        Estima tempo de espera na fila (minutos)
        Considera tempo médio de cada lote na frente
        """
        pos = self.get_posicao_na_fila(lote_id)
        if pos['lotes_na_frente'] == 0:
            return 0
        
        # Pegar tempo médio da etapa
        tempo_por_lote = self.get_tempo_produto_etapa(produto_id, pos['etapa_id'])
        
        # Multiplicar pelo número de lotes na frente
        return pos['lotes_na_frente'] * tempo_por_lote
    
    # =========================================================
    # CÁLCULO DE PREVISÃO
    # =========================================================
    
    def calcular_tempo_restante_lote(self, lote_id: int) -> dict:
        """
        Calcula tempo restante para conclusão de um lote
        Retorna: {tempo_restante_minutos, etapas_restantes, detalhes}
        """
        # Buscar dados do lote
        query = """
            SELECT l.id, l.etapa_atual_id, l.status_operador, l.inicio_producao,
                   op.produto_id, e.ordem as etapa_ordem
            FROM op_lotes l
            JOIN ordens_producao op ON l.op_id = op.id
            JOIN producao_etapas e ON l.etapa_atual_id = e.id
            WHERE l.id = %s
        """
        lote = self.db.fetch_one(query, [lote_id])
        
        if not lote:
            return {'tempo_restante_minutos': 0, 'etapas_restantes': 0, 'detalhes': []}
        
        # Buscar etapas restantes (incluindo atual)
        query = """
            SELECT id, nome, ordem FROM producao_etapas
            WHERE ativo = 1 AND ordem >= %s
            ORDER BY ordem
        """
        etapas = self.db.fetch_all(query, [lote['etapa_ordem']]) or []
        
        tempo_total = 0
        detalhes = []
        
        for i, etapa in enumerate(etapas):
            tempo_etapa = self.get_tempo_produto_etapa(lote['produto_id'], etapa['id'])
            
            # Se for etapa atual e já está em produção, descontar tempo já gasto
            if i == 0 and lote['status_operador'] == 'em_producao' and lote['inicio_producao']:
                tempo_gasto = (datetime.now() - lote['inicio_producao']).total_seconds() / 60
                tempo_etapa = max(0, tempo_etapa - tempo_gasto)
            
            tempo_total += tempo_etapa
            detalhes.append({
                'etapa_id': etapa['id'],
                'etapa_nome': etapa['nome'],
                'tempo_minutos': tempo_etapa
            })
        
        return {
            'tempo_restante_minutos': int(tempo_total),
            'etapas_restantes': len(etapas),
            'detalhes': detalhes
        }
    
    def calcular_previsao_lote(self, lote_id: int, empresa_id: int = None) -> dict:
        """
        Calcula data/hora prevista de conclusão de um lote
        Considera: tempo restante + fila + jornada de trabalho
        """
        # Buscar dados do lote
        query = """
            SELECT l.id, l.etapa_atual_id, op.produto_id
            FROM op_lotes l
            JOIN ordens_producao op ON l.op_id = op.id
            WHERE l.id = %s
        """
        lote = self.db.fetch_one(query, [lote_id])
        
        if not lote:
            return {'previsao': None, 'erro': 'Lote não encontrado'}
        
        # Calcular tempo restante de produção
        tempo_restante = self.calcular_tempo_restante_lote(lote_id)
        
        # Calcular tempo de espera na fila
        tempo_fila = self.get_tempo_fila_estimado(lote_id, lote['produto_id'])
        
        # Tempo total em minutos
        tempo_total = tempo_restante['tempo_restante_minutos'] + tempo_fila
        
        # Converter minutos em data/hora considerando jornada
        previsao = self.adicionar_minutos_uteis(datetime.now(), tempo_total, empresa_id)
        
        return {
            'previsao': previsao,
            'tempo_producao_minutos': tempo_restante['tempo_restante_minutos'],
            'tempo_fila_minutos': tempo_fila,
            'tempo_total_minutos': tempo_total,
            'detalhes': tempo_restante['detalhes']
        }
    
    def calcular_previsao_op(self, op_id: int, empresa_id: int = None) -> dict:
        """
        Calcula previsão de conclusão de uma OP
        Considera o lote mais demorado
        """
        # Buscar todos os lotes da OP
        query = """
            SELECT id FROM op_lotes 
            WHERE op_id = %s AND status NOT IN ('concluido', 'cancelado')
        """
        lotes = self.db.fetch_all(query, [op_id]) or []
        
        if not lotes:
            return {'previsao': None, 'mensagem': 'Nenhum lote pendente'}
        
        # Calcular previsão de cada lote
        previsoes = []
        for lote in lotes:
            prev = self.calcular_previsao_lote(lote['id'], empresa_id)
            if prev['previsao']:
                previsoes.append(prev)
        
        if not previsoes:
            return {'previsao': None, 'mensagem': 'Não foi possível calcular'}
        
        # Pegar a maior previsão (último lote a terminar)
        maior_previsao = max(previsoes, key=lambda x: x['previsao'])
        
        return {
            'previsao': maior_previsao['previsao'],
            'qtd_lotes': len(lotes),
            'tempo_total_minutos': maior_previsao['tempo_total_minutos'],
            'lotes_previsoes': previsoes
        }
    
    def adicionar_minutos_uteis(self, data_inicio: datetime, minutos: int, empresa_id: int = None) -> datetime:
        """
        Adiciona minutos úteis a uma data/hora
        Considera jornada de trabalho e feriados
        """
        if minutos <= 0:
            return data_inicio
        
        data_atual = data_inicio
        minutos_restantes = minutos
        
        # Limite de segurança: máximo 365 dias
        max_iteracoes = 365
        iteracao = 0
        
        while minutos_restantes > 0 and iteracao < max_iteracoes:
            iteracao += 1
            
            # Verificar se é dia útil
            if not self.is_dia_util(data_atual.date(), empresa_id):
                data_atual = datetime.combine(data_atual.date() + timedelta(days=1), time(8, 0))
                continue
            
            # Pegar minutos úteis restantes no dia
            dia_semana = (data_atual.weekday() + 1) % 7
            minutos_dia = self.get_minutos_uteis_dia(dia_semana, empresa_id)
            
            # Calcular minutos já gastos no dia
            jornadas = self.get_jornada_dia(dia_semana, empresa_id)
            if jornadas:
                j = jornadas[0]  # Primeiro turno
                hora_inicio = j['hora_inicio']
                
                if isinstance(hora_inicio, timedelta):
                    hora_inicio_dt = (datetime.min + hora_inicio).time()
                else:
                    hora_inicio_dt = hora_inicio
                
                inicio_dia = datetime.combine(data_atual.date(), hora_inicio_dt)
                
                if data_atual < inicio_dia:
                    data_atual = inicio_dia
                
                # Minutos restantes no dia
                minutos_restantes_dia = minutos_dia
            else:
                data_atual = datetime.combine(data_atual.date() + timedelta(days=1), time(8, 0))
                continue
            
            if minutos_restantes <= minutos_restantes_dia:
                # Termina hoje
                data_atual += timedelta(minutes=minutos_restantes)
                minutos_restantes = 0
            else:
                # Continua amanhã
                minutos_restantes -= minutos_restantes_dia
                data_atual = datetime.combine(data_atual.date() + timedelta(days=1), time(8, 0))
        
        return data_atual
    
    # =========================================================
    # PREVISÃO PARA ORÇAMENTO
    # =========================================================
    
    def calcular_previsao_orcamento(self, orcamento_id: int, empresa_id: int = None) -> dict:
        """
        Calcula previsão de produção para um orçamento
        Considera todos os itens e a fila atual
        """
        # Buscar itens do orçamento
        query = """
            SELECT oi.produto_id, oi.quantidade, p.name as produto_nome
            FROM orcamento_itens oi
            JOIN products p ON oi.produto_id = p.id
            WHERE oi.orcamento_id = %s
        """
        itens = self.db.fetch_all(query, [orcamento_id]) or []
        
        if not itens:
            return {'previsao_producao': None, 'mensagem': 'Orçamento sem itens'}
        
        # Calcular tempo total necessário
        tempo_total = 0
        detalhes_itens = []
        
        for item in itens:
            tempo_produto = self.get_tempo_total_produto(item['produto_id'])
            tempo_item = tempo_produto * item['quantidade']
            tempo_total += tempo_item
            
            detalhes_itens.append({
                'produto_id': item['produto_id'],
                'produto_nome': item['produto_nome'],
                'quantidade': item['quantidade'],
                'tempo_unitario_minutos': tempo_produto,
                'tempo_total_minutos': tempo_item
            })
        
        # Estimar tempo de fila (simplificado: usar fila média das etapas)
        query = "SELECT AVG(qtd_aguardando) as media_fila FROM vw_resumo_etapas_producao"
        result = self.db.fetch_one(query)
        fila_media = result['media_fila'] if result and result['media_fila'] else 0
        tempo_fila = int(fila_media * 30)  # 30 min por lote na fila
        
        # Tempo total com fila
        tempo_total_com_fila = tempo_total + tempo_fila
        
        # Calcular data de conclusão
        previsao_producao = self.adicionar_minutos_uteis(datetime.now(), tempo_total_com_fila, empresa_id)
        
        return {
            'previsao_producao': previsao_producao.date() if previsao_producao else None,
            'tempo_producao_minutos': tempo_total,
            'tempo_fila_minutos': tempo_fila,
            'tempo_total_minutos': tempo_total_com_fila,
            'detalhes_itens': detalhes_itens
        }
    
    # =========================================================
    # ANÁLISE DE GARGALOS
    # =========================================================
    
    def get_analise_gargalos(self) -> list:
        """Retorna análise de gargalos por etapa"""
        query = """
            SELECT * FROM vw_resumo_etapas_producao
            ORDER BY 
                CASE status_gargalo 
                    WHEN 'critico' THEN 1 
                    WHEN 'atencao' THEN 2 
                    ELSE 3 
                END,
                ordem
        """
        return self.db.fetch_all(query) or []
    
    def get_previsao_escoamento_fila(self, etapa_id: int, empresa_id: int = None) -> dict:
        """Calcula quando a fila de uma etapa será escoada"""
        # Buscar fila atual
        fila = self.get_fila_etapa(etapa_id)
        
        if not fila:
            return {'previsao': datetime.now(), 'tempo_minutos': 0, 'qtd_lotes': 0}
        
        # Calcular tempo total
        tempo_total = 0
        for lote in fila:
            tempo = self.get_tempo_produto_etapa(lote['produto_id'], etapa_id)
            tempo_total += tempo
        
        # Calcular data de escoamento
        previsao = self.adicionar_minutos_uteis(datetime.now(), tempo_total, empresa_id)
        
        return {
            'previsao': previsao,
            'tempo_minutos': tempo_total,
            'qtd_lotes': len(fila)
        }


# Instância singleton para uso em rotas
_service_instance = None

def get_previsao_service() -> PrevisaoProducaoService:
    global _service_instance
    if _service_instance is None:
        _service_instance = PrevisaoProducaoService()
    return _service_instance
