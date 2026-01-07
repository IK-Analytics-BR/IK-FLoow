"""
Rotas para importação de XMLs de NF-e de ENTRADA (Compras)
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import get_db
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

importar_nfe_entrada = Blueprint('importar_nfe_entrada', __name__)


@importar_nfe_entrada.route('/importar-nfe-entrada')
def importar_nfe_entrada_form():
    """
    Página de importação de NF-e de ENTRADA (Compras)
    """
    # Verificar se usuário está logado e é admin
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') != 'admin':
        return "Acesso negado", 403
    
    db = get_db()
    
    # Estatísticas atuais
    stats = {
        'nfe': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                COALESCE(SUM(total_nota), 0) as valor_total,
                COUNT(DISTINCT emit_cnpj) as fornecedores
            FROM nfe_entrada_staging_notas
            WHERE status_importacao = 'pendente'
        """),
        'log': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucesso,
                SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros,
                SUM(CASE WHEN status = 'duplicado' THEN 1 ELSE 0 END) as duplicados
            FROM nfe_entrada_import_log
        """)
    }
    
    # Últimas importações
    ultimas_importacoes = db.fetch_all("""
        SELECT 
            status,
            COUNT(*) as quantidade,
            MAX(created_at) as ultima_data
        FROM nfe_entrada_import_log
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY status
        ORDER BY ultima_data DESC
        LIMIT 10
    """)
    
    return render_template('importar_nfe_entrada.html',
                         stats=stats,
                         ultimas_importacoes=ultimas_importacoes)


@importar_nfe_entrada.route('/importar-nfe-entrada/buscar-xmls', methods=['POST'])
def buscar_xmls():
    """
    Busca XMLs de ENTRADA em uma pasta
    """
    data = request.json
    pasta = data.get('pasta', '')
    
    if not pasta or not os.path.exists(pasta):
        return jsonify({'erro': 'Pasta não encontrada'}), 400
    
    # Buscar XMLs
    xml_files = []
    pastas_encontradas = {}
    
    try:
        for root, dirs, files in os.walk(pasta):
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(root, file)
                    xml_files.append(xml_path)
                    
                    # Contar por subpasta
                    rel_path = os.path.relpath(root, pasta)
                    if rel_path not in pastas_encontradas:
                        pastas_encontradas[rel_path] = 0
                    pastas_encontradas[rel_path] += 1
        
        return jsonify({
            'total': len(xml_files),
            'pastas': pastas_encontradas
        })
    
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@importar_nfe_entrada.route('/importar-nfe-entrada/iniciar', methods=['POST'])
def iniciar_importacao():
    """
    Inicia processo de importação de NFe de ENTRADA
    """
    data = request.json
    pasta = data.get('pasta', '')
    
    if not pasta or not os.path.exists(pasta):
        return jsonify({'erro': 'Pasta não encontrada'}), 400
    
    # Criar arquivo temporário com o caminho
    temp_file = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_import_entrada_path.txt')
    with open(temp_file, 'w') as f:
        f.write(pasta)
    
    try:
        # Criar processo em background
        thread = threading.Thread(target=executar_importacao, args=(pasta,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'mensagem': 'Importação iniciada com sucesso',
            'status': 'processando'
        })
    
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


def executar_importacao(pasta):
    """
    Executa importação COMPLETA em background
    Importa XMLs + Processa (cria fornecedores, produtos, pedidos, estoque)
    """
    # CORRIGIDO: Usar script com correções aplicadas
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'importar_nfe_entrada_incremental_v2.py')
    python_exe = sys.executable
    
    subprocess.run([python_exe, script_path, pasta])


@importar_nfe_entrada.route('/importar-nfe-entrada/progresso')
def obter_progresso():
    """
    Obtém progresso da importação atual
    """
    # Ler arquivo de progresso (se existir)
    progress_file = os.path.join(os.path.dirname(__file__), '..', '..', 'import_entrada_progress.json')
    
    if os.path.exists(progress_file):
        try:
            import json
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            return jsonify(progress)
        except:
            pass
    
    # Se não houver arquivo, retornar estatísticas do banco
    db = get_db()
    
    # Contar últimas importações (últimos 5 minutos)
    stats = db.fetch_one("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucesso,
            SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros,
            SUM(CASE WHEN status = 'duplicado' THEN 1 ELSE 0 END) as duplicados,
            MAX(created_at) as ultima_importacao
        FROM nfe_entrada_import_log
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
    """)
    
    return jsonify({
        'status': 'concluido' if stats['ultima_importacao'] else 'aguardando',
        'total_processados': stats['total'] or 0,
        'sucesso': stats['sucesso'] or 0,
        'erros': stats['erros'] or 0,
        'duplicados': stats['duplicados'] or 0
    })


@importar_nfe_entrada.route('/importar-nfe-entrada/estatisticas')
def obter_estatisticas():
    """
    Obtém estatísticas atualizadas
    """
    db = get_db()
    
    stats = {
        'nfe': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(total_nota) as valor_total,
                COUNT(DISTINCT emit_cnpj) as fornecedores
            FROM nfe_entrada_staging_notas
            WHERE status_importacao = 'pendente'
        """),
        'log_hoje': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucesso,
                SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros
            FROM nfe_entrada_import_log
            WHERE DATE(created_at) = CURDATE()
        """)
    }
    
    return jsonify(stats)
