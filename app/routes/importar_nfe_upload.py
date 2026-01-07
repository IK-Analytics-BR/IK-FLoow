"""
ROTAS FLASK PARA IMPORTAÇÃO DE NFe COM UPLOAD
- Upload de múltiplos arquivos XML
- Importação incremental
- Descarte automático após processar
- Ideal para produção na AWS
"""

from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
import threading
import time
import uuid
from datetime import datetime

# Importar scripts de importação
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.scripts.importar_nfe_entrada_incremental_v2 import importar_xml_files as importar_entrada
from app.scripts.importar_nfe_saida_incremental import importar_xml_files as importar_saida

# Blueprint
nfe_upload_bp = Blueprint('nfe_upload', __name__)

# Armazenamento global de progresso (não usar session em thread)
# Chave: session_id, Valor: dict com progresso
import threading as th
_progresso_lock = th.Lock()
_progresso_global = {}

# Configurações
ALLOWED_EXTENSIONS = {'xml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB por arquivo


def allowed_file(filename):
    """Verifica se arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@nfe_upload_bp.route('/importar-nfe-upload')
def importar_nfe_upload_page():
    """Página de importação com upload"""
    return render_template('importar_nfe_upload.html')


@nfe_upload_bp.route('/importar-nfe-upload/entrada', methods=['POST'])
def importar_nfe_entrada_upload():
    """
    Importa NFe de ENTRADA (Compras) via upload
    - Recebe múltiplos arquivos XML
    - Processa incrementalmente
    - Descarta arquivos após processamento
    """
    
    try:
        # Verificar se há arquivos
        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        files = request.files.getlist('files[]')
        
        if not files or files[0].filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp(prefix='nfe_entrada_upload_')
        
        try:
            arquivos_xml = []
            arquivos_invalidos = []
            
            # Salvar arquivos temporariamente
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(temp_dir, filename)
                    file.save(filepath)
                    arquivos_xml.append(filepath)
                else:
                    arquivos_invalidos.append(file.filename)
            
            if not arquivos_xml:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum arquivo XML válido encontrado'
                }), 400
            
            # Importar XMLs
            stats = importar_entrada(arquivos_xml)
            
            # Remover diretório temporário
            shutil.rmtree(temp_dir)
            
            return jsonify({
                'success': True,
                'message': 'Importação concluída com sucesso',
                'stats': {
                    'total': stats['total'],
                    'sucesso': stats['sucesso'],
                    'duplicados': stats['duplicados'],
                    'erros': stats['erros'],
                    'arquivos_invalidos': arquivos_invalidos,
                    'erros_detalhes': stats['erros_detalhes'][:10]  # Apenas 10 primeiros
                }
            })
            
        except Exception as e:
            # Limpar diretório temporário em caso de erro
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar arquivos: {str(e)}'
        }), 500


@nfe_upload_bp.route('/importar-nfe-upload/saida', methods=['POST'])
def importar_nfe_saida_upload():
    """
    Importa NFe de SAÍDA (Vendas) via upload
    - Recebe múltiplos arquivos XML
    - Processa incrementalmente
    - Descarta arquivos após processamento
    """
    
    try:
        # Verificar se há arquivos
        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        files = request.files.getlist('files[]')
        
        if not files or files[0].filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp(prefix='nfe_saida_upload_')
        
        try:
            arquivos_xml = []
            arquivos_invalidos = []
            
            # Salvar arquivos temporariamente
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(temp_dir, filename)
                    file.save(filepath)
                    arquivos_xml.append(filepath)
                else:
                    arquivos_invalidos.append(file.filename)
            
            if not arquivos_xml:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum arquivo XML válido encontrado'
                }), 400
            
            # Importar XMLs
            stats = importar_saida(arquivos_xml)
            
            # Remover diretório temporário
            shutil.rmtree(temp_dir)
            
            return jsonify({
                'success': True,
                'message': 'Importação concluída com sucesso',
                'stats': {
                    'total': stats['total'],
                    'sucesso': stats['sucesso'],
                    'duplicados': stats['duplicados'],
                    'erros': stats['erros'],
                    'arquivos_invalidos': arquivos_invalidos,
                    'erros_detalhes': stats['erros_detalhes'][:10]  # Apenas 10 primeiros
                }
            })
            
        except Exception as e:
            # Limpar diretório temporário em caso de erro
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar arquivos: {str(e)}'
        }), 500


@nfe_upload_bp.route('/importar-nfe-upload/buscar-pasta', methods=['POST'])
def buscar_xmls_pasta():
    """
    Busca XMLs em uma pasta do servidor (recursivamente em todas as subpastas)
    - Usado para importação em lote de pasta local
    - Busca automática em subpastas
    """
    try:
        data = request.json
        pasta = data.get('pasta', '')
        tipo = data.get('tipo', 'entrada')  # 'entrada' ou 'saida'
        
        if not pasta:
            return jsonify({
                'success': False,
                'message': 'Pasta não informada'
            }), 400
        
        if not os.path.exists(pasta):
            return jsonify({
                'success': False,
                'message': 'Pasta não encontrada no servidor'
            }), 404
        
        if not os.path.isdir(pasta):
            return jsonify({
                'success': False,
                'message': 'Caminho informado não é uma pasta'
            }), 400
        
        # Buscar XMLs RECURSIVAMENTE em todas as subpastas
        xml_files = []
        pastas_encontradas = {}
        
        for root, dirs, files in os.walk(pasta):
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(root, file)
                    xml_files.append(xml_path)
                    
                    # Contar por subpasta
                    rel_path = os.path.relpath(root, pasta)
                    if rel_path == '.':
                        rel_path = 'Pasta raiz'
                    
                    if rel_path not in pastas_encontradas:
                        pastas_encontradas[rel_path] = 0
                    pastas_encontradas[rel_path] += 1
        
        return jsonify({
            'success': True,
            'total': len(xml_files),
            'pastas': pastas_encontradas,
            'tipo': tipo
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar XMLs: {str(e)}'
        }), 500


@nfe_upload_bp.route('/importar-nfe-upload/limpar-dados', methods=['POST'])
def limpar_dados_nfe():
    """
    Limpa dados de NFe anteriores
    - NFe Entrada: staging, fornecedores, produtos, pedidos, estoque
    - NFe Saída: vendas
    """
    try:
        from database import get_db
        
        data = request.json
        tipo = data.get('tipo', 'entrada')
        
        db = get_db()
        registros_apagados = {}
        
        if tipo == 'entrada':
            # Limpar NFe de Entrada (ORDEM IMPORTANTE - respeitar foreign keys)
            
            # 1. Movimentos de estoque de pedidos NFe
            try:
                db.execute("""
                    DELETE sm FROM stock_movements sm
                    INNER JOIN purchase_orders po ON sm.reference_id = po.id AND sm.reference_type = 'purchase_order'
                    WHERE po.nfe_entrada_staging_id IS NOT NULL
                """)
                registros_apagados['movimentos_estoque'] = db.connection.cursor().rowcount
            except Exception as e:
                registros_apagados['movimentos_estoque'] = f'Erro: {str(e)}'
            
            # 2. Itens dos pedidos (ANTES de apagar os pedidos - foreign key!)
            try:
                db.execute("""
                    DELETE poi FROM purchase_order_items poi
                    INNER JOIN purchase_orders po ON poi.purchase_order_id = po.id
                    WHERE po.nfe_entrada_staging_id IS NOT NULL
                """)
                registros_apagados['itens_pedidos'] = db.connection.cursor().rowcount
            except Exception as e:
                registros_apagados['itens_pedidos'] = f'Erro: {str(e)}'
            
            # 3. Pedidos de compra vinculados a NFe (DEPOIS dos itens)
            try:
                result = db.execute("DELETE FROM purchase_orders WHERE nfe_entrada_staging_id IS NOT NULL")
                registros_apagados['pedidos_compra'] = result
            except Exception as e:
                registros_apagados['pedidos_compra'] = f'Erro: {str(e)}'
            
            # 4. Produtos criados hoje (categoria 3 = matéria prima)
            try:
                result = db.execute("DELETE FROM products WHERE category_id = 3 AND DATE(created_at) = CURDATE()")
                registros_apagados['produtos'] = result
            except Exception as e:
                registros_apagados['produtos'] = f'Erro: {str(e)}'
            
            # 5. Fornecedores criados hoje
            try:
                result = db.execute("DELETE FROM suppliers WHERE DATE(created_at) = CURDATE()")
                registros_apagados['fornecedores'] = result
            except Exception as e:
                registros_apagados['fornecedores'] = f'Erro: {str(e)}'
            
            # 6. Staging itens
            try:
                result = db.execute("DELETE FROM nfe_entrada_staging_itens")
                registros_apagados['staging_itens'] = result
            except Exception as e:
                registros_apagados['staging_itens'] = f'Erro: {str(e)}'
            
            # 7. Staging notas
            try:
                result = db.execute("DELETE FROM nfe_entrada_staging_notas")
                registros_apagados['staging_notas'] = result
            except Exception as e:
                registros_apagados['staging_notas'] = f'Erro: {str(e)}'
            
            # 8. Log de importação
            try:
                result = db.execute("DELETE FROM nfe_entrada_import_log")
                registros_apagados['import_log'] = result
            except Exception as e:
                registros_apagados['import_log'] = f'Erro: {str(e)}'
            
        else:
            # Limpar NFe de Saída
            # 1. Itens de venda
            try:
                db.execute("""
                    DELETE si FROM sale_items si
                    INNER JOIN sales s ON si.sale_id = s.id
                    WHERE s.chave_acesso_nfe IS NOT NULL
                """)
                registros_apagados['itens_venda'] = db.connection.cursor().rowcount
            except Exception as e:
                registros_apagados['itens_venda'] = f'Erro: {str(e)}'
            
            # 2. Vendas com NFe
            try:
                result = db.execute("DELETE FROM sales WHERE chave_acesso_nfe IS NOT NULL")
                registros_apagados['vendas'] = result
            except Exception as e:
                registros_apagados['vendas'] = f'Erro: {str(e)}'
            
            # 3. Staging (se existir)
            try:
                result = db.execute("DELETE FROM nfe_staging_notas")
                registros_apagados['staging_notas'] = result
            except Exception as e:
                registros_apagados['staging_notas'] = f'Erro: {str(e)}'
        
        return jsonify({
            'success': True,
            'message': f'Dados de NFe de {tipo} limpos com sucesso',
            'registros_apagados': registros_apagados
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao limpar dados: {str(e)}'
        }), 500


@nfe_upload_bp.route('/importar-nfe-upload/processar-pasta', methods=['POST'])
def processar_pasta():
    """
    Inicia processamento em BACKGROUND com progresso em tempo real
    - Cria thread para processar XMLs
    - Armazena progresso na sessão
    - Frontend consulta progresso via /progresso
    """
    try:
        data = request.json
        pasta = data.get('pasta', '')
        tipo = data.get('tipo', 'entrada')
        limpar_antes = data.get('limpar_antes', False)
        
        if not pasta or not os.path.exists(pasta):
            return jsonify({
                'success': False,
                'message': 'Pasta não encontrada'
            }), 400
        
        # Buscar TODOS os XMLs recursivamente (IGNORANDO EVENTOS)
        xml_files = []
        xml_eventos_ignorados = []
        
        for root, dirs, files in os.walk(pasta):
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(root, file)
                    
                    # FILTRAR XMLs de eventos/cancelamentos
                    nome_lower = file.lower()
                    if any(palavra in nome_lower for palavra in [
                        'evento', 'canc', 'inut', 'proceventonfe', 
                        'retevento', 'retcanc', 'retinut', '_01-'
                    ]):
                        xml_eventos_ignorados.append(xml_path)
                        continue
                    
                    xml_files.append(xml_path)
        
        print(f"📊 XMLs encontrados: {len(xml_files)} válidos, {len(xml_eventos_ignorados)} eventos ignorados")
        
        if not xml_files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo XML encontrado'
            }), 400
        
        # Obter session_id para armazenar progresso
        from flask import session as flask_session
        if 'session_id' not in flask_session:
            flask_session['session_id'] = str(uuid.uuid4())
        session_id = flask_session['session_id']
        
        # Inicializar progresso no dicionário global
        with _progresso_lock:
            _progresso_global[session_id] = {
                'status': 'processando',
                'tipo': tipo,
                'total': len(xml_files),
                'processados': 0,
                'sucesso': 0,
                'duplicados': 0,
                'erros': 0,
                'clientes_novos': 0,
                'clientes_existentes': 0,
                'fornecedores_novos': 0,
                'produtos_novos': 0,
                'produtos_existentes': 0,
                'vendas_criadas': 0,
                'pedidos_criados': 0,
                'percentual': 0,
                'arquivo_atual': '',
                'logs': [],
                'inicio': datetime.now().isoformat(),
                'erros_detalhes': []
            }
        
        # Obter instância do Flask app
        from flask import current_app as app
        flask_app = app._get_current_object()
        
        # Iniciar thread de processamento
        thread = threading.Thread(
            target=processar_pasta_background,
            args=(flask_app, session_id, pasta, tipo, limpar_antes, xml_files)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Processamento iniciado! {len(xml_files)} arquivos encontrados.',
            'total': len(xml_files)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao iniciar processamento: {str(e)}'
        }), 500


def processar_pasta_background(flask_app, session_id, pasta, tipo, limpar_antes, xml_files):
    """
    Função executada em background para processar XMLs EM LOTES
    Evita travamentos fechando conexão a cada lote
    """
    print(f"\n[PROGRESSO] Thread iniciada! Session: {session_id}, Tipo: {tipo}, Total: {len(xml_files)}")
    
    with flask_app.app_context():
        try:
            from database import get_db
            
            # Limpar dados anteriores se solicitado
            if limpar_antes:
                _limpar_dados_anteriores(tipo)
            
            # CONFIGURAR PROCESSAMENTO EM LOTES
            TAMANHO_LOTE = 100  # 100 XMLs por lote (mais eficiente para grandes volumes)
            total_arquivos = len(xml_files)
            
            # Dividir em lotes
            lotes = []
            for i in range(0, total_arquivos, TAMANHO_LOTE):
                lote = xml_files[i:i + TAMANHO_LOTE]
                lotes.append(lote)
            
            print(f"[PACOTE] Processando {total_arquivos} arquivos em {len(lotes)} lotes de {TAMANHO_LOTE}")
            
            # Processar cada lote
            arquivos_processados = 0
            ultimo_progresso = 0
            
            for lote_num, lote_arquivos in enumerate(lotes, 1):
                print(f"\n{'='*50}")
                print(f"[PACOTE] LOTE {lote_num}/{len(lotes)} ({len(lote_arquivos)} arquivos)")
                print(f"{'='*50}")
                
                # Conexão gerenciada automaticamente pelo sistema de retry
                
                # Processar arquivos do lote
                for i, xml_file in enumerate(lote_arquivos):
                    nome_arquivo = os.path.basename(xml_file)
                    arquivos_processados += 1
                    
                    # Atualizar progresso
                    with _progresso_lock:
                        if session_id in _progresso_global:
                            _progresso_global[session_id]['processados'] = arquivos_processados
                            _progresso_global[session_id]['percentual'] = int((arquivos_processados / total_arquivos) * 100)
                            _progresso_global[session_id]['arquivo_atual'] = f"Lote {lote_num}: {nome_arquivo}"
                    
                    # Sistema de retry automático gerencia a conexão
                    
                    try:
                        # Processar arquivo
                        # Processar arquivo
                        if tipo == 'entrada':
                            resultado = _processar_xml_entrada(xml_file)
                        else:
                            resultado = _processar_xml_saida(xml_file)
                        
                        # Log apenas a cada 50 arquivos para não travar
                        if arquivos_processados % 50 == 0:
                            print(f"[{arquivos_processados}/{total_arquivos}] Processados: {resultado['status']}")
                        
                        # Atualizar estatísticas
                        if resultado:
                            with _progresso_lock:
                                if session_id in _progresso_global:
                                    prog = _progresso_global[session_id]
                                    if resultado['status'] == 'sucesso':
                                        prog['sucesso'] += 1
                                        # Acumular contadores para SAÍDA
                                        if tipo == 'saida':
                                            prog['clientes_novos'] += resultado.get('cliente_novo', 0)
                                            prog['clientes_existentes'] += resultado.get('clientes_existentes', 0)
                                            prog['vendas_criadas'] += resultado.get('venda_criada', 0)
                                        # Acumular contadores para ENTRADA
                                        else:
                                            prog['fornecedores_novos'] += resultado.get('fornecedor_novo', 0)
                                            prog['pedidos_criados'] += resultado.get('pedido_criado', 0)
                                        # Contadores comuns
                                        prog['produtos_novos'] += resultado.get('produtos_novos', 0)
                                        prog['produtos_existentes'] += resultado.get('produtos_existentes', 0)
                                        prog['duplicados'] += resultado.get('duplicados', 0)
                                    elif resultado['status'] == 'duplicado':
                                        prog['duplicados'] += resultado.get('duplicados', 1)
                                    else:
                                        prog['erros'] += 1
                                        if len(prog['erros_detalhes']) < 10:
                                            prog['erros_detalhes'].append(resultado.get('erro', 'Erro desconhecido')[:200])
                        
                    except Exception as e_proc:
                        print(f"[{arquivos_processados}/{total_arquivos}] {nome_arquivo}: ERRO - {str(e_proc)[:100]}")
                        
                        with _progresso_lock:
                            if session_id in _progresso_global:
                                _progresso_global[session_id]['erros'] += 1
                                if len(_progresso_global[session_id]['erros_detalhes']) < 10:
                                    _progresso_global[session_id]['erros_detalhes'].append(str(e_proc)[:200])
                
                # Limpeza rápida de memória
                if lote_num % 10 == 0:  # Apenas a cada 10 lotes
                    import gc
                    gc.collect()
            
            # Finalizar processamento
            with _progresso_lock:
                if session_id in _progresso_global:
                    _progresso_global[session_id]['status'] = 'concluido'
                    _progresso_global[session_id]['fim'] = datetime.now().isoformat()
            
            print(f"\n🎉 PROCESSAMENTO COMPLETO!")
            print(f"[PACOTE] {len(lotes)} lotes processados com sucesso")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            with _progresso_lock:
                if session_id in _progresso_global:
                    _progresso_global[session_id]['status'] = 'erro'
                    _progresso_global[session_id]['erro_geral'] = str(e)


def _limpar_dados_anteriores(tipo):
    """Limpa dados anteriores antes da importação"""
    from database import get_db
    db = get_db()
    
    if tipo == 'entrada':
        # Limpar NFe de Entrada
        try:
            db.execute("""
                DELETE sm FROM stock_movements sm
                INNER JOIN purchase_orders po ON sm.reference_id = po.id AND sm.reference_type = 'purchase_order'
                WHERE po.nfe_entrada_staging_id IS NOT NULL
            """)
        except:
            pass
        
        try:
            db.execute("""
                DELETE poi FROM purchase_order_items poi
                INNER JOIN purchase_orders po ON poi.purchase_order_id = po.id
                WHERE po.nfe_entrada_staging_id IS NOT NULL
            """)
        except:
            pass
        
        try:
            db.execute("DELETE FROM purchase_orders WHERE nfe_entrada_staging_id IS NOT NULL")
        except:
            pass
        
        try:
            db.execute("DELETE FROM products WHERE category_id = 3 AND DATE(created_at) = CURDATE()")
        except:
            pass
        
        try:
            db.execute("DELETE FROM suppliers WHERE DATE(created_at) = CURDATE()")
        except:
            pass
        
        try:
            db.execute("DELETE FROM nfe_entrada_staging_itens")
        except:
            pass
        
        try:
            db.execute("DELETE FROM nfe_entrada_staging_notas")
        except:
            pass
    else:
        # Limpar NFe de Saída
        try:
            db.execute("""
                DELETE si FROM sale_items si
                INNER JOIN sales s ON si.sale_id = s.id
                WHERE s.chave_acesso_nfe IS NOT NULL
            """)
        except:
            pass
        
        try:
            db.execute("DELETE FROM sales WHERE chave_acesso_nfe IS NOT NULL")
        except:
            pass
        
        try:
            db.execute("DELETE FROM nfe_staging_itens")
        except:
            pass
        
        try:
            db.execute("DELETE FROM nfe_staging_notas")
        except:
            pass


def _processar_xml_entrada(xml_file):
    """Processa um XML de entrada e retorna resultado"""
    try:
        from app.scripts.importar_nfe_entrada_incremental_v2 import ImportadorNFeEntradaIncrementalV2
        
        # Classe cria sua própria conexão com get_db() internamente
        importador = ImportadorNFeEntradaIncrementalV2()
        sucesso = importador.importar_arquivo(xml_file)
        
        if sucesso:
            return {
                'status': 'sucesso',
                'fornecedor_novo': importador.fornecedores_novos,
                'fornecedores_existentes': importador.fornecedores_existentes,
                'produtos_novos': importador.produtos_novos,
                'produtos_existentes': importador.produtos_existentes,
                'pedido_criado': importador.pedidos_criados,
                'duplicados': 0
            }
        else:
            if importador.duplicados > 0:
                return {'status': 'duplicado', 'duplicados': importador.duplicados}
            else:
                return {'status': 'erro', 'erro': 'Falha ao importar'}
    except Exception as e:
        erro_str = str(e).lower()
        if 'duplicado' in erro_str or 'já existe' in erro_str or 'duplicate' in erro_str:
            return {'status': 'duplicado'}
        # XMLs de cancelamento não são erro, são ignorados
        if 'cancelamento' in erro_str or 'inutilização' in erro_str:
            return {'status': 'duplicado'}  # Tratar como duplicado (ignorar)
        return {'status': 'erro', 'erro': str(e)}


def _processar_xml_saida(xml_file):
    """Processa um XML de saída e retorna resultado com contadores"""
    try:
        from app.scripts.importar_nfe_saida_incremental import ImportadorNFeSaidaIncremental
        
        # Classe cria sua própria conexão com get_db() internamente
        importador = ImportadorNFeSaidaIncremental()
        
        # Processar arquivo
        sucesso = importador.importar_arquivo(xml_file)
        
        if sucesso:
            # Retornar incrementos por arquivo (sempre 1 para cada tipo quando sucesso)
            return {
                'status': 'sucesso',
                'cliente_novo': 1 if importador.clientes_novos > 0 else 0,
                'clientes_existentes': 1 if importador.clientes_existentes > 0 else 0,
                'produtos_novos': 1 if importador.produtos_novos > 0 else 0,
                'produtos_existentes': 1 if importador.produtos_existentes > 0 else 0,
                'venda_criada': 1,  # Sempre 1 venda por arquivo de sucesso
                'duplicados': 0     # Se sucesso, não é duplicado
            }
        else:
            # Se não teve sucesso, verificar se foi duplicado
            if importador.duplicados > 0:
                return {'status': 'duplicado', 'duplicados': importador.duplicados}
            else:
                return {'status': 'erro', 'erro': 'Falha ao importar'}
            
    except Exception as e:
        erro_str = str(e).lower()
        if 'duplicado' in erro_str or 'já existe' in erro_str or 'duplicate' in erro_str:
            return {'status': 'duplicado'}
        # XMLs de cancelamento não são erro, são ignorados
        if 'cancelamento' in erro_str or 'inutilização' in erro_str:
            return {'status': 'duplicado'}  # Tratar como duplicado (ignorar)
        return {'status': 'erro', 'erro': str(e)}


@nfe_upload_bp.route('/importar-nfe-upload/progresso')
def obter_progresso():
    """
    Retorna progresso da importação em tempo real
    Consultado pelo frontend a cada segundo
    """
    from flask import session as flask_session
    session_id = flask_session.get('session_id')
    
    if not session_id:
        return jsonify({
            'success': False,
            'message': 'Sessão não encontrada'
        })
    
    with _progresso_lock:
        progresso = _progresso_global.get(session_id, {})
    
    if not progresso:
        return jsonify({
            'success': False,
            'message': 'Nenhuma importação em andamento'
        })
    
    return jsonify({
        'success': True,
        'progresso': progresso
    })


@nfe_upload_bp.route('/importar-nfe-upload/processar-pasta-OLD', methods=['POST'])
def processar_pasta_OLD():
    """
    VERSÃO ANTIGA - Processa tudo de uma vez sem progresso
    Mantida para compatibilidade
    """
    try:
        data = request.json
        pasta = data.get('pasta', '')
        tipo = data.get('tipo', 'entrada')  # 'entrada' ou 'saida'
        limpar_antes = data.get('limpar_antes', False)  # Limpar dados antes de importar
        
        if not pasta or not os.path.exists(pasta):
            return jsonify({
                'success': False,
                'message': 'Pasta não encontrada'
            }), 400
        
        # Limpar dados anteriores se solicitado
        if limpar_antes:
            from database import get_db
            db = get_db()
            
            if tipo == 'entrada':
                # Limpar NFe de Entrada (ORDEM IMPORTANTE - respeitar foreign keys)
                
                # 1. Movimentos de estoque
                try:
                    db.execute("""
                        DELETE sm FROM stock_movements sm
                        INNER JOIN purchase_orders po ON sm.reference_id = po.id AND sm.reference_type = 'purchase_order'
                        WHERE po.nfe_entrada_staging_id IS NOT NULL
                    """)
                except:
                    pass
                
                # 2. Itens dos pedidos (ANTES de apagar pedidos - foreign key!)
                try:
                    db.execute("""
                        DELETE poi FROM purchase_order_items poi
                        INNER JOIN purchase_orders po ON poi.purchase_order_id = po.id
                        WHERE po.nfe_entrada_staging_id IS NOT NULL
                    """)
                except:
                    pass
                
                # 3. Pedidos de compra (DEPOIS dos itens)
                try:
                    db.execute("DELETE FROM purchase_orders WHERE nfe_entrada_staging_id IS NOT NULL")
                except:
                    pass
                
                # 4. Produtos criados hoje
                try:
                    db.execute("DELETE FROM products WHERE category_id = 3 AND DATE(created_at) = CURDATE()")
                except:
                    pass
                
                # 5. Fornecedores criados hoje
                try:
                    db.execute("DELETE FROM suppliers WHERE DATE(created_at) = CURDATE()")
                except:
                    pass
                
                # 6. Staging itens
                try:
                    db.execute("DELETE FROM nfe_entrada_staging_itens")
                except:
                    pass
                
                # 7. Staging notas
                try:
                    db.execute("DELETE FROM nfe_entrada_staging_notas")
                except:
                    pass
                
                # 8. Log de importação
                try:
                    db.execute("DELETE FROM nfe_entrada_import_log")
                except:
                    pass
            else:
                # Limpar NFe de Saída
                try:
                    db.execute("""
                        DELETE si FROM sale_items si
                        INNER JOIN sales s ON si.sale_id = s.id
                        WHERE s.chave_acesso_nfe IS NOT NULL
                    """)
                except:
                    pass
                
                try:
                    db.execute("DELETE FROM sales WHERE chave_acesso_nfe IS NOT NULL")
                except:
                    pass
                
                try:
                    db.execute("DELETE FROM nfe_staging_notas")
                except:
                    pass
        
        # Buscar TODOS os XMLs recursivamente (IGNORANDO EVENTOS)
        xml_files = []
        xml_eventos_ignorados = []
        
        for root, dirs, files in os.walk(pasta):
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(root, file)
                    
                    # FILTRAR XMLs de eventos/cancelamentos
                    nome_lower = file.lower()
                    if any(palavra in nome_lower for palavra in [
                        'evento', 'canc', 'inut', 'proceventonfe', 
                        'retevento', 'retcanc', 'retinut', '_01-'
                    ]):
                        xml_eventos_ignorados.append(xml_path)
                        continue
                    
                    xml_files.append(xml_path)
        
        print(f"📊 XMLs encontrados: {len(xml_files)} válidos, {len(xml_eventos_ignorados)} eventos ignorados")
        
        if not xml_files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo XML encontrado na pasta e subpastas'
            }), 400
        
        # Importar baseado no tipo
        if tipo == 'entrada':
            stats = importar_entrada(xml_files)
        else:
            stats = importar_saida(xml_files)
        
        return jsonify({
            'success': True,
            'message': f'{"Dados limpos e p" if limpar_antes else "P"}rocessados {len(xml_files)} arquivos de {len(set([os.path.dirname(f) for f in xml_files]))} pastas diferentes',
            'limpar_antes': limpar_antes,
            'stats': {
                'total': stats['total'],
                'sucesso': stats['sucesso'],
                'duplicados': stats['duplicados'],
                'erros': stats['erros'],
                'total_arquivos': len(xml_files),
                'erros_detalhes': stats['erros_detalhes'][:10]  # Apenas 10 primeiros
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar pasta: {str(e)}'
        }), 500


@nfe_upload_bp.route('/importar-nfe-upload/status')
def importar_nfe_status():
    """Retorna estatísticas de importação - APENAS do tipo selecionado"""
    
    from database import get_db
    db = get_db()
    
    try:
        # Pegar tipo do parâmetro GET (padrão: saida)
        tipo = request.args.get('tipo', 'saida')
        
        if tipo == 'entrada':
            # Estatísticas de NFe de Entrada
            entrada_stats = {
                'total_notas': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_staging_notas")['total'],
                'pendentes': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_staging_notas WHERE status_importacao = 'pendente'")['total'],
                'processadas': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_staging_notas WHERE status_importacao = 'processado'")['total'],
                'com_erro': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_staging_notas WHERE status_importacao = 'erro'")['total'],
            }
            
            return jsonify({
                'success': True,
                'tipo': 'entrada',
                'entrada': entrada_stats,
                'saida': {'total_vendas': 0, 'valor_total': 0}  # Placeholders vazios
            })
        else:
            # Estatísticas de NFe de Saída
            saida_stats = {
                'total_vendas': db.fetch_one("SELECT COUNT(*) as total FROM sales WHERE chave_acesso_nfe IS NOT NULL")['total'],
                'valor_total': db.fetch_one("SELECT SUM(net_total) as total FROM sales WHERE chave_acesso_nfe IS NOT NULL")['total'] or 0,
            }
            
            return jsonify({
                'success': True,
                'tipo': 'saida',
                'entrada': {'total_notas': 0, 'pendentes': 0, 'processadas': 0, 'com_erro': 0},  # Placeholders vazios
                'saida': saida_stats
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar estatísticas: {str(e)}'
        }), 500
