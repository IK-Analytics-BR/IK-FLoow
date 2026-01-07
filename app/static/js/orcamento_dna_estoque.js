/**
 * Módulo de Integração DNA/Estoque para Orçamentos
 * Verifica estoque com DNA similar ao adicionar produto e permite:
 * - Alocar do estoque existente
 * - Gerar OP para quantidade faltante
 * - Calcular previsão de produção automaticamente
 * 
 * IMPORTANTE: 
 * - Previsão de produção é calculada ao SELECIONAR produto
 * - Abatimento de estoque DNA ocorre apenas na APROVAÇÃO do orçamento
 */

// Variáveis globais para controle de alocação
let alocacoesEstoque = [];
let opsGeradas = [];
let previsoesProducao = {};

/**
 * Verifica se existe estoque com DNA similar ao produto selecionado
 * @param {number} produtoId - ID do produto
 * @param {number} quantidade - Quantidade desejada
 * @param {number} largura - Largura em mm (opcional)
 * @param {number} comprimento - Comprimento em mm (opcional)
 * @returns {Promise} - Promise com resultado da busca
 */
async function verificarEstoqueDNA(produtoId, quantidade, largura = 0, comprimento = 0) {
    try {
        const params = new URLSearchParams({
            quantidade: quantidade,
            largura: largura,
            comprimento: comprimento
        });
        
        const response = await fetch(`/api/orcamento/buscar-estoque-dna/${produtoId}?${params}`);
        const data = await response.json();
        
        return data;
    } catch (error) {
        console.error('[DNA] Erro ao verificar estoque:', error);
        return { success: false, message: error.message };
    }
}

/**
 * Exibe modal com opções de alocação de estoque/produção
 * @param {Object} resultado - Resultado da busca de estoque DNA
 * @param {Object} itemOrcamento - Item do orçamento sendo adicionado
 */
function exibirModalAlocacao(resultado, itemOrcamento) {
    // Criar modal se não existir
    let modal = document.getElementById('modalAlocacaoDNA');
    if (!modal) {
        modal = criarModalAlocacao();
        document.body.appendChild(modal);
    }
    
    const tbody = document.getElementById('tbodyEstoqueDNA');
    const resumo = document.getElementById('resumoAlocacaoDNA');
    const btnConfirmar = document.getElementById('btnConfirmarAlocacao');
    
    // Limpar conteúdo anterior
    tbody.innerHTML = '';
    
    // Informações do produto solicitado
    document.getElementById('dnaProdutoSolicitado').textContent = 
        resultado.produto_solicitado?.codigo_dna || 'Não definido';
    document.getElementById('qtdSolicitada').textContent = resultado.quantidade_solicitada;
    
    // Preencher tabela de estoque similar
    if (resultado.estoque_similar && resultado.estoque_similar.length > 0) {
        resultado.estoque_similar.forEach((item, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="form-check">
                        <input class="form-check-input estoque-check" type="checkbox" 
                               id="estoque_${index}" 
                               data-produto-id="${item.produto_id}"
                               data-quantidade-max="${item.estoque_disponivel}"
                               data-preco="${item.preco_unitario}"
                               ${item.tipo_match === 'EXATO' ? 'checked' : ''}>
                    </div>
                </td>
                <td>
                    <strong>${item.produto_codigo || ''}</strong><br>
                    <small>${item.produto_nome}</small>
                </td>
                <td>
                    <span class="badge ${getBadgeClass(item.tipo_match)}">${item.tipo_match}</span><br>
                    <small class="text-muted">${item.codigo_dna || '-'}</small>
                </td>
                <td class="text-center">
                    ${item.largura_mm || '-'} x ${item.comprimento_mm || '-'} mm
                </td>
                <td class="text-center">
                    <strong>${item.estoque_disponivel}</strong>
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm quantidade-alocar"
                           id="qtd_${index}" 
                           value="${Math.min(item.quantidade_sugerida, resultado.quantidade_solicitada)}"
                           min="0" max="${item.estoque_disponivel}" step="0.01"
                           style="width: 80px;">
                </td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    <i class="fas fa-box-open fa-2x mb-2"></i><br>
                    Nenhum produto com DNA similar encontrado no estoque
                </td>
            </tr>
        `;
    }
    
    // Atualizar resumo
    atualizarResumoAlocacao(resultado);
    
    // Armazenar dados para uso posterior
    modal.dataset.itemOrcamento = JSON.stringify(itemOrcamento);
    modal.dataset.resultado = JSON.stringify(resultado);
    
    // Exibir modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Adicionar listeners para checkboxes e inputs
    document.querySelectorAll('.estoque-check, .quantidade-alocar').forEach(el => {
        el.addEventListener('change', () => atualizarResumoAlocacao(resultado));
    });
}

/**
 * Cria o HTML do modal de alocação
 */
function criarModalAlocacao() {
    const modalDiv = document.createElement('div');
    modalDiv.className = 'modal fade';
    modalDiv.id = 'modalAlocacaoDNA';
    modalDiv.tabIndex = -1;
    modalDiv.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-info text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-dna me-2"></i>
                        Alocação de Estoque por DNA
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <!-- Info do produto solicitado -->
                    <div class="alert alert-secondary mb-3">
                        <div class="row">
                            <div class="col-md-6">
                                <strong>DNA Solicitado:</strong> 
                                <span id="dnaProdutoSolicitado" class="badge bg-primary">-</span>
                            </div>
                            <div class="col-md-6">
                                <strong>Quantidade:</strong> 
                                <span id="qtdSolicitada">0</span> unidades
                            </div>
                        </div>
                    </div>
                    
                    <!-- Tabela de estoque similar -->
                    <h6><i class="fas fa-boxes me-1"></i> Estoque Disponível com DNA Similar</h6>
                    <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                        <table class="table table-sm table-hover">
                            <thead class="table-light sticky-top">
                                <tr>
                                    <th width="40">Usar</th>
                                    <th>Produto</th>
                                    <th>DNA/Match</th>
                                    <th class="text-center">Dimensões</th>
                                    <th class="text-center">Disponível</th>
                                    <th>Qtd. Alocar</th>
                                </tr>
                            </thead>
                            <tbody id="tbodyEstoqueDNA">
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Resumo da alocação -->
                    <div class="card mt-3" id="resumoAlocacaoDNA">
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-md-4">
                                    <h6 class="text-muted">Do Estoque</h6>
                                    <h4 class="text-success" id="qtdDoEstoque">0</h4>
                                </div>
                                <div class="col-md-4">
                                    <h6 class="text-muted">A Produzir (OP)</h6>
                                    <h4 class="text-warning" id="qtdAProduzir">0</h4>
                                </div>
                                <div class="col-md-4">
                                    <h6 class="text-muted">Total</h6>
                                    <h4 class="text-primary" id="qtdTotal">0</h4>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Opção de gerar OP -->
                    <div class="form-check mt-3" id="divGerarOP" style="display: none;">
                        <input class="form-check-input" type="checkbox" id="chkGerarOP" checked>
                        <label class="form-check-label" for="chkGerarOP">
                            <i class="fas fa-industry me-1"></i>
                            Gerar Ordem de Produção para quantidade faltante
                        </label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times me-1"></i> Cancelar
                    </button>
                    <button type="button" class="btn btn-outline-warning" id="btnIgnorarDNA">
                        <i class="fas fa-forward me-1"></i> Ignorar e Adicionar Normal
                    </button>
                    <button type="button" class="btn btn-success" id="btnConfirmarAlocacao">
                        <i class="fas fa-check me-1"></i> Confirmar Alocação
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Adicionar event listeners
    setTimeout(() => {
        document.getElementById('btnConfirmarAlocacao')?.addEventListener('click', confirmarAlocacao);
        document.getElementById('btnIgnorarDNA')?.addEventListener('click', ignorarDNAeAdicionar);
    }, 100);
    
    return modalDiv;
}

/**
 * Retorna classe CSS do badge baseado no tipo de match
 */
function getBadgeClass(tipoMatch) {
    switch (tipoMatch) {
        case 'EXATO': return 'bg-success';
        case 'DERIVAVEL': return 'bg-info';
        case 'PARCIAL': return 'bg-warning text-dark';
        default: return 'bg-secondary';
    }
}

/**
 * Atualiza o resumo de alocação baseado nas seleções
 */
function atualizarResumoAlocacao(resultado) {
    let qtdEstoque = 0;
    
    document.querySelectorAll('.estoque-check:checked').forEach((checkbox, index) => {
        const inputQtd = document.getElementById(`qtd_${index}`);
        if (inputQtd) {
            qtdEstoque += parseFloat(inputQtd.value) || 0;
        }
    });
    
    const qtdSolicitada = resultado.quantidade_solicitada || 0;
    const qtdProduzir = Math.max(0, qtdSolicitada - qtdEstoque);
    
    document.getElementById('qtdDoEstoque').textContent = qtdEstoque.toFixed(2);
    document.getElementById('qtdAProduzir').textContent = qtdProduzir.toFixed(2);
    document.getElementById('qtdTotal').textContent = qtdSolicitada.toFixed(2);
    
    // Mostrar/ocultar opção de gerar OP
    const divGerarOP = document.getElementById('divGerarOP');
    if (qtdProduzir > 0) {
        divGerarOP.style.display = 'block';
    } else {
        divGerarOP.style.display = 'none';
    }
}

/**
 * Confirma a alocação selecionada
 */
async function confirmarAlocacao() {
    const modal = document.getElementById('modalAlocacaoDNA');
    const itemOrcamento = JSON.parse(modal.dataset.itemOrcamento || '{}');
    const resultado = JSON.parse(modal.dataset.resultado || '{}');
    
    const alocacoes = [];
    let qtdEstoqueTotal = 0;
    
    // Coletar alocações selecionadas
    document.querySelectorAll('.estoque-check:checked').forEach((checkbox, index) => {
        const inputQtd = document.getElementById(`qtd_${index}`);
        const qtd = parseFloat(inputQtd?.value) || 0;
        
        if (qtd > 0) {
            alocacoes.push({
                produto_estoque_id: parseInt(checkbox.dataset.produtoId),
                quantidade: qtd,
                preco: parseFloat(checkbox.dataset.preco) || 0
            });
            qtdEstoqueTotal += qtd;
        }
    });
    
    const qtdSolicitada = resultado.quantidade_solicitada || 0;
    const qtdProduzir = Math.max(0, qtdSolicitada - qtdEstoqueTotal);
    const gerarOP = document.getElementById('chkGerarOP')?.checked && qtdProduzir > 0;
    
    // Adicionar item ao orçamento com informações de alocação
    itemOrcamento.alocacoes_estoque = alocacoes;
    itemOrcamento.qtd_estoque_alocada = qtdEstoqueTotal;
    itemOrcamento.qtd_a_produzir = qtdProduzir;
    itemOrcamento.gerar_op = gerarOP;
    itemOrcamento.codigo_dna = resultado.produto_solicitado?.codigo_dna;
    
    // Armazenar para processamento posterior
    alocacoesEstoque.push({
        produto_id: itemOrcamento.produto_id,
        alocacoes: alocacoes,
        qtd_produzir: qtdProduzir,
        gerar_op: gerarOP
    });
    
    // Fechar modal
    const bsModal = bootstrap.Modal.getInstance(modal);
    bsModal.hide();
    
    // Chamar função original de adicionar item (se existir)
    if (typeof adicionarItemComAlocacao === 'function') {
        adicionarItemComAlocacao(itemOrcamento);
    } else if (typeof adicionarItemAoOrcamento === 'function') {
        adicionarItemAoOrcamento(itemOrcamento);
    }
    
    // Mostrar feedback
    mostrarToast('success', 
        `Item adicionado! Estoque: ${qtdEstoqueTotal}, ${gerarOP ? `OP: ${qtdProduzir}` : 'Sem OP'}`);
}

/**
 * Ignora verificação de DNA e adiciona item normalmente
 */
function ignorarDNAeAdicionar() {
    const modal = document.getElementById('modalAlocacaoDNA');
    const itemOrcamento = JSON.parse(modal.dataset.itemOrcamento || '{}');
    
    // Fechar modal
    const bsModal = bootstrap.Modal.getInstance(modal);
    bsModal.hide();
    
    // Adicionar item sem alocação especial
    if (typeof adicionarItemAoOrcamento === 'function') {
        adicionarItemAoOrcamento(itemOrcamento);
    }
}

/**
 * Processa alocações ao salvar/aprovar orçamento
 */
async function processarAlocacoesOrcamento(orcamentoId, clienteId, empresaId) {
    const resultados = {
        reservas: [],
        ops: [],
        erros: []
    };
    
    for (const alocacao of alocacoesEstoque) {
        // Reservar estoque
        for (const item of alocacao.alocacoes) {
            try {
                const response = await fetch('/api/orcamento/reservar-estoque', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        orcamento_id: orcamentoId,
                        produto_estoque_id: item.produto_estoque_id,
                        quantidade: item.quantidade
                    })
                });
                const data = await response.json();
                if (data.success) {
                    resultados.reservas.push(data);
                } else {
                    resultados.erros.push(data.message);
                }
            } catch (error) {
                resultados.erros.push(error.message);
            }
        }
        
        // Gerar OP se necessário
        if (alocacao.gerar_op && alocacao.qtd_produzir > 0) {
            try {
                const response = await fetch('/api/orcamento/gerar-op', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        orcamento_id: orcamentoId,
                        produto_id: alocacao.produto_id,
                        quantidade: alocacao.qtd_produzir,
                        cliente_id: clienteId,
                        empresa_id: empresaId
                    })
                });
                const data = await response.json();
                if (data.success) {
                    resultados.ops.push(data);
                    opsGeradas.push(data.numero_op);
                } else {
                    resultados.erros.push(data.message);
                }
            } catch (error) {
                resultados.erros.push(error.message);
            }
        }
    }
    
    return resultados;
}

/**
 * Exibe toast de notificação
 */
function mostrarToast(tipo, mensagem) {
    // Verificar se existe container de toasts
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${mensagem}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    container.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/**
 * Hook para interceptar adição de item ao orçamento
 * Deve ser chamado antes de adicionar o item
 */
async function verificarDNAAnteDeAdicionar(itemOrcamento) {
    // Verificar se produto tem especificações técnicas (DNA)
    const resultado = await verificarEstoqueDNA(
        itemOrcamento.produto_id,
        itemOrcamento.quantidade,
        itemOrcamento.largura || 0,
        itemOrcamento.comprimento || 0
    );
    
    if (!resultado.success) {
        // Produto não tem DNA, adicionar normalmente
        return { continuar: true, item: itemOrcamento };
    }
    
    // Verificar se há estoque similar
    if (resultado.estoque_similar && resultado.estoque_similar.length > 0) {
        // Exibir modal de alocação
        exibirModalAlocacao(resultado, itemOrcamento);
        return { continuar: false, aguardarModal: true };
    }
    
    // Não há estoque similar, perguntar se quer gerar OP
    if (resultado.quantidade_a_produzir > 0) {
        const confirmar = confirm(
            `Não há estoque com DNA similar para este produto.\n\n` +
            `Deseja gerar uma Ordem de Produção para ${resultado.quantidade_solicitada} unidades?`
        );
        
        if (confirmar) {
            itemOrcamento.gerar_op = true;
            itemOrcamento.qtd_a_produzir = resultado.quantidade_solicitada;
            alocacoesEstoque.push({
                produto_id: itemOrcamento.produto_id,
                alocacoes: [],
                qtd_produzir: resultado.quantidade_solicitada,
                gerar_op: true
            });
        }
    }
    
    return { continuar: true, item: itemOrcamento };
}

/**
 * Calcula previsão de produção ao selecionar produto
 * @param {number} produtoId - ID do produto
 * @param {number} quantidade - Quantidade desejada
 * @param {number} empresaId - ID da empresa (opcional)
 * @returns {Promise} - Promise com previsão calculada
 */
async function calcularPrevisaoProducao(produtoId, quantidade = 1, empresaId = 1) {
    try {
        const params = new URLSearchParams({
            quantidade: quantidade,
            empresa_id: empresaId
        });
        
        const response = await fetch(`/api/orcamento/calcular-previsao-producao/${produtoId}?${params}`);
        const data = await response.json();
        
        if (data.success) {
            // Armazenar previsão para uso posterior
            previsoesProducao[produtoId] = data;
        }
        
        return data;
    } catch (error) {
        console.error('[PREVISAO] Erro ao calcular previsão:', error);
        return { success: false, message: error.message };
    }
}

/**
 * Exibe informações de previsão de produção no formulário
 * @param {Object} previsao - Dados da previsão
 * @param {HTMLElement} containerEl - Elemento container para exibir info
 */
function exibirPrevisaoProducao(previsao, containerEl) {
    if (!previsao || !previsao.success) {
        if (containerEl) {
            containerEl.innerHTML = '<small class="text-muted">Previsão não disponível</small>';
        }
        return;
    }
    
    const resumo = previsao.resumo || {};
    const gargalos = previsao.gargalos || [];
    const temGargalo = gargalos.some(g => g.status === 'critico' || g.status === 'atencao');
    
    let html = `
        <div class="previsao-producao-info p-2 border rounded bg-light">
            <div class="row">
                <div class="col-md-4">
                    <small class="text-muted">Previsão de Conclusão:</small><br>
                    <strong class="text-primary fs-6">${resumo.previsao || '-'}</strong>
                </div>
                <div class="col-md-4">
                    <small class="text-muted">Tempo Estimado:</small><br>
                    <strong>${resumo.tempo_total || '-'}</strong>
                </div>
                <div class="col-md-4">
                    <small class="text-muted">Dias Úteis:</small><br>
                    <strong>${resumo.dias_uteis || '-'}</strong>
                </div>
            </div>
    `;
    
    // Mostrar alerta de gargalo se houver
    if (temGargalo) {
        const gargalosCriticos = gargalos.filter(g => g.status === 'critico');
        const gargalosAtencao = gargalos.filter(g => g.status === 'atencao');
        
        html += `
            <div class="mt-2 alert alert-warning py-1 px-2 mb-0">
                <small>
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Atenção:</strong> 
                    ${gargalosCriticos.length > 0 ? `${gargalosCriticos.length} etapa(s) com gargalo crítico. ` : ''}
                    ${gargalosAtencao.length > 0 ? `${gargalosAtencao.length} etapa(s) com atenção.` : ''}
                </small>
            </div>
        `;
    }
    
    // Mostrar ficha técnica se disponível
    if (previsao.ficha_tecnica) {
        html += `
            <div class="mt-2">
                <small class="text-muted">
                    <i class="fas fa-file-alt"></i>
                    Ficha Técnica: ${previsao.ficha_tecnica.nome || 'Padrão'} 
                    (v${previsao.ficha_tecnica.versao || '1'})
                </small>
            </div>
        `;
    }
    
    html += '</div>';
    
    if (containerEl) {
        containerEl.innerHTML = html;
    }
    
    return html;
}

/**
 * Preenche automaticamente o campo de previsão de produção
 * @param {number} produtoId - ID do produto
 * @param {number} quantidade - Quantidade
 */
async function preencherPrevisaoAutomatica(produtoId, quantidade) {
    const previsao = await calcularPrevisaoProducao(produtoId, quantidade);
    
    if (previsao.success) {
        // Preencher campo de data prevista se existir
        const campoPrevisao = document.getElementById('previsao_producao') || 
                              document.getElementById('data_previsao') ||
                              document.querySelector('[name="previsao_producao"]');
        
        if (campoPrevisao) {
            campoPrevisao.value = previsao.previsao_conclusao;
        }
        
        // Exibir info de previsão
        const containerPrevisao = document.getElementById('previsao-producao-container') ||
                                   document.getElementById('info-previsao');
        
        if (containerPrevisao) {
            exibirPrevisaoProducao(previsao, containerPrevisao);
        }
        
        // Mostrar toast de sucesso
        mostrarToast('info', 
            `Previsão: ${previsao.resumo?.previsao || 'calculada'} (${previsao.resumo?.dias_uteis || '?'})`);
    }
    
    return previsao;
}

/**
 * Hook para ser chamado quando produto é selecionado no orçamento
 * @param {Object} produto - Dados do produto selecionado
 * @param {number} quantidade - Quantidade
 */
async function onProdutoSelecionado(produto, quantidade = 1) {
    const produtoId = produto.id || produto.produto_id;
    
    if (!produtoId) {
        console.warn('[DNA] Produto sem ID');
        return;
    }
    
    console.log(`[DNA] Produto selecionado: ${produtoId}, Qtd: ${quantidade}`);
    
    // Calcular e exibir previsão de produção automaticamente
    const previsao = await preencherPrevisaoAutomatica(produtoId, quantidade);
    
    // Retornar dados para uso no formulário
    return {
        produto_id: produtoId,
        previsao: previsao,
        previsao_conclusao: previsao.previsao_conclusao || null,
        dias_uteis: previsao.dias_uteis_necessarios || 0,
        tempo_producao_minutos: previsao.tempo_total_minutos || 0
    };
}

/**
 * Aprova orçamento processando DNA e gerando OPs
 * @param {number} orcamentoId - ID do orçamento
 */
async function aprovarOrcamentoComDNA(orcamentoId) {
    try {
        const response = await fetch(`/api/orcamento/aprovar-orcamento/${orcamentoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Mostrar resumo de OPs geradas
            const ops = data.resultados?.ops_geradas || [];
            
            if (ops.length > 0) {
                let mensagem = `Orçamento aprovado!\n\nOrdens de Produção geradas:\n`;
                ops.forEach(op => {
                    mensagem += `• ${op.numero_op} - ${op.produto} (${op.quantidade} un) - Prev: ${op.previsao}\n`;
                });
                
                alert(mensagem);
            } else {
                mostrarToast('success', 'Orçamento aprovado! Todo o estoque foi alocado.');
            }
            
            // Recarregar página ou redirecionar
            if (typeof window.location.reload === 'function') {
                setTimeout(() => window.location.reload(), 1000);
            }
        } else {
            mostrarToast('danger', `Erro ao aprovar: ${data.message}`);
        }
        
        return data;
    } catch (error) {
        console.error('[DNA] Erro ao aprovar orçamento:', error);
        mostrarToast('danger', `Erro: ${error.message}`);
        return { success: false, message: error.message };
    }
}

/**
 * Cria botão de aprovar orçamento com processamento DNA
 * @param {number} orcamentoId - ID do orçamento
 * @returns {HTMLElement} - Botão criado
 */
function criarBotaoAprovarDNA(orcamentoId) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-success';
    btn.innerHTML = '<i class="fas fa-check-circle me-1"></i> Aprovar (DNA)';
    btn.onclick = async () => {
        if (confirm('Deseja aprovar este orçamento?\n\nIsso irá:\n• Alocar estoque com DNA similar\n• Gerar OPs para quantidades faltantes')) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processando...';
            
            await aprovarOrcamentoComDNA(orcamentoId);
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check-circle me-1"></i> Aprovar (DNA)';
        }
    };
    
    return btn;
}

/**
 * Verifica estoque produzido com DNA similar - APENAS INFORMACIONAL
 * Não reserva nem altera estoque
 * @param {number} produtoId - ID do produto
 * @param {number} quantidade - Quantidade desejada
 */
async function verificarEstoqueProduzido(produtoId, quantidade = 1) {
    try {
        const params = new URLSearchParams({ quantidade: quantidade });
        const response = await fetch(`/api/orcamento/verificar-estoque-produzido/${produtoId}?${params}`);
        const data = await response.json();
        
        if (data.success) {
            exibirModalEstoqueProduzido(data);
        } else {
            mostrarToast('warning', data.message || 'Erro ao verificar estoque');
        }
        
        return data;
    } catch (error) {
        console.error('[ESTOQUE] Erro ao verificar estoque produzido:', error);
        mostrarToast('danger', `Erro: ${error.message}`);
        return { success: false, message: error.message };
    }
}

/**
 * Exibe modal com informações do estoque produzido (informacional)
 * @param {Object} dados - Dados retornados pela API
 */
function exibirModalEstoqueProduzido(dados) {
    // Remover modal existente
    const modalExistente = document.getElementById('modalEstoqueProduzido');
    if (modalExistente) modalExistente.remove();
    
    const produto = dados.produto_solicitado || {};
    const estoque = dados.estoque_similar || [];
    const resumo = dados.resumo || {};
    
    // Determinar cor do badge do resumo
    let badgeClass = 'bg-danger';
    let badgeIcon = 'fa-times-circle';
    if (resumo.atende_pedido) {
        badgeClass = 'bg-success';
        badgeIcon = 'fa-check-circle';
    } else if (resumo.total_disponivel > 0) {
        badgeClass = 'bg-warning';
        badgeIcon = 'fa-exclamation-circle';
    }
    
    // Montar tabela de estoque
    let tabelaEstoque = '';
    if (estoque.length > 0) {
        tabelaEstoque = `
            <table class="table table-sm table-striped">
                <thead class="table-light">
                    <tr>
                        <th>Produto</th>
                        <th>DNA</th>
                        <th class="text-center">Tipo</th>
                        <th class="text-end">Estoque</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        for (const item of estoque) {
            const tipoClass = item.tipo_match === 'PROPRIO' ? 'success' : 
                              item.tipo_match === 'EXATO' ? 'primary' :
                              item.tipo_match === 'DIMENSAO_EXATA' ? 'info' : 'secondary';
            
            tabelaEstoque += `
                <tr>
                    <td>
                        <strong>${item.produto_nome}</strong><br>
                        <small class="text-muted">${item.codigo_interno || '-'}</small>
                    </td>
                    <td><code>${item.codigo_dna || '-'}</code></td>
                    <td class="text-center">
                        <span class="badge bg-${tipoClass}">${item.tipo_match}</span>
                    </td>
                    <td class="text-end fw-bold">${item.estoque_disponivel.toFixed(0)}</td>
                </tr>
            `;
        }
        
        tabelaEstoque += '</tbody></table>';
    } else {
        tabelaEstoque = '<div class="alert alert-warning">Nenhum produto similar encontrado em estoque.</div>';
    }
    
    // Criar modal
    const modalHtml = `
        <div class="modal fade" id="modalEstoqueProduzido" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-boxes me-2"></i>
                            Verificar Estoque Produzido (DNA)
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Produto Solicitado -->
                        <div class="card mb-3">
                            <div class="card-header bg-light">
                                <strong>Produto Solicitado</strong>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-8">
                                        <h6>${produto.nome || '-'}</h6>
                                        <small class="text-muted">
                                            Código: ${produto.codigo || '-'} | 
                                            DNA: <code>${produto.codigo_dna || 'N/A'}</code>
                                        </small>
                                        <br>
                                        <small>
                                            ${produto.tipo_correia || ''} | ${produto.material || ''} |
                                            ${produto.largura_mm}mm x ${produto.comprimento_mm}mm
                                        </small>
                                    </div>
                                    <div class="col-md-4 text-end">
                                        <span class="badge ${badgeClass} fs-6">
                                            <i class="fas ${badgeIcon} me-1"></i>
                                            ${resumo.atende_pedido ? 'ATENDE' : 'INSUFICIENTE'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resumo -->
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body py-2">
                                        <h4 class="mb-0">${dados.quantidade_desejada.toFixed(0)}</h4>
                                        <small class="text-muted">Quantidade Desejada</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center ${resumo.atende_pedido ? 'border-success' : 'border-warning'}">
                                    <div class="card-body py-2">
                                        <h4 class="mb-0 ${resumo.atende_pedido ? 'text-success' : 'text-warning'}">
                                            ${resumo.total_disponivel.toFixed(0)}
                                        </h4>
                                        <small class="text-muted">Total Disponível</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center ${resumo.qtd_faltante > 0 ? 'border-danger' : 'border-success'}">
                                    <div class="card-body py-2">
                                        <h4 class="mb-0 ${resumo.qtd_faltante > 0 ? 'text-danger' : 'text-success'}">
                                            ${resumo.qtd_faltante.toFixed(0)}
                                        </h4>
                                        <small class="text-muted">Faltante</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Tabela de Estoque -->
                        <h6><i class="fas fa-list me-1"></i> Produtos Disponíveis (${estoque.length})</h6>
                        <div style="max-height: 300px; overflow-y: auto;">
                            ${tabelaEstoque}
                        </div>
                        
                        <!-- Mensagem -->
                        ${dados.mensagem ? `
                            <div class="alert ${resumo.atende_pedido ? 'alert-success' : 'alert-warning'} mt-3 mb-0">
                                ${dados.mensagem}
                            </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <small class="text-muted me-auto">
                            <i class="fas fa-info-circle"></i>
                            Informação apenas para consulta. Estoque não será reservado.
                        </small>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = new bootstrap.Modal(document.getElementById('modalEstoqueProduzido'));
    modal.show();
}

/**
 * Cria botão de verificar estoque produzido
 * @param {number} produtoId - ID do produto
 * @param {function} getQuantidade - Função que retorna a quantidade atual
 * @returns {HTMLElement} - Botão criado
 */
function criarBotaoVerificarEstoque(produtoId, getQuantidade) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-info btn-sm';
    btn.innerHTML = '<i class="fas fa-boxes me-1"></i> Verificar Estoque';
    btn.title = 'Verificar estoque produzido com DNA similar (informacional)';
    btn.onclick = async () => {
        const qtd = typeof getQuantidade === 'function' ? getQuantidade() : 1;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Verificando...';
        
        await verificarEstoqueProduzido(produtoId, qtd);
        
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-boxes me-1"></i> Verificar Estoque';
    };
    
    return btn;
}

// Exportar funções para uso global
window.verificarEstoqueDNA = verificarEstoqueDNA;
window.verificarDNAAnteDeAdicionar = verificarDNAAnteDeAdicionar;
window.exibirModalAlocacao = exibirModalAlocacao;
window.processarAlocacoesOrcamento = processarAlocacoesOrcamento;
window.calcularPrevisaoProducao = calcularPrevisaoProducao;
window.preencherPrevisaoAutomatica = preencherPrevisaoAutomatica;
window.onProdutoSelecionado = onProdutoSelecionado;
window.aprovarOrcamentoComDNA = aprovarOrcamentoComDNA;
window.exibirPrevisaoProducao = exibirPrevisaoProducao;
window.criarBotaoAprovarDNA = criarBotaoAprovarDNA;
window.verificarEstoqueProduzido = verificarEstoqueProduzido;
window.exibirModalEstoqueProduzido = exibirModalEstoqueProduzido;
window.criarBotaoVerificarEstoque = criarBotaoVerificarEstoque;
window.alocacoesEstoque = alocacoesEstoque;
window.opsGeradas = opsGeradas;
window.previsoesProducao = previsoesProducao;
