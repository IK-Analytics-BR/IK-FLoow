"""
Rotas para importação de XMLs de NF-e
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import get_db
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

importar_nfe = Blueprint('importar_nfe', __name__)


@importar_nfe.route('/importar-nfe')
def importar_nfe_form():
    """
    Página de importação de NF-e
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
                SUM(total_nota) as valor_total,
                COUNT(DISTINCT dest_cnpj_cpf) as clientes
            FROM nfe_staging_notas
            WHERE status_importacao = 'pendente'
        """),
        'eventos': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN tipo_evento = 'cancelamento' THEN 1 ELSE 0 END) as cancelamentos,
                SUM(CASE WHEN tipo_evento = 'inutilizacao' THEN 1 ELSE 0 END) as inutilizacoes,
                SUM(CASE WHEN tipo_evento = 'carta_correcao' THEN 1 ELSE 0 END) as cartas_correcao
            FROM nfe_eventos
        """),
        'log': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucesso,
                SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros,
                SUM(CASE WHEN status = 'duplicado' THEN 1 ELSE 0 END) as duplicados
            FROM nfe_import_log
        """)
    }
    
    # Últimas importações
    ultimas_importacoes = db.fetch_all("""
        SELECT 
            tipo_documento,
            status,
            COUNT(*) as quantidade,
            MAX(created_at) as ultima_data
        FROM nfe_import_log
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY tipo_documento, status
        ORDER BY ultima_data DESC
        LIMIT 10
    """)
    
    return render_template('importar_nfe.html',
                         stats=stats,
                         ultimas_importacoes=ultimas_importacoes)


@importar_nfe.route('/importar-nfe/buscar-xmls', methods=['POST'])
def buscar_xmls():
    """
    Busca e classifica XMLs em uma pasta
    """
    data = request.json
    pasta = data.get('pasta', '')
    
    if not pasta or not os.path.exists(pasta):
        return jsonify({'erro': 'Pasta não encontrada'}), 400
    
    # Buscar e classificar XMLs
    xml_files = []
    pastas_encontradas = {}
    tipos_encontrados = {
        'nfe_autorizada': 0,
        'nfe_cancelada': 0,
        'evento_cancelamento': 0,
        'inutilizacao': 0,
        'carta_correcao': 0,
        'outros': 0,
        'desconhecido': 0
    }
    
    try:
        # Importar classificador
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from utils.xml_classifier import classificar_xml
        
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
                    
                    # Classificar tipo (apenas para estatísticas)
                    # Fazemos isso para alguns arquivos para não demorar muito
                    if len(xml_files) <= 500 or len(xml_files) % 25 == 0:
                        try:
                            info = classificar_xml(xml_path)
                            tipo = info['tipo']
                            status = info.get('status')
                            
                            if tipo == 'nfe':
                                # Verificar status da NF-e
                                if status == 'cancelada':
                                    tipos_encontrados['nfe_cancelada'] += 1
                                else:
                                    tipos_encontrados['nfe_autorizada'] += 1
                            elif tipo == 'cancelamento':
                                tipos_encontrados['evento_cancelamento'] += 1
                            elif tipo == 'inutilizacao':
                                tipos_encontrados['inutilizacao'] += 1
                            elif tipo == 'carta_correcao':
                                tipos_encontrados['carta_correcao'] += 1
                            elif tipo == 'desconhecido':
                                tipos_encontrados['desconhecido'] += 1
                            else:
                                tipos_encontrados['outros'] += 1
                        except:
                            pass
        
        return jsonify({
            'total': len(xml_files),
            'pastas': pastas_encontradas,
            'tipos': tipos_encontrados
        })
    
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@importar_nfe.route('/importar-nfe/iniciar', methods=['POST'])
def iniciar_importacao():
    """
    Inicia processo de importação
    """
    data = request.json
    pasta = data.get('pasta', '')
    
    if not pasta or not os.path.exists(pasta):
        return jsonify({'erro': 'Pasta não encontrada'}), 400
    
    # Criar arquivo temporário com o caminho
    temp_file = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_import_path.txt')
    with open(temp_file, 'w') as f:
        f.write(pasta)
    
    # Executar importador em background
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'importar_xml_nfe_background.py')
    
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
    Executa importação em background
    """
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'importar_xml_nfe_background.py')
    python_exe = sys.executable
    
    subprocess.run([python_exe, script_path, pasta])


@importar_nfe.route('/importar-nfe/progresso')
def obter_progresso():
    """
    Obtém progresso da importação atual
    """
    # Ler arquivo de progresso (se existir)
    progress_file = os.path.join(os.path.dirname(__file__), '..', '..', 'import_progress.json')
    
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
        FROM nfe_import_log
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
    """)
    
    return jsonify({
        'status': 'concluido' if stats['ultima_importacao'] else 'aguardando',
        'total_processados': stats['total'] or 0,
        'sucesso': stats['sucesso'] or 0,
        'erros': stats['erros'] or 0,
        'duplicados': stats['duplicados'] or 0
    })


@importar_nfe.route('/importar-nfe/estatisticas')
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
                COUNT(DISTINCT dest_cnpj_cpf) as clientes
            FROM nfe_staging_notas
            WHERE status_importacao = 'pendente'
        """),
        'eventos': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN tipo_evento = 'cancelamento' THEN 1 ELSE 0 END) as cancelamentos,
                SUM(CASE WHEN tipo_evento = 'inutilizacao' THEN 1 ELSE 0 END) as inutilizacoes,
                SUM(CASE WHEN tipo_evento = 'carta_correcao' THEN 1 ELSE 0 END) as cartas_correcao
            FROM nfe_eventos
        """),
        'log_hoje': db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucesso,
                SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros
            FROM nfe_import_log
            WHERE DATE(created_at) = CURDATE()
        """)
    }
    
    return jsonify(stats)
