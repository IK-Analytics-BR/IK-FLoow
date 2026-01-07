/**
 * Orcamento Form - JavaScript Functions
 * Sistema com navegação fluida por teclado
 */

// Variaveis globais
let itensOrcamento = [];
let duplicatasOrcamento = [];
let comissionadosOrcamento = [];
let crmHistorico = [];
let linhaClienteSelecionada = -1;
let linhaProdutoSelecionada = -1;
let linhaTransportadoraSelecionada = -1;

// =====================================================
// INICIALIZACAO
// =====================================================
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar data de hoje
    const hoje = new Date().toISOString().split('T')[0];
    const dataEmissao = document.querySelector('input[name="data_emissao"]');
    if (dataEmissao && !dataEmissao.value) {
        dataEmissao.value = hoje;
    }
    
    // Data validade padrao (15 dias)
    const dataValidade = document.querySelector('input[name="data_validade"]');
    if (dataValidade && !dataValidade.value) {
        const validade = new Date();
        validade.setDate(validade.getDate() + 15);
        dataValidade.value = validade.toISOString().split('T')[0];
    }
    
    // Bind eventos
    bindEventos();
    
    // Bind teclas de atalho globais
    bindAtalhosGlobais();
    
    // Carregar itens existentes (se edição)
    carregarItensExistentes();
    
    // Carregar forma de pagamento existente (se edição)
    carregarFormaPagamentoExistente();
    
    // Calcular totais iniciais
    calcularTotais();
    
    // Interceptar submit do form
    const form = document.getElementById('formOrcamento');
    if (form) form.addEventListener('submit', prepararEnvio);
});

// =====================================================
// ATALHOS DE TECLADO GLOBAIS
// =====================================================
function bindAtalhosGlobais() {
    document.addEventListener('keydown', function(e) {
        // Ignorar se estiver em modal aberto
        const modalAberto = document.querySelector('.modal.show');
        
        // =====================================================
        // F5 = PRÓXIMA ABA (navegação sequencial)
        // F6 = ABA ANTERIOR
        // =====================================================
        if ((e.key === 'F5' || e.key === 'F6') && !modalAberto) {
            e.preventDefault();
            e.stopPropagation();
            
            const abas = [
                '#tabDados',      // 1 - Dados do Orcamento
                '#tabItens',      // 2 - Itens
                '#tabDuplicatas', // 3 - Pagamento
                '#tabTransporte', // 4 - Transporte
                '#tabOutros',     // 5 - Outros
                '#tabComissao',   // 6 - Comissao
                '#tabCRM'         // 7 - CRM
            ];
            
            // Encontrar aba atual
            let abaAtualIdx = 0;
            abas.forEach((aba, idx) => {
                const tabPane = document.querySelector(aba);
                if (tabPane && tabPane.classList.contains('active')) {
                    abaAtualIdx = idx;
                }
            });
            
            // Calcular próxima aba
            let novaAbaIdx;
            if (e.key === 'F5') {
                novaAbaIdx = (abaAtualIdx + 1) % abas.length; // Próxima (circular)
            } else {
                novaAbaIdx = (abaAtualIdx - 1 + abas.length) % abas.length; // Anterior (circular)
            }
            
            // Ativar nova aba
            const novaAba = abas[novaAbaIdx];
            const tab = document.querySelector(`a[href="${novaAba}"]`);
            if (tab) {
                tab.click();
                // Focar no primeiro campo da aba
                setTimeout(() => focarPrimeiroCampoAba(novaAba), 200);
                
                // Atualizar indicador
                atualizarIndicadorAba(novaAbaIdx + 1);
                
                // Se for aba de Pagamento, atualizar valores e gerar parcelas
                if (novaAba === '#tabDuplicatas') {
                    setTimeout(() => {
                        atualizarParcelas(); // Sincroniza forma de pagamento
                        atualizarValorTotalPagamento(); // Atualiza valor
                        // Gerar parcelas automaticamente se tiver forma de pagamento
                        if (formaPagamentoSelecionada && formaPagamentoSelecionada.id) {
                            gerarParcelasPagamento();
                        }
                    }, 100);
                }
            }
            return;
        }
        
        // =====================================================
        // F2/F3 - Busca (contextual por aba)
        // =====================================================
        if ((e.key === 'F2' || e.key === 'F3') && !modalAberto) {
            e.preventDefault();
            e.stopPropagation();
            
            // Verificar qual aba está ativa
            const tabItensAtiva = document.querySelector('#tabItens.active, #tabItens.show');
            const tabTransporteAtiva = document.querySelector('#tabTransporte.active, #tabTransporte.show');
            const tabPagamentoAtiva = document.querySelector('#tabDuplicatas.active, #tabDuplicatas.show');
            
            // Aba Itens ou campo produto -> buscar produto
            if (tabItensAtiva || document.activeElement.id === 'produto_codigo') {
                abrirBuscaProduto();
            }
            // Aba Transporte ou campo transportadora -> buscar transportadora
            else if (tabTransporteAtiva || document.activeElement.id === 'transportadora_codigo') {
                abrirBuscaTransportadora();
            }
            // Aba Pagamento -> buscar forma de pagamento
            else if (tabPagamentoAtiva || document.activeElement.id === 'pagamento_nome') {
                abrirModalFormaPagamento();
            }
            // Aba Dados ou outras -> buscar cliente
            else {
                abrirBuscaCliente();
            }
            return;
        }
        
        // =====================================================
        // Navegação nos modais
        // =====================================================
        if (modalAberto && modalAberto.id === 'modalBuscaCliente') {
            handleNavegacaoModalCliente(e);
            return;
        }
        
        if (modalAberto && modalAberto.id === 'modalBuscaProduto') {
            handleNavegacaoModalProduto(e);
            return;
        }
        
        if (modalAberto && modalAberto.id === 'modalBuscaTransportadora') {
            handleNavegacaoModalTransportadora(e);
            return;
        }
        
        // =====================================================
        // Enter para navegar entre campos
        // =====================================================
        if (e.key === 'Enter' && !modalAberto) {
            handleEnterNavegacao(e);
        }
    });
}

// Focar no primeiro campo de uma aba
function focarPrimeiroCampoAba(abaId) {
    const primeirosCampos = {
        '#tabDados': 'cliente_codigo',
        '#tabItens': 'produto_codigo',
        '#tabTransporte': 'perfil_transporte',
        '#tabComissao': 'comissao_vendedor1_aliquota',
        '#tabDuplicatas': null,
        '#tabCRM': null,
        '#tabOutros': 'observacoes'
    };
    
    const campoId = primeirosCampos[abaId];
    if (campoId) {
        const campo = document.getElementById(campoId);
        if (campo) campo.focus();
    }
}

// Navegação por Enter entre campos
function handleEnterNavegacao(e) {
    const el = document.activeElement;
    
    // Ignorar se for textarea ou botão
    if (el.tagName === 'TEXTAREA' || el.tagName === 'BUTTON') return;
    
    // Campos da aba Dados (ordem de navegação)
    const camposDados = [
        'cliente_codigo', 'vendedor_id', 'vendedor2_id', 
        'data_validade', 'condicao_pagamento', 'forma_pagamento_id'
    ];
    
    // Campos da aba Itens
    const camposItens = [
        'produto_codigo', 'item_quantidade', 'item_preco_lista', 
        'item_perc_desconto', 'item_preco_unitario'
    ];
    
    const idxDados = camposDados.indexOf(el.id);
    const idxItens = camposItens.indexOf(el.id);
    
    // Navegação na aba Dados
    if (idxDados >= 0) {
        e.preventDefault();
        
        // Último campo da aba Dados -> ir para aba Itens
        if (idxDados === camposDados.length - 1) {
            const tabItens = document.querySelector('a[href="#tabItens"]');
            if (tabItens) {
                tabItens.click();
                setTimeout(() => {
                    const campoProduto = document.getElementById('produto_codigo');
                    if (campoProduto) campoProduto.focus();
                }, 200);
            }
        } else {
            // Próximo campo
            const proximo = document.getElementById(camposDados[idxDados + 1]);
            if (proximo) {
                proximo.focus();
                if (proximo.select) proximo.select();
            }
        }
        return;
    }
    
    // Navegação na aba Itens
    if (idxItens >= 0) {
        e.preventDefault();
        
        // Último campo -> adicionar item
        if (idxItens === camposItens.length - 1) {
            adicionarItem();
        } else {
            // Próximo campo
            const proximo = document.getElementById(camposItens[idxItens + 1]);
            if (proximo) {
                proximo.focus();
                if (proximo.select) proximo.select();
            }
        }
    }
}

function handleNavegacaoModalCliente(e) {
    const tbody = document.getElementById('tbodyClientes');
    const rows = tbody.querySelectorAll('.cliente-row');
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (rows.length > 0) {
            linhaClienteSelecionada = Math.min(linhaClienteSelecionada + 1, rows.length - 1);
            destacarLinhaCliente(rows);
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (rows.length > 0) {
            linhaClienteSelecionada = Math.max(linhaClienteSelecionada - 1, 0);
            destacarLinhaCliente(rows);
        }
    } else if (e.key === 'Enter') {
        e.preventDefault();
        // Se tem linha selecionada, selecionar ela
        if (linhaClienteSelecionada >= 0 && rows[linhaClienteSelecionada]) {
            rows[linhaClienteSelecionada].click();
        } 
        // Se não tem linha selecionada, pesquisar
        else {
            pesquisarClientes();
        }
    } else if (e.key === 'Escape') {
        fecharModalCliente();
    }
}

function handleNavegacaoModalProduto(e) {
    const tbody = document.getElementById('tbodyProdutos');
    const rows = tbody.querySelectorAll('.produto-row');
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (rows.length > 0) {
            linhaProdutoSelecionada = Math.min(linhaProdutoSelecionada + 1, rows.length - 1);
            destacarLinhaProduto(rows);
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (rows.length > 0) {
            linhaProdutoSelecionada = Math.max(linhaProdutoSelecionada - 1, 0);
            destacarLinhaProduto(rows);
        }
    } else if (e.key === 'Enter') {
        e.preventDefault();
        // Se tem linha selecionada, selecionar ela
        if (linhaProdutoSelecionada >= 0 && rows[linhaProdutoSelecionada]) {
            selecionarProdutoDestacado();
        } 
        // Se não tem linha selecionada, pesquisar
        else {
            pesquisarProdutos();
        }
    } else if (e.key === 'Escape') {
        fecharModalProduto();
    }
}

function destacarLinhaCliente(rows) {
    rows.forEach((r, i) => {
        r.classList.toggle('table-primary', i === linhaClienteSelecionada);
    });
    if (rows[linhaClienteSelecionada]) {
        rows[linhaClienteSelecionada].scrollIntoView({ block: 'nearest' });
    }
}

function destacarLinhaProduto(rows) {
    rows.forEach((r, i) => {
        r.classList.toggle('table-primary', i === linhaProdutoSelecionada);
    });
    if (rows[linhaProdutoSelecionada]) {
        rows[linhaProdutoSelecionada].scrollIntoView({ block: 'nearest' });
    }
}

function bindEventos() {
    // Calculos de item
    ['item_quantidade', 'item_preco_lista', 'item_perc_desconto', 'item_preco_unitario'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', calcularItemTotal);
    });
    
    // Eventos de frete e desconto
    ['valor_frete', 'valor_seguro', 'percentual_desconto'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', calcularTotais);
    });
    
    // Eventos de comissao
    ['comissao_vendedor1_aliquota', 'comissao_vendedor2_aliquota', 'comissao_vendedor3_aliquota', 'comissao_vendedor4_aliquota'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', () => calcularTotais());
    });
    
    // Evento de mudança de vendedor - sincronizar com aba de comissão
    const vendedor1Select = document.getElementById('vendedor_id');
    if (vendedor1Select) {
        // Ao mudar vendedor manualmente, forçar atualização da comissão
        vendedor1Select.addEventListener('change', () => sincronizarVendedorComissao(true));
        // Carregar inicial se já houver valor (não força para respeitar valor salvo)
        sincronizarVendedorComissao(false);
    }
    
    const vendedor2Select = document.getElementById('vendedor2_id');
    if (vendedor2Select) {
        vendedor2Select.addEventListener('change', () => sincronizarVendedor2Comissao(true));
        sincronizarVendedor2Comissao(false);
    }
    
    // Listener para clique na aba Pagamento - atualizar valores e gerar parcelas
    const tabPagamento = document.querySelector('a[href="#tabDuplicatas"]');
    if (tabPagamento) {
        tabPagamento.addEventListener('shown.bs.tab', function() {
            atualizarParcelas(); // Sincroniza forma de pagamento
            atualizarValorTotalPagamento(); // Atualiza valor
            
            // Gerar parcelas automaticamente se tiver forma de pagamento selecionada
            if (formaPagamentoSelecionada && formaPagamentoSelecionada.id) {
                setTimeout(() => {
                    gerarParcelasPagamento();
                }, 200);
            }
        });
    }
    
    // Listener para clique na aba Outros - carregar select de itens
    const tabOutros = document.querySelector('a[href="#tabOutros"]');
    if (tabOutros) {
        tabOutros.addEventListener('shown.bs.tab', function() {
            carregarInsumosItens();
        });
    }
    
    // Listener para clique na aba Comissão - recalcular comissões
    const tabComissao = document.querySelector('a[href="#tabComissao"]');
    if (tabComissao) {
        tabComissao.addEventListener('shown.bs.tab', function() {
            console.log('[Comissao] Aba Comissao aberta - recalculando...');
            calcularComissoes();
        });
    }
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// =====================================================
// CLIENTE
// =====================================================
function buscarCliente() {
    abrirBuscaCliente();
}

function abrirBuscaCliente() {
    linhaClienteSelecionada = -1;
    const modalEl = document.getElementById('modalBuscaCliente');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    
    // Limpar busca anterior
    document.getElementById('busca_cliente_input').value = '';
    document.getElementById('tbodyClientes').innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Digite para buscar...</td></tr>';
    
    // Focar quando o modal terminar de abrir
    modalEl.addEventListener('shown.bs.modal', function focaCliente() {
        document.getElementById('busca_cliente_input').focus();
        modalEl.removeEventListener('shown.bs.modal', focaCliente);
    });
    
    modal.show();
}

function fecharModalCliente() {
    const modalEl = document.getElementById('modalBuscaCliente');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
}

function pesquisarClientes() {
    const termo = document.getElementById('busca_cliente_input').value;
    if (termo.length < 2) {
        alert('Digite pelo menos 2 caracteres para buscar.');
        return;
    }
    
    const tbody = document.getElementById('tbodyClientes');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Buscando...</td></tr>';
    
    fetch(`/orcamentos/api/buscar-clientes?q=${encodeURIComponent(termo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Nenhum cliente encontrado.</td></tr>';
                return;
            }
            
            let html = '';
            data.forEach(c => {
                const nome = c.nome || c.name || '';
                const doc = c.documento || c.cnpj || c.cpf || '';
                const cidade = c.cidade || '';
                const estado = c.estado || c.uf || '';
                
                html += `<tr style="cursor:pointer" class="cliente-row" 
                            data-id="${c.id}" 
                            data-nome="${nome.replace(/"/g, '&quot;')}" 
                            data-documento="${doc}"
                            data-cidade="${cidade}"
                            data-estado="${estado}">
                    <td>${c.id}</td>
                    <td>${nome}</td>
                    <td>${doc}</td>
                    <td>${cidade}</td>
                    <td>${estado}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
            
            // Adicionar eventos de clique
            tbody.querySelectorAll('.cliente-row').forEach(row => {
                row.addEventListener('click', function() {
                    const id = this.dataset.id;
                    const nome = this.dataset.nome;
                    const documento = this.dataset.documento;
                    const cidade = this.dataset.cidade;
                    const estado = this.dataset.estado;
                    selecionarCliente(id, nome, documento, cidade, estado);
                });
            });
        })
        .catch(err => {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-3">Erro ao buscar clientes.</td></tr>';
            console.error(err);
        });
}

function selecionarCliente(id, nome, documento, cidade, uf) {
    document.getElementById('cliente_id').value = id;
    document.getElementById('cliente_codigo').value = id;
    document.getElementById('cliente_nome').value = nome;
    
    // Atualizar observação cadastral se existir
    const obsEl = document.getElementById('cliente_obs');
    if (obsEl) obsEl.textContent = cidade ? `${cidade}/${uf}` : 'Cliente selecionado';
    
    // Fechar modal
    fecharModalCliente();
    
    // Ficar na aba atual e focar no próximo campo
    setTimeout(() => {
        const proximoCampo = document.getElementById('vendedor_id');
        if (proximoCampo) {
            proximoCampo.focus();
        }
    }, 300);
}

function centralInfoCliente() {
    const clienteId = document.getElementById('cliente_id').value;
    if (clienteId) {
        window.open(`/clientes/${clienteId}`, '_blank');
    } else {
        alert('Selecione um cliente primeiro.');
    }
}

function limiteCredito() {
    alert('Funcionalidade de limite de credito em desenvolvimento.');
}

function detalharCliente() {
    const clienteId = document.getElementById('cliente_id').value;
    if (clienteId) {
        window.open(`/clientes/${clienteId}`, '_blank');
    }
}

function selecionarContatos() {
    alert('Funcionalidade de selecao de contatos em desenvolvimento.');
}

// =====================================================
// PRODUTO
// =====================================================
function buscarProduto() {
    abrirBuscaProduto();
}

function abrirBuscaProduto() {
    linhaProdutoSelecionada = -1;
    const modalEl = document.getElementById('modalBuscaProduto');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    
    // Limpar busca anterior
    document.getElementById('busca_produto_input').value = '';
    document.getElementById('tbodyProdutos').innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Digite para buscar...</td></tr>';
    
    // Focar quando o modal terminar de abrir
    modalEl.addEventListener('shown.bs.modal', function focaProduto() {
        document.getElementById('busca_produto_input').focus();
        modalEl.removeEventListener('shown.bs.modal', focaProduto);
    });
    
    modal.show();
}

function fecharModalProduto() {
    const modalEl = document.getElementById('modalBuscaProduto');
    if (!modalEl) return;
    
    // Tentar fechar via Bootstrap
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
    
    // Forçar fechamento imediato
    modalEl.classList.remove('show');
    modalEl.style.display = 'none';
    modalEl.setAttribute('aria-hidden', 'true');
    modalEl.removeAttribute('aria-modal');
    
    // Remover backdrop imediatamente
    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('padding-right');
    document.body.style.removeProperty('overflow');
}

function pesquisarProdutos() {
    const termo = document.getElementById('busca_produto_input').value;
    if (termo.length < 2) {
        alert('Digite pelo menos 2 caracteres para buscar.');
        return;
    }
    
    const tbody = document.getElementById('tbodyProdutos');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Buscando...</td></tr>';
    
    fetch(`/orcamentos/api/buscar-produtos?q=${encodeURIComponent(termo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Nenhum produto encontrado.</td></tr>';
                return;
            }
            
            let html = '';
            data.forEach((p, idx) => {
                const nome = p.nome || p.name || p.description || '';
                const codigo = p.codigo || p.internal_code || p.id;
                const preco = parseFloat(p.preco || p.sale_price || p.price || 0);
                const unidade = p.unidade || p.unit || 'UN';
                const estoque = p.estoque || p.stock_quantity || 0;
                
                html += `<tr style="cursor:pointer" class="produto-row" 
                            data-idx="${idx}"
                            data-id="${p.id}" 
                            data-codigo="${codigo}" 
                            data-nome="${nome.replace(/"/g, '&quot;')}" 
                            data-preco="${preco}" 
                            data-unidade="${unidade}"
                            onmouseover="this.classList.add('table-info')"
                            onmouseout="if(!this.classList.contains('table-primary')) this.classList.remove('table-info')">
                    <td>${codigo}</td>
                    <td>${nome}</td>
                    <td>${unidade}</td>
                    <td class="text-end">R$ ${preco.toFixed(2).replace('.', ',')}</td>
                    <td class="text-end">${estoque}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
            
            // Adicionar eventos de clique simples (destacar) e duplo clique (selecionar)
            tbody.querySelectorAll('.produto-row').forEach(row => {
                // Clique simples - destaca a linha
                row.addEventListener('click', function() {
                    // Remover destaque de outras linhas
                    tbody.querySelectorAll('.produto-row').forEach(r => r.classList.remove('table-primary'));
                    this.classList.add('table-primary');
                    linhaProdutoSelecionada = parseInt(this.dataset.idx);
                });
                
                // Duplo clique - seleciona o produto
                row.addEventListener('dblclick', function() {
                    const id = this.dataset.id;
                    const codigo = this.dataset.codigo;
                    const nome = this.dataset.nome;
                    const preco = parseFloat(this.dataset.preco);
                    const unidade = this.dataset.unidade;
                    selecionarProduto(id, codigo, nome, preco, unidade);
                });
            });
            
            // Selecionar primeiro automaticamente se houver resultados
            if (data.length > 0) {
                linhaProdutoSelecionada = 0;
                const firstRow = tbody.querySelector('.produto-row');
                if (firstRow) firstRow.classList.add('table-primary');
            }
        })
        .catch(err => {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-3">Erro ao buscar produtos.</td></tr>';
            console.error(err);
        });
}

// Selecionar produto que está destacado na tabela (via botão ou Enter)
function selecionarProdutoDestacado() {
    const tbody = document.getElementById('tbodyProdutos');
    const rows = tbody.querySelectorAll('.produto-row');
    
    if (linhaProdutoSelecionada >= 0 && rows[linhaProdutoSelecionada]) {
        const row = rows[linhaProdutoSelecionada];
        const id = row.dataset.id;
        const codigo = row.dataset.codigo;
        const nome = row.dataset.nome;
        const preco = parseFloat(row.dataset.preco);
        const unidade = row.dataset.unidade;
        
        // Resetar seleção antes de fechar
        linhaProdutoSelecionada = -1;
        
        // Fechar modal primeiro
        fecharModalProduto();
        
        // Depois preencher os campos (com verificação de null)
        const produtoIdEl = document.getElementById('produto_id');
        const produtoCodigoEl = document.getElementById('produto_codigo');
        const produtoNomeEl = document.getElementById('produto_nome');
        const unidadeEl = document.getElementById('item_unidade');
        const precoListaEl = document.getElementById('item_preco_lista');
        const precoUnitarioEl = document.getElementById('item_preco_unitario');
        const quantidadeEl = document.getElementById('item_quantidade');
        const percDescontoEl = document.getElementById('item_perc_desconto');
        
        if (produtoIdEl) produtoIdEl.value = id;
        if (produtoCodigoEl) produtoCodigoEl.value = codigo || id;
        if (produtoNomeEl) produtoNomeEl.value = nome;
        if (unidadeEl) unidadeEl.value = unidade;
        if (precoListaEl) precoListaEl.value = preco.toFixed(2);
        if (precoUnitarioEl) precoUnitarioEl.value = preco.toFixed(2);
        if (quantidadeEl) quantidadeEl.value = '1';
        if (percDescontoEl) percDescontoEl.value = '0';
        calcularItemTotal();
        
        // Focar no campo quantidade
        setTimeout(() => {
            const qtdEl = document.getElementById('item_quantidade');
            if (qtdEl) {
                qtdEl.focus();
                qtdEl.select();
            }
        }, 100);
    } else {
        alert('Selecione um produto da lista primeiro (clique na linha ou use as setas).');
    }
}

function selecionarProduto(id, codigo, nome, preco, unidade) {
    const produtoIdEl = document.getElementById('produto_id');
    const produtoCodigoEl = document.getElementById('produto_codigo');
    const produtoNomeEl = document.getElementById('produto_nome');
    const unidadeEl = document.getElementById('item_unidade');
    const precoListaEl = document.getElementById('item_preco_lista');
    const precoUnitarioEl = document.getElementById('item_preco_unitario');
    const quantidadeEl = document.getElementById('item_quantidade');
    const percDescontoEl = document.getElementById('item_perc_desconto');
    
    if (produtoIdEl) produtoIdEl.value = id;
    if (produtoCodigoEl) produtoCodigoEl.value = codigo || id;
    if (produtoNomeEl) produtoNomeEl.value = nome;
    if (unidadeEl) unidadeEl.value = unidade;
    if (precoListaEl) precoListaEl.value = preco.toFixed(2);
    if (precoUnitarioEl) precoUnitarioEl.value = preco.toFixed(2);
    if (quantidadeEl) quantidadeEl.value = '1';
    if (percDescontoEl) percDescontoEl.value = '0';
    calcularItemTotal();
    
    // Fechar modal
    fecharModalProduto();
    
    // Focar no campo quantidade e selecionar
    setTimeout(() => {
        const qtdEl = document.getElementById('item_quantidade');
        if (qtdEl) {
            qtdEl.focus();
            qtdEl.select();
        }
    }, 300);
}

function detalharProduto() {
    const produtoId = document.getElementById('produto_id').value;
    if (produtoId) {
        window.open(`/produtos/${produtoId}`, '_blank');
    }
}

// =====================================================
// ITENS
// =====================================================
function calcularItemTotal() {
    const qtdEl = document.getElementById('item_quantidade');
    const precoListaEl = document.getElementById('item_preco_lista');
    const percDescontoEl = document.getElementById('item_perc_desconto');
    const precoUnitarioEl = document.getElementById('item_preco_unitario');
    const subtotalEl = document.getElementById('item_subtotal');
    const totalEl = document.getElementById('item_total');
    
    const qtd = parseFloat(qtdEl?.value) || 0;
    const precoLista = parseFloat(precoListaEl?.value) || 0;
    const percDesconto = parseFloat(percDescontoEl?.value) || 0;
    
    const precoUnitario = precoLista * (1 - percDesconto / 100);
    const subtotal = qtd * precoUnitario;
    
    if (precoUnitarioEl) precoUnitarioEl.value = precoUnitario.toFixed(2);
    if (subtotalEl) subtotalEl.value = subtotal.toLocaleString('pt-BR', {minimumFractionDigits: 2});
    if (totalEl) totalEl.value = subtotal.toLocaleString('pt-BR', {minimumFractionDigits: 2});
}

function adicionarItem() {
    const produtoId = document.getElementById('produto_id').value;
    const produtoCodigo = document.getElementById('produto_codigo').value;
    const produtoNome = document.getElementById('produto_nome').value;
    const unidade = document.getElementById('item_unidade')?.value || 'UN';
    const quantidade = parseFloat(document.getElementById('item_quantidade').value) || 0;
    const precoLista = parseFloat(document.getElementById('item_preco_lista').value) || 0;
    const percDesconto = parseFloat(document.getElementById('item_perc_desconto').value) || 0;
    const precoUnitario = parseFloat(document.getElementById('item_preco_unitario').value) || 0;
    const observacao = document.getElementById('item_observacao')?.value || '';
    
    if (!produtoId) {
        alert('Selecione um produto.');
        document.getElementById('produto_codigo').focus();
        return;
    }
    
    if (quantidade <= 0) {
        alert('Informe a quantidade.');
        document.getElementById('item_quantidade').focus();
        return;
    }
    
    const valorTotal = quantidade * precoUnitario;
    
    const item = {
        id: Date.now(),
        produto_id: parseInt(produtoId),
        produto_codigo: produtoCodigo,
        produto_nome: produtoNome,
        unidade: unidade,
        quantidade: quantidade,
        preco_tabela: precoLista,
        preco_lista: precoLista,
        percentual_desconto: percDesconto,
        preco_unitario: precoUnitario,
        valor_total: valorTotal,
        observacao: observacao
    };
    
    itensOrcamento.push(item);
    renderizarItens();
    limparCamposItem();
    calcularTotais();
    
    // Focar no campo código para próximo item
    document.getElementById('produto_codigo').focus();
}

function removerItem(id) {
    itensOrcamento = itensOrcamento.filter(i => i.id !== id);
    renderizarItens();
    calcularTotais();
}

// Editar item da grade - carrega nos campos para edição (para itens do array JS)
function editarItem(btn) {
    const row = btn.closest('tr');
    if (!row) return;
    
    const itemId = row.dataset.id;
    // Buscar comparando como string
    const item = itensOrcamento.find(i => String(i.id) === String(itemId));
    
    if (!item) {
        // Se não encontrou no array, tenta ler direto do HTML
        editarItemDireto(btn);
        return;
    }
    
    // Carregar dados do item nos campos
    document.getElementById('produto_id').value = item.produto_id;
    document.getElementById('produto_codigo').value = item.produto_codigo;
    document.getElementById('produto_nome').value = item.produto_nome;
    document.getElementById('item_unidade').value = item.unidade || 'UN';
    document.getElementById('item_quantidade').value = item.quantidade;
    document.getElementById('item_preco_lista').value = (item.preco_lista || item.preco_tabela || 0).toFixed(2);
    document.getElementById('item_perc_desconto').value = item.percentual_desconto || 0;
    document.getElementById('item_preco_unitario').value = parseFloat(item.preco_unitario).toFixed(2);
    if (document.getElementById('item_observacao')) {
        document.getElementById('item_observacao').value = item.observacao || '';
    }
    
    // Remover o item da lista (será readicionado ao clicar em Adicionar)
    itensOrcamento = itensOrcamento.filter(i => String(i.id) !== String(itemId));
    renderizarItens();
    calcularTotais();
    
    // Calcular e focar no campo quantidade
    calcularItemTotal();
    document.getElementById('item_quantidade').focus();
    document.getElementById('item_quantidade').select();
}

// Editar item lendo dados diretamente dos data-attributes (para itens do Jinja2)
function editarItemDireto(btn) {
    const row = btn.closest('tr');
    if (!row) return;
    
    // Ler dados dos data-attributes
    const produtoId = row.dataset.produtoId;
    const codigo = row.dataset.codigo;
    const nome = row.dataset.nome;
    const unidade = row.dataset.unidade || 'UN';
    const quantidade = parseFloat(row.dataset.quantidade) || 0;
    const precoLista = parseFloat(row.dataset.precoLista) || 0;
    const desconto = parseFloat(row.dataset.desconto) || 0;
    const precoUnitario = parseFloat(row.dataset.precoUnitario) || 0;
    
    // Carregar nos campos
    document.getElementById('produto_id').value = produtoId;
    document.getElementById('produto_codigo').value = codigo;
    document.getElementById('produto_nome').value = nome;
    document.getElementById('item_unidade').value = unidade;
    document.getElementById('item_quantidade').value = quantidade;
    document.getElementById('item_preco_lista').value = precoLista.toFixed(2);
    document.getElementById('item_perc_desconto').value = desconto;
    document.getElementById('item_preco_unitario').value = precoUnitario.toFixed(2);
    if (document.getElementById('item_observacao')) {
        document.getElementById('item_observacao').value = '';
    }
    
    // Remover do array JS se existir
    const itemId = row.dataset.id;
    itensOrcamento = itensOrcamento.filter(i => String(i.id) !== String(itemId));
    
    // Remover a linha do HTML
    row.remove();
    
    // Verificar se ficou vazio
    const tbody = document.getElementById('tbodyItens');
    if (tbody && tbody.querySelectorAll('tr[data-id]').length === 0 && itensOrcamento.length === 0) {
        tbody.innerHTML = '<tr id="semItens"><td colspan="9" class="text-center text-muted py-4">Nenhum item adicionado</td></tr>';
    }
    
    calcularTotais();
    calcularItemTotal();
    document.getElementById('item_quantidade').focus();
    document.getElementById('item_quantidade').select();
}

// Remover item por ID (string)
function removerItemPorId(itemId) {
    // Remover do array JS
    itensOrcamento = itensOrcamento.filter(i => String(i.id) !== String(itemId));
    
    // Remover do HTML
    const row = document.querySelector(`tr[data-id="${itemId}"]`);
    if (row) row.remove();
    
    // Verificar se ficou vazio
    const tbody = document.getElementById('tbodyItens');
    if (tbody && tbody.querySelectorAll('tr[data-id]').length === 0 && itensOrcamento.length === 0) {
        tbody.innerHTML = '<tr id="semItens"><td colspan="9" class="text-center text-muted py-4">Nenhum item adicionado</td></tr>';
    }
    
    calcularTotais();
}

// Aplicar lista de preço ao produto selecionado
function aplicarListaPreco() {
    const produtoIdEl = document.getElementById('produto_id');
    const listaPrecoEl = document.getElementById('lista_preco');
    
    if (!produtoIdEl || !listaPrecoEl) {
        console.log('[Lista Preço] Elementos não encontrados');
        return;
    }
    
    const produtoId = produtoIdEl.value;
    const listaId = listaPrecoEl.value;
    
    console.log('[Lista Preço] Produto:', produtoId, 'Lista:', listaId);
    
    if (!produtoId) {
        console.log('[Lista Preço] Nenhum produto selecionado');
        return;
    }
    
    let url = `/api/preco-produto?produto_id=${produtoId}`;
    if (listaId) url += `&lista_id=${listaId}`;
    
    console.log('[Lista Preço] URL:', url);
    
    fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(response => {
            console.log('[Lista Preço] Response status:', response.status);
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.text();
        })
        .then(text => {
            console.log('[Lista Preço] Response text:', text.substring(0, 200));
            try {
                const data = JSON.parse(text);
                console.log('[Lista Preço] Dados recebidos:', data);
                if (data.preco !== undefined) {
                    // Se a lista é do tipo desconto, mostrar o desconto no campo apropriado
                    if (data.tipo === 'desconto' && data.percentual > 0 && data.preco_original) {
                        // Manter preço original no Preço Lista
                        document.getElementById('item_preco_lista').value = data.preco_original.toFixed(2);
                        // Mostrar percentual de desconto
                        document.getElementById('item_perc_desconto').value = data.percentual;
                        // Preço unitário já com desconto
                        document.getElementById('item_preco_unitario').value = data.preco.toFixed(2);
                        console.log('[Lista Preço] Desconto aplicado:', data.percentual, '%');
                    } else {
                        // Para outros tipos (fixo, markup), atualiza o preço diretamente
                        document.getElementById('item_preco_lista').value = data.preco.toFixed(2);
                        document.getElementById('item_preco_unitario').value = data.preco.toFixed(2);
                        document.getElementById('item_perc_desconto').value = '0';
                    }
                    calcularItemTotal();
                    console.log('[Lista Preço] Preço aplicado:', data.preco);
                } else if (data.error) {
                    console.error('[Lista Preço] Erro:', data.error);
                }
            } catch(e) {
                console.error('[Lista Preço] Resposta não é JSON:', e);
            }
        })
        .catch(err => {
            console.error('[Lista Preço] Erro ao buscar preço:', err);
        });
}

function renderizarItens() {
    const tbody = document.getElementById('tbodyItens');
    if (!tbody) return;
    
    if (itensOrcamento.length === 0) {
        tbody.innerHTML = '<tr id="semItens"><td colspan="9" class="text-center text-muted py-4">Nenhum item adicionado</td></tr>';
        return;
    }
    
    let html = '';
    itensOrcamento.forEach((item, index) => {
        const formatNum = (n) => (n || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        const nome = item.produto_nome || '';
        
        html += `<tr data-id="${item.id}" 
                     data-produto-id="${item.produto_id}"
                     data-codigo="${item.produto_codigo || ''}"
                     data-nome="${nome}"
                     data-unidade="${item.unidade || 'UN'}"
                     data-quantidade="${item.quantidade || 0}"
                     data-preco-lista="${item.preco_lista || 0}"
                     data-desconto="${item.percentual_desconto || 0}"
                     data-preco-unitario="${item.preco_unitario || 0}"
                     data-valor-total="${item.valor_total || 0}">
            <td>${item.produto_codigo}</td>
            <td title="${nome}">${nome.substring(0, 40)}${nome.length > 40 ? '...' : ''}</td>
            <td class="text-center">${item.unidade}</td>
            <td class="text-end">${formatNum(item.quantidade)}</td>
            <td class="text-end">${formatNum(item.preco_lista)}</td>
            <td class="text-end">${formatNum(item.percentual_desconto)}</td>
            <td class="text-end">${formatNum(item.preco_unitario)}</td>
            <td class="text-end fw-bold">${formatNum(item.valor_total)}</td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-outline-primary py-0 px-1" onclick="editarItem(this)" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger py-0 px-1" onclick="removerItemPorId('${item.id}')" title="Remover">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        </tr>`;
    });
    tbody.innerHTML = html;
    
    const resumoEl = document.getElementById('resumo_qtd_itens');
    if (resumoEl) resumoEl.textContent = itensOrcamento.length;
}

function limparCamposItem() {
    document.getElementById('produto_id').value = '';
    document.getElementById('produto_codigo').value = '';
    document.getElementById('produto_nome').value = '';
    document.getElementById('item_unidade').value = 'UN';
    document.getElementById('item_quantidade').value = '1';
    document.getElementById('item_preco_lista').value = '0.00';
    document.getElementById('item_perc_desconto').value = '0';
    document.getElementById('item_preco_unitario').value = '0.00';
    document.getElementById('item_subtotal').value = '0,00';
    if (document.getElementById('item_observacao')) {
        document.getElementById('item_observacao').value = '';
    }
}

// =====================================================
// TOTAIS
// =====================================================
function calcularTotais() {
    let totalProdutos = 0;
    itensOrcamento.forEach(item => {
        totalProdutos += parseFloat(item.valor_total) || 0;
    });
    
    const frete = parseFloat(document.getElementById('valor_frete')?.value) || 0;
    const percDesconto = parseFloat(document.getElementById('percentual_desconto')?.value) || 0;
    
    const valorDesconto = totalProdutos * (percDesconto / 100);
    const totalDocumento = totalProdutos - valorDesconto + frete;
    
    // Atualizar campos na aba Dados
    const totalProdutosEl = document.getElementById('total_produtos');
    const totalDocumentoEl = document.getElementById('total_documento');
    
    if (totalProdutosEl) totalProdutosEl.value = totalProdutos.toLocaleString('pt-BR', {minimumFractionDigits: 2});
    if (totalDocumentoEl) totalDocumentoEl.value = totalDocumento.toLocaleString('pt-BR', {minimumFractionDigits: 2});
    
    // Resumo na aba de itens
    const resumoQtd = document.getElementById('resumo_qtd_itens');
    const resumoTotal = document.getElementById('resumo_total_produtos');
    const resumoComImpostos = document.getElementById('resumo_total_com_impostos');
    
    if (resumoQtd) resumoQtd.textContent = itensOrcamento.length;
    if (resumoTotal) resumoTotal.textContent = totalProdutos.toLocaleString('pt-BR', {minimumFractionDigits: 2});
    if (resumoComImpostos) resumoComImpostos.textContent = totalDocumento.toLocaleString('pt-BR', {minimumFractionDigits: 2});
    
    // Atualizar valor na aba de pagamento
    atualizarResumoPagamento(totalDocumento);
    
    // Comissao
    calcularComissoes(totalDocumento);
}

// =====================================================
// FORMA DE PAGAMENTO - PARCELAS
// =====================================================
function atualizarParcelas() {
    const selectPagamento = document.getElementById('forma_pagamento_id');
    const selectParcelas = document.getElementById('num_parcelas');
    const inputDias = document.getElementById('dias_primeira_parcela');
    
    if (!selectPagamento || !selectParcelas) return;
    
    const option = selectPagamento.options[selectPagamento.selectedIndex];
    if (!option || !option.value) {
        // Limpar parcelas
        selectParcelas.innerHTML = '<option value="1">1x</option>';
        if (inputDias) inputDias.value = 0;
        return;
    }
    
    const maxParcelas = parseInt(option.dataset.maxParcelas) || 1;
    const diasReceber = parseInt(option.dataset.diasReceber) || 0;
    const diasEntre = parseInt(option.dataset.diasEntre) || 30;
    
    // Popular select de parcelas
    selectParcelas.innerHTML = '';
    for (let i = 1; i <= maxParcelas; i++) {
        const opt = document.createElement('option');
        opt.value = i;
        opt.text = `${i}x`;
        selectParcelas.appendChild(opt);
    }
    
    // Definir dias da primeira parcela
    if (inputDias) {
        inputDias.value = diasReceber;
    }
    
    // Sincronizar com aba de Pagamento
    sincronizarFormaPagamentoAbas(option, maxParcelas, diasReceber, diasEntre);
    
    console.log(`Forma pagamento: max ${maxParcelas}x, ${diasReceber} dias p/ receber, ${diasEntre} dias entre`);
}

function sincronizarFormaPagamentoAbas(option, maxParcelas, diasReceber, diasEntre) {
    // Atualizar campo na aba Pagamento
    const pagamentoNome = document.getElementById('pagamento_nome');
    const pagamentoParcelas = document.getElementById('pagamento_parcelas');
    const pagamentoDiasInicio = document.getElementById('pagamento_dias_inicio');
    const pagamentoIntervalo = document.getElementById('pagamento_intervalo');
    const pagamentoMethodId = document.getElementById('pagamento_method_id');
    
    if (pagamentoNome && option) {
        pagamentoNome.value = option.text || '';
    }
    
    if (pagamentoMethodId && option) {
        pagamentoMethodId.value = option.value || '';
    }
    
    // Popular select de parcelas na aba Pagamento
    if (pagamentoParcelas) {
        pagamentoParcelas.innerHTML = '';
        for (let i = 1; i <= maxParcelas; i++) {
            const opt = document.createElement('option');
            opt.value = i;
            opt.text = `${i}x`;
            pagamentoParcelas.appendChild(opt);
        }
    }
    
    // Definir dias na aba Pagamento
    if (pagamentoDiasInicio) {
        pagamentoDiasInicio.value = diasReceber;
    }
    
    if (pagamentoIntervalo) {
        pagamentoIntervalo.value = diasEntre;
    }
    
    // Atualizar formaPagamentoSelecionada (usado pela aba pagamento)
    if (option && option.value) {
        formaPagamentoSelecionada = {
            id: option.value,
            nome: option.text,
            maxParcelas: maxParcelas,
            diasReceber: diasReceber,
            diasEntre: diasEntre
        };
    }
    
    // Atualizar valor total
    atualizarValorTotalPagamento();
}

// =====================================================
// COMISSAO
// =====================================================
function calcularComissoes(totalOrcamentoParam) {
    // Se não foi passado o total, pegar do valor total do orçamento
    let totalOrcamento = totalOrcamentoParam;
    if (totalOrcamento === undefined || totalOrcamento === null) {
        // Tentar pegar do resumo de itens (principal)
        let valorTotalEl = document.getElementById('resumo_total_com_impostos');
        if (valorTotalEl) {
            totalOrcamento = parseFloat(valorTotalEl.textContent?.replace(/[^\d,.-]/g, '').replace(',', '.')) || 0;
        }
        
        // Se não encontrou, tentar do campo de pagamento
        if (!totalOrcamento || totalOrcamento === 0) {
            valorTotalEl = document.getElementById('pagamento_valor_total');
            if (valorTotalEl) {
                totalOrcamento = parseFloat(valorTotalEl.value?.replace(/[^\d,.-]/g, '').replace(',', '.')) || 0;
            }
        }
        
        // Se não encontrou, tentar calcular da lista de itens
        if ((!totalOrcamento || totalOrcamento === 0) && typeof itensOrcamento !== 'undefined') {
            totalOrcamento = itensOrcamento.reduce((sum, item) => sum + (item.valor_total || 0), 0);
        }
        
        console.log(`[Comissao] Total do orcamento: R$ ${totalOrcamento.toFixed(2)}`);
    }
    
    const aliquotaV1 = parseFloat(document.getElementById('comissao_vendedor1_aliquota')?.value) || 0;
    const aliquotaV2 = parseFloat(document.getElementById('comissao_vendedor2_aliquota')?.value) || 0;
    const aliquotaV3 = parseFloat(document.getElementById('comissao_vendedor3_aliquota')?.value) || 0;
    const aliquotaV4 = parseFloat(document.getElementById('comissao_vendedor4_aliquota')?.value) || 0;
    
    const valorV1 = totalOrcamento * (aliquotaV1 / 100);
    const valorV2 = totalOrcamento * (aliquotaV2 / 100);
    const valorV3 = totalOrcamento * (aliquotaV3 / 100);
    const valorV4 = totalOrcamento * (aliquotaV4 / 100);
    
    const formatMoney = (val) => 'R$ ' + val.toLocaleString('pt-BR', {minimumFractionDigits: 2});
    
    // Atualizar exibição
    const elTotal = document.getElementById('comissao_total_orcamento');
    const elV1 = document.getElementById('comissao_valor_v1');
    const elV2 = document.getElementById('comissao_valor_v2');
    const elV3 = document.getElementById('comissao_valor_v3');
    const elV4 = document.getElementById('comissao_valor_v4');
    const elTotalCom = document.getElementById('comissao_total');
    
    if (elTotal) elTotal.textContent = formatMoney(totalOrcamento);
    if (elV1) elV1.textContent = formatMoney(valorV1);
    if (elV2) elV2.textContent = formatMoney(valorV2);
    if (elV3) elV3.textContent = formatMoney(valorV3);
    if (elV4) elV4.textContent = formatMoney(valorV4);
    if (elTotalCom) elTotalCom.textContent = formatMoney(valorV1 + valorV2 + valorV3 + valorV4);
    
    // Atualizar campos hidden para enviar no formulário
    const hiddenV1 = document.getElementById('comissao_valor_v1_hidden');
    const hiddenV2 = document.getElementById('comissao_valor_v2_hidden');
    if (hiddenV1) hiddenV1.value = valorV1.toFixed(2);
    if (hiddenV2) hiddenV2.value = valorV2.toFixed(2);
}

/**
 * Sincroniza o vendedor 1 selecionado na aba Dados com a aba de Comissão
 * e busca a comissão padrão do vendedor
 * @param {boolean} forceUpdate - Se true, sempre atualiza a comissão
 */
function sincronizarVendedorComissao(forceUpdate = false) {
    const select = document.getElementById('vendedor_id');
    const nomeField = document.getElementById('comissao_vendedor1_nome');
    const aliquotaField = document.getElementById('comissao_vendedor1_aliquota');
    
    if (select && nomeField) {
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption && selectedOption.value) {
            nomeField.value = selectedOption.text;
            
            // Buscar comissão padrão do vendedor
            // forceUpdate=true quando muda o vendedor manualmente
            buscarComissaoPadraoVendedor(selectedOption.value, 1, forceUpdate);
        } else {
            nomeField.value = '';
            if (aliquotaField) aliquotaField.value = '0.00';
        }
    }
}

/**
 * Sincroniza o vendedor 2 selecionado na aba Dados com a aba de Comissão
 * e busca a comissão padrão do vendedor
 * @param {boolean} forceUpdate - Se true, sempre atualiza a comissão
 */
function sincronizarVendedor2Comissao(forceUpdate = false) {
    const select = document.getElementById('vendedor2_id');
    const nomeField = document.getElementById('comissao_vendedor2_nome');
    const aliquotaField = document.getElementById('comissao_vendedor2_aliquota');
    
    if (select && nomeField) {
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption && selectedOption.value) {
            nomeField.value = selectedOption.text;
            
            // Buscar comissão padrão do vendedor
            // forceUpdate=true quando muda o vendedor manualmente
            buscarComissaoPadraoVendedor(selectedOption.value, 2, forceUpdate);
        } else {
            nomeField.value = '';
            if (aliquotaField) aliquotaField.value = '0.00';
        }
    }
}

/**
 * Busca a comissão padrão do vendedor via API
 * @param {string|number} vendedorId - ID do vendedor
 * @param {number} numeroVendedor - Número do vendedor (1 ou 2)
 * @param {boolean} forceUpdate - Se true, sempre atualiza (default: false)
 */
function buscarComissaoPadraoVendedor(vendedorId, numeroVendedor, forceUpdate = false) {
    if (!vendedorId) {
        console.log(`[Comissao] Vendedor ${numeroVendedor}: ID vazio, ignorando`);
        return;
    }
    
    console.log(`[Comissao] Buscando comissao do vendedor ID=${vendedorId}...`);
    
    fetch(`/orcamentos/api/vendedor/${vendedorId}/comissao`)
        .then(response => response.json())
        .then(data => {
            console.log(`[Comissao] Resposta API:`, data);
            
            if (data.error) {
                console.log('[Comissao] Erro na API:', data.error);
                return;
            }
            
            const comissaoPadrao = data.comissao_padrao || 0;
            const aliquotaField = document.getElementById(`comissao_vendedor${numeroVendedor}_aliquota`);
            
            console.log(`[Comissao] Vendedor ${numeroVendedor}: comissao=${comissaoPadrao}%, campo existe=${!!aliquotaField}`);
            
            if (aliquotaField) {
                const valorAtual = parseFloat(aliquotaField.value) || 0;
                console.log(`[Comissao] Valor atual no campo: ${valorAtual}`);
                
                // Preenche se forceUpdate ou se o campo estiver zerado
                if (forceUpdate || valorAtual === 0) {
                    aliquotaField.value = comissaoPadrao.toFixed(2);
                    console.log(`[Comissao] Campo atualizado para: ${comissaoPadrao}%`);
                    calcularComissoes();
                } else {
                    console.log(`[Comissao] Campo nao atualizado (valor atual: ${valorAtual})`);
                }
            }
        })
        .catch(err => {
            console.error('[Comissao] Erro ao buscar:', err);
        });
}

// =====================================================
// DUPLICATAS
// =====================================================
function adicionarParcela() {
    alert('Funcionalidade de adicionar parcela em desenvolvimento.');
}

function reiniciarParcelas() {
    duplicatasOrcamento = [];
    document.getElementById('tbodyDuplicatas').innerHTML = '';
}

// =====================================================
// FORMA DE PAGAMENTO
// =====================================================
let formaPagamentoSelecionada = null;

function abrirModalFormaPagamento() {
    const modal = new bootstrap.Modal(document.getElementById('modalFormaPagamento'));
    modal.show();
}

function selecionarFormaPagamento(elemento) {
    // Obter dados do elemento clicado
    const id = elemento.dataset.id;
    const nome = elemento.dataset.nome;
    const maxParcelas = parseInt(elemento.dataset.maxParcelas) || 1;
    const diasEntre = parseInt(elemento.dataset.diasEntre) || 30;
    const diasReceber = parseInt(elemento.dataset.diasReceber) || 0;
    const geraBoleto = elemento.dataset.geraBoleto === '1' || elemento.dataset.geraBoleto === 'True';
    
    console.log('[Forma Pagamento] Selecionada:', id, nome, 'Max parcelas:', maxParcelas);
    
    // Salvar dados
    formaPagamentoSelecionada = {
        id: id,
        nome: nome,
        maxParcelas: maxParcelas,
        diasEntre: diasEntre,
        diasReceber: diasReceber,
        geraBoleto: geraBoleto
    };
    
    // Preencher campos
    document.getElementById('pagamento_nome').value = nome;
    document.getElementById('pagamento_method_id').value = id;
    
    // Atualizar select de parcelas
    const selectParcelas = document.getElementById('pagamento_parcelas');
    if (selectParcelas) {
        selectParcelas.innerHTML = '';
        for (let i = 1; i <= maxParcelas; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = i + 'x';
            selectParcelas.appendChild(option);
        }
    }
    
    // Atualizar intervalo padrão
    const intervaloEl = document.getElementById('pagamento_intervalo');
    if (intervaloEl) {
        intervaloEl.value = diasEntre;
    }
    
    // Dias para receber (primeira parcela)
    const diasInicioEl = document.getElementById('pagamento_dias_inicio');
    if (diasInicioEl) {
        diasInicioEl.value = diasReceber;
    }
    
    // Fechar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalFormaPagamento'));
    if (modal) modal.hide();
    
    // Gerar parcelas automaticamente
    setTimeout(() => gerarParcelasPagamento(), 100);
}

function gerarParcelasPagamento() {
    const formaPagamentoId = document.getElementById('pagamento_method_id')?.value;
    if (!formaPagamentoId) {
        alert('Selecione uma forma de pagamento primeiro.');
        return;
    }
    
    const parcelas = parseInt(document.getElementById('pagamento_parcelas')?.value) || 1;
    const diasInicio = parseInt(document.getElementById('pagamento_dias_inicio')?.value) || 0;
    const intervalo = parseInt(document.getElementById('pagamento_intervalo')?.value) || 30;
    
    // Calcular valor total do orçamento
    let valorTotal = 0;
    itensOrcamento.forEach(item => {
        valorTotal += parseFloat(item.valor_total) || 0;
    });
    
    if (valorTotal <= 0) {
        alert('Adicione itens ao orçamento primeiro.');
        return;
    }
    
    const valorParcela = valorTotal / parcelas;
    const hoje = new Date();
    
    // Limpar parcelas existentes
    duplicatasOrcamento = [];
    
    // Gerar parcelas
    for (let i = 1; i <= parcelas; i++) {
        const diasVencimento = diasInicio + ((i - 1) * intervalo);
        const dataVencimento = new Date(hoje);
        dataVencimento.setDate(dataVencimento.getDate() + diasVencimento);
        
        duplicatasOrcamento.push({
            numero: i,
            vencimento: dataVencimento.toISOString().split('T')[0],
            valor: valorParcela,
            forma_pagamento: formaPagamentoSelecionada?.nome || 'N/A',
            forma_pagamento_id: formaPagamentoId,
            status: 'pendente'
        });
    }
    
    // Renderizar parcelas
    renderizarParcelasPagamento();
    
    // Atualizar resumo
    atualizarResumoPagamento(valorTotal);
}

function renderizarParcelasPagamento() {
    const tbody = document.getElementById('tbodyParcelas');
    if (!tbody) {
        console.log('[Renderizar Parcelas] tbody não encontrado');
        return;
    }
    
    console.log('[Renderizar Parcelas] Total de parcelas:', duplicatasOrcamento.length);
    console.log('[Renderizar Parcelas] Dados:', JSON.stringify(duplicatasOrcamento));
    
    if (duplicatasOrcamento.length === 0) {
        tbody.innerHTML = `<tr id="semParcelas">
            <td colspan="6" class="text-center text-muted py-3">
                <i class="fas fa-info-circle me-1"></i> Selecione uma forma de pagamento e clique em "Gerar Parcelas"
            </td>
        </tr>`;
        return;
    }
    
    // Atualizar select de parcelas
    const selectParcelas = document.getElementById('pagamento_parcelas');
    if (selectParcelas) {
        selectParcelas.value = duplicatasOrcamento.length;
    }
    
    let html = '';
    let total = 0;
    
    duplicatasOrcamento.forEach((parcela, index) => {
        const valorNum = parseFloat(parcela.valor) || 0;
        total += valorNum;
        const dataFormatada = new Date(parcela.vencimento + 'T00:00:00').toLocaleDateString('pt-BR');
        const valorFormatado = valorNum.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        
        html += `<tr data-index="${index}">
            <td class="text-center">${parcela.numero}/${duplicatasOrcamento.length}</td>
            <td class="text-center">${dataFormatada}</td>
            <td class="text-end">${valorFormatado}</td>
            <td>${parcela.forma_pagamento}</td>
            <td class="text-center"><span class="badge bg-warning">Pendente</span></td>
            <td class="text-center">
                <button type="button" class="btn btn-outline-danger btn-sm py-0 px-1" onclick="removerParcela(${index})" title="Remover">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>`;
    });
    
    tbody.innerHTML = html;
    
    // Atualizar total
    const totalEl = document.getElementById('totalParcelas');
    if (totalEl) {
        totalEl.textContent = total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }
}

function removerParcela(index) {
    duplicatasOrcamento.splice(index, 1);
    // Renumerar
    duplicatasOrcamento.forEach((p, i) => p.numero = i + 1);
    renderizarParcelasPagamento();
}

function atualizarResumoPagamento(valorTotal) {
    let totalParcelado = 0;
    duplicatasOrcamento.forEach(p => totalParcelado += p.valor);
    
    const diferenca = valorTotal - totalParcelado;
    
    const totalOrcEl = document.getElementById('resumo_total_orcamento');
    const totalParcEl = document.getElementById('resumo_total_parcelado');
    const diferencaEl = document.getElementById('resumo_diferenca');
    const valorTotalEl = document.getElementById('pagamento_valor_total');
    
    if (totalOrcEl) totalOrcEl.textContent = valorTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    if (totalParcEl) totalParcEl.textContent = totalParcelado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    if (valorTotalEl) valorTotalEl.value = valorTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    
    if (diferencaEl) {
        diferencaEl.textContent = diferenca.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        diferencaEl.className = diferenca === 0 ? 'badge bg-success' : 'badge bg-danger';
    }
}

function atualizarValorTotalPagamento() {
    // Calcular total do orçamento
    let totalProdutos = 0;
    itensOrcamento.forEach(item => {
        totalProdutos += parseFloat(item.valor_total) || 0;
    });
    
    const frete = parseFloat(document.getElementById('valor_frete')?.value) || 0;
    const percDesconto = parseFloat(document.getElementById('percentual_desconto')?.value) || 0;
    const valorDesconto = totalProdutos * (percDesconto / 100);
    const totalDocumento = totalProdutos - valorDesconto + frete;
    
    // Atualizar na aba de pagamento
    atualizarResumoPagamento(totalDocumento);
}

function calcularParcelasPagamento() {
    // Recalcular quando mudar parcelas ou intervalo
    if (formaPagamentoSelecionada) {
        gerarParcelasPagamento();
    }
}

function carregarFormaPagamentoExistente() {
    // Verificar se há uma forma de pagamento já selecionada (modo edição)
    const pagamentoId = document.getElementById('pagamento_method_id')?.value;
    const pagamentoNome = document.getElementById('pagamento_nome')?.value;
    
    if (pagamentoId && pagamentoId !== '' && pagamentoId !== 'None') {
        console.log('[Forma Pagamento] Carregando existente:', pagamentoId, pagamentoNome);
        
        // Buscar dados da forma de pagamento no modal
        const modalItem = document.querySelector(`#modalFormaPagamento .forma-pagamento-item[data-id="${pagamentoId}"]`);
        
        if (modalItem) {
            // Preencher variável global com dados do modal
            formaPagamentoSelecionada = {
                id: pagamentoId,
                nome: modalItem.dataset.nome || pagamentoNome,
                maxParcelas: parseInt(modalItem.dataset.maxParcelas) || 1,
                diasEntre: parseInt(modalItem.dataset.diasEntre) || 30,
                diasReceber: parseInt(modalItem.dataset.diasReceber) || 0,
                geraBoleto: modalItem.dataset.geraBoleto === '1'
            };
            
            // Atualizar select de parcelas
            const selectParcelas = document.getElementById('pagamento_parcelas');
            if (selectParcelas) {
                selectParcelas.innerHTML = '';
                for (let i = 1; i <= formaPagamentoSelecionada.maxParcelas; i++) {
                    const option = document.createElement('option');
                    option.value = i;
                    option.textContent = i + 'x';
                    selectParcelas.appendChild(option);
                }
            }
            
            console.log('[Forma Pagamento] Dados carregados:', formaPagamentoSelecionada);
        } else {
            // Se não achou no modal, criar objeto básico
            formaPagamentoSelecionada = {
                id: pagamentoId,
                nome: pagamentoNome || 'N/A',
                maxParcelas: 12,
                diasEntre: 30,
                diasReceber: 0,
                geraBoleto: false
            };
            console.log('[Forma Pagamento] Usando dados básicos:', formaPagamentoSelecionada);
        }
    }
}

// =====================================================
// CRM
// =====================================================
function novoHistoricoCRM() {
    const modal = new bootstrap.Modal(document.getElementById('modalNovoHistorico'));
    modal.show();
}

function salvarHistoricoCRM() {
    alert('Historico CRM salvo!');
    bootstrap.Modal.getInstance(document.getElementById('modalNovoHistorico')).hide();
}

function imprimirCRM() {
    window.print();
}

function editarEventoCRM() {
    alert('Funcionalidade de edicao em desenvolvimento.');
}

// =====================================================
// CARREGAR ITENS EXISTENTES
// =====================================================
function carregarItensExistentes() {
    const tbody = document.getElementById('tbodyItens');
    if (!tbody) return;
    
    // Se ja tem itens renderizados no HTML (edicao)
    const rows = tbody.querySelectorAll('tr[data-id]');
    console.log('[Carregar Itens] Encontrados:', rows.length, 'itens');
    
    rows.forEach(row => {
        // Preferir data-attributes, fallback para texto das células
        const item = {
            id: row.dataset.id,
            produto_id: row.dataset.produtoId,
            produto_codigo: row.dataset.codigo || row.cells[0]?.textContent?.trim() || '',
            produto_nome: row.dataset.nome || row.cells[1]?.textContent?.trim() || '',
            unidade: row.dataset.unidade || row.cells[2]?.textContent?.trim() || 'UN',
            quantidade: parseFloat(row.dataset.quantidade) || parseFloat(row.cells[3]?.textContent?.replace(',', '.')) || 0,
            preco_lista: parseFloat(row.dataset.precoLista) || parseFloat(row.cells[4]?.textContent?.replace(',', '.')) || 0,
            percentual_desconto: parseFloat(row.dataset.desconto) || parseFloat(row.cells[5]?.textContent?.replace(',', '.')) || 0,
            preco_unitario: parseFloat(row.dataset.precoUnitario) || parseFloat(row.cells[6]?.textContent?.replace(',', '.')) || 0,
            valor_total: parseFloat(row.dataset.valorTotal) || parseFloat(row.cells[7]?.textContent?.replace(',', '.')) || 0
        };
        console.log('[Carregar Itens] Item:', item);
        itensOrcamento.push(item);
    });
    
    if (itensOrcamento.length > 0) {
        calcularTotais();
    }
}

// =====================================================
// PREPARAR ENVIO DO FORMULARIO
// =====================================================
function prepararEnvio(e) {
    // Atualizar JSON de itens
    document.getElementById('itens_json').value = JSON.stringify(itensOrcamento);
    
    // Atualizar JSON de duplicatas
    document.getElementById('duplicatas_json').value = JSON.stringify(duplicatasOrcamento);
    document.getElementById('num_parcelas').value = duplicatasOrcamento.length || 1;
    
    // Debug: mostrar valores antes de enviar
    console.log('[Preparar Envio] pagamento_method_id:', document.getElementById('pagamento_method_id')?.value);
    console.log('[Preparar Envio] vendedor_id:', document.getElementById('vendedor_id')?.value);
    console.log('[Preparar Envio] cliente_id:', document.getElementById('cliente_id')?.value);
    console.log('[Preparar Envio] empresa_id:', document.getElementById('empresa_id')?.value);
    console.log('[Preparar Envio] duplicatas:', duplicatasOrcamento.length);
    
    let erros = [];
    
    // Validar cliente (obrigatório)
    const clienteId = document.getElementById('cliente_id')?.value;
    if (!clienteId || clienteId === '' || clienteId === 'None') {
        erros.push('• Cliente é obrigatório');
    }
    
    // Validar vendedor (obrigatório)
    const vendedorId = document.getElementById('vendedor_id')?.value;
    if (!vendedorId || vendedorId === '' || vendedorId === 'None') {
        erros.push('• Vendedor é obrigatório');
    }
    
    // Validar itens (pelo menos um)
    if (itensOrcamento.length === 0) {
        erros.push('• Adicione pelo menos um item ao orçamento');
    }
    
    // Validar forma de pagamento (obrigatório) - buscar na aba Pagamentos
    const formaPagamentoId = document.getElementById('pagamento_method_id')?.value;
    if (!formaPagamentoId || formaPagamentoId === '' || formaPagamentoId === 'None') {
        erros.push('• Forma de Pagamento é obrigatória (aba Pagamento)');
    }
    
    // Se houver erros, mostrar e impedir envio
    if (erros.length > 0) {
        e.preventDefault();
        alert('Campos obrigatórios não preenchidos:\n\n' + erros.join('\n'));
        
        // Navegar para a aba correta
        if (!clienteId || !vendedorId) {
            document.querySelector('a[href="#tabDados"]')?.click();
        } else if (itensOrcamento.length === 0) {
            document.querySelector('a[href="#tabItens"]')?.click();
        } else if (!formaPagamentoId) {
            document.querySelector('a[href="#tabDuplicatas"]')?.click();
        }
        return false;
    }
    
    return true;
}

// =====================================================
// ACOES PRINCIPAIS
// =====================================================
function salvarEFechar() {
    document.getElementById('acao_form').value = 'salvar_fechar';
    if (prepararEnvio({preventDefault: function(){}})) {
        document.getElementById('formOrcamento').submit();
    }
}

function duplicarOrcamento() {
    const id = document.querySelector('input[name="id"]').value;
    if (id && confirm('Deseja duplicar este orçamento?')) {
        // Criar form dinâmico para enviar via POST
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/orcamentos/' + id + '/duplicar';
        document.body.appendChild(form);
        form.submit();
    } else if (!id) {
        alert('Salve o orçamento primeiro antes de duplicar.');
    }
}

function gerarRevisao() {
    const id = document.querySelector('input[name="id"]').value;
    if (id) {
        window.location.href = '/orcamentos/' + id + '/revisao';
    } else {
        alert('Salve o orcamento primeiro.');
    }
}

function abrirEventosCRM() {
    const tab = document.querySelector('a[href="#tabCRM"]');
    if (tab) tab.click();
}

// Placeholder functions
function abrirGerador() { alert('Gerador em desenvolvimento.'); }
function opcoesAvancadas() { alert('Opcoes avancadas em desenvolvimento.'); }
function fecharOS() { alert('Fechar OS em desenvolvimento.'); }
function embalagens() { alert('Embalagens em desenvolvimento.'); }
function produtoDescartavel() { alert('Produto descartavel em desenvolvimento.'); }
function alterarItem() { alert('Alterar item em desenvolvimento.'); }
function ratearDesconto() { alert('Ratear desconto em desenvolvimento.'); }
function explodirEstrutura() { alert('Explodir estrutura em desenvolvimento.'); }
function subirItem() { alert('Subir item em desenvolvimento.'); }
function descerItem() { alert('Descer item em desenvolvimento.'); }
function buscarCondPagto() { alert('Buscar condicao de pagamento em desenvolvimento.'); }
function buscarTransportadora() { abrirBuscaTransportadora(); }

// =====================================================
// TRANSPORTADORA
// =====================================================
function abrirBuscaTransportadora() {
    linhaTransportadoraSelecionada = -1;
    const modalEl = document.getElementById('modalBuscaTransportadora');
    if (!modalEl) return;
    
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    
    // Limpar busca anterior
    document.getElementById('busca_transportadora_input').value = '';
    document.getElementById('tbodyTransportadoras').innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Digite para buscar...</td></tr>';
    
    // Focar quando o modal terminar de abrir
    modalEl.addEventListener('shown.bs.modal', function focaTransp() {
        document.getElementById('busca_transportadora_input').focus();
        modalEl.removeEventListener('shown.bs.modal', focaTransp);
    });
    
    modal.show();
}

function fecharModalTransportadora() {
    const modalEl = document.getElementById('modalBuscaTransportadora');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
}

function handleNavegacaoModalTransportadora(e) {
    const tbody = document.getElementById('tbodyTransportadoras');
    const rows = tbody.querySelectorAll('.transportadora-row');
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (rows.length > 0) {
            linhaTransportadoraSelecionada = Math.min(linhaTransportadoraSelecionada + 1, rows.length - 1);
            destacarLinhaTransportadora(rows);
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (rows.length > 0) {
            linhaTransportadoraSelecionada = Math.max(linhaTransportadoraSelecionada - 1, 0);
            destacarLinhaTransportadora(rows);
        }
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (linhaTransportadoraSelecionada >= 0 && rows[linhaTransportadoraSelecionada]) {
            rows[linhaTransportadoraSelecionada].click();
        } else {
            pesquisarTransportadoras();
        }
    } else if (e.key === 'Escape') {
        fecharModalTransportadora();
    }
}

function destacarLinhaTransportadora(rows) {
    rows.forEach((r, i) => {
        r.classList.toggle('table-primary', i === linhaTransportadoraSelecionada);
    });
    if (rows[linhaTransportadoraSelecionada]) {
        rows[linhaTransportadoraSelecionada].scrollIntoView({ block: 'nearest' });
    }
}

function pesquisarTransportadoras() {
    const termo = document.getElementById('busca_transportadora_input').value;
    if (termo.length < 2) {
        alert('Digite pelo menos 2 caracteres para buscar.');
        return;
    }
    
    const tbody = document.getElementById('tbodyTransportadoras');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Buscando...</td></tr>';
    
    fetch(`/orcamentos/api/buscar-transportadoras?q=${encodeURIComponent(termo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Nenhuma transportadora encontrada.</td></tr>';
                return;
            }
            
            linhaTransportadoraSelecionada = -1;
            let html = '';
            data.forEach(t => {
                const nome = t.nome || t.name || '';
                const doc = t.documento || t.cnpj || t.cpf || '';
                const cidade = t.cidade || t.city || '';
                const estado = t.estado || t.state || '';
                
                html += `<tr style="cursor:pointer" class="transportadora-row" 
                            data-id="${t.id}" 
                            data-nome="${nome.replace(/"/g, '&quot;')}" 
                            data-documento="${doc}"
                            data-cidade="${cidade}"
                            data-estado="${estado}">
                    <td>${t.id}</td>
                    <td>${nome}</td>
                    <td>${doc}</td>
                    <td>${cidade}</td>
                    <td>${estado}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
            
            // Adicionar eventos de clique
            tbody.querySelectorAll('.transportadora-row').forEach(row => {
                row.addEventListener('click', function() {
                    selecionarTransportadora(
                        this.dataset.id,
                        this.dataset.nome,
                        this.dataset.documento,
                        this.dataset.cidade,
                        this.dataset.estado
                    );
                });
            });
        })
        .catch(err => {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-3">Erro ao buscar transportadoras.</td></tr>';
            console.error(err);
        });
}

function selecionarTransportadora(id, nome, documento, cidade, estado) {
    document.getElementById('transportadora_id').value = id;
    document.getElementById('transportadora_codigo').value = id;
    document.getElementById('transportadora_nome').value = nome;
    
    // Preencher campos básicos
    const docEl = document.getElementById('transp_documento');
    if (docEl) docEl.value = documento || '';
    
    const cidadeEl = document.getElementById('transp_cidade');
    if (cidadeEl) cidadeEl.value = cidade ? `${cidade}/${estado}` : '';
    
    // Buscar dados completos via API
    fetch(`/transportadoras/api/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) return;
            
            // Preencher CNPJ/CPF
            const doc = data.cnpj || data.cpf || '';
            if (docEl) docEl.value = doc;
            
            // Preencher IE
            const ieEl = document.getElementById('transp_ie');
            if (ieEl) ieEl.value = data.inscricao_estadual || '';
            
            // Preencher endereço completo
            const enderecoEl = document.getElementById('transp_endereco');
            if (enderecoEl) {
                let endereco = data.endereco || '';
                if (data.numero) endereco += ', ' + data.numero;
                if (data.bairro) endereco += ' - ' + data.bairro;
                enderecoEl.value = endereco;
            }
            
            // Cidade/UF
            if (cidadeEl && data.cidade) {
                cidadeEl.value = `${data.cidade}/${data.estado || ''}`;
            }
        })
        .catch(err => console.error('[Transportadora] Erro ao buscar dados:', err));
    
    // Fechar modal
    fecharModalTransportadora();
}
function calcularPesos() { alert('Calcular pesos em desenvolvimento.'); }
function aplicarHistorico() { alert('Aplicar historico em desenvolvimento.'); }
function somarHistorico() { alert('Somar historico em desenvolvimento.'); }

function buscarEndereco() { alert('Buscar endereco em desenvolvimento.'); }
function adicionarComissionado() { alert('Adicionar comissionado em desenvolvimento.'); }
function removerComissionado() { alert('Remover comissionado em desenvolvimento.'); }
function removerItemSelecionado() { alert('Remover item selecionado em desenvolvimento.'); }

// =====================================================
// FUNCOES DA ABA OUTROS (INSUMOS/TEMPLATE)
// =====================================================

/**
 * Carrega os itens do orçamento no select de insumos
 */
function carregarInsumosItens() {
    const select = document.getElementById('select_item_insumos');
    if (!select) return;
    
    // Limpar opções
    select.innerHTML = '<option value="">-- Selecione um item do orçamento --</option>';
    
    // Preencher com itens do orçamento
    if (typeof itensOrcamento !== 'undefined' && itensOrcamento.length > 0) {
        itensOrcamento.forEach((item, index) => {
            const option = document.createElement('option');
            option.value = item.produto_id || index;
            option.textContent = `${item.codigo || item.produto_id} - ${item.descricao || item.nome} (Qtd: ${item.quantidade || 1})`;
            option.dataset.index = index;
            option.dataset.quantidade = item.quantidade || 1;
            select.appendChild(option);
        });
    }
}

/**
 * Carrega os insumos de um produto específico (do template de produção)
 * Multiplica as quantidades e custos pela quantidade do orçamento
 */
function carregarInsumosItem(produtoId) {
    const msgSemTemplate = document.getElementById('msgSemTemplate');
    const secaoServicos = document.getElementById('secaoServicos');
    const secaoMateriasPrimas = document.getElementById('secaoMateriasPrimas');
    const secaoConsumoInterno = document.getElementById('secaoConsumoInterno');
    const badgeStatus = document.getElementById('badge_template_status');
    
    // Obter quantidade do item selecionado no orçamento
    const select = document.getElementById('select_item_insumos');
    const selectedOption = select?.options[select.selectedIndex];
    const quantidadeOrcamento = parseFloat(selectedOption?.dataset?.quantidade) || 1;
    
    // Esconder todas as seções
    if (msgSemTemplate) msgSemTemplate.style.display = 'block';
    if (secaoServicos) secaoServicos.style.display = 'none';
    if (secaoMateriasPrimas) secaoMateriasPrimas.style.display = 'none';
    if (secaoConsumoInterno) secaoConsumoInterno.style.display = 'none';
    
    if (!produtoId) {
        if (badgeStatus) {
            badgeStatus.className = 'badge bg-secondary';
            badgeStatus.textContent = 'Sem ficha técnica';
        }
        limparResumoTemplate();
        return;
    }
    
    // Loading
    if (msgSemTemplate) {
        msgSemTemplate.innerHTML = `<i class="fas fa-spinner fa-spin fa-2x mb-2"></i><br>Carregando ficha técnica...`;
    }
    
    // Buscar template do produto via API
    fetch(`/orcamentos/api/produto/${produtoId}/insumos`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('[Template] Erro:', data.error);
                if (msgSemTemplate) {
                    msgSemTemplate.innerHTML = `<i class="fas fa-exclamation-triangle fa-2x mb-2 text-danger"></i><br>Erro ao carregar ficha técnica`;
                }
                return;
            }
            
            // Verificar se tem template
            if (!data.template) {
                if (msgSemTemplate) {
                    msgSemTemplate.innerHTML = `<i class="fas fa-box-open fa-2x mb-2 text-secondary"></i><br>Este produto não possui ficha técnica cadastrada`;
                }
                if (badgeStatus) {
                    badgeStatus.className = 'badge bg-warning';
                    badgeStatus.textContent = 'Sem ficha técnica';
                }
                limparResumoTemplate();
                return;
            }
            
            // Tem template!
            if (msgSemTemplate) msgSemTemplate.style.display = 'none';
            if (badgeStatus) {
                badgeStatus.className = 'badge bg-success';
                badgeStatus.textContent = 'Ficha técnica encontrada';
            }
            
            // Preencher info do template
            const infoNome = document.getElementById('infoTemplateNome');
            const infoCusto = document.getElementById('infoTemplateCusto');
            const infoTempo = document.getElementById('infoTemplateTempo');
            if (infoNome) infoNome.value = data.template.nome || '';
            if (infoCusto) infoCusto.value = formatarMoeda(data.template.custo_base || 0);
            if (infoTempo) infoTempo.value = (data.template.tempo_horas || 0) + 'h';
            
            // Renderizar serviços (multiplicando pela quantidade do orçamento)
            if (data.servicos && data.servicos.length > 0) {
                renderizarItensTemplate('tbodyServicos', data.servicos, quantidadeOrcamento);
                if (secaoServicos) secaoServicos.style.display = 'block';
            }
            
            // Renderizar matérias primas
            if (data.materias_primas && data.materias_primas.length > 0) {
                renderizarItensTemplate('tbodyMateriasPrimas', data.materias_primas, quantidadeOrcamento);
                if (secaoMateriasPrimas) secaoMateriasPrimas.style.display = 'block';
            }
            
            // Renderizar consumo interno
            if (data.consumo_interno && data.consumo_interno.length > 0) {
                renderizarItensTemplate('tbodyConsumoInterno', data.consumo_interno, quantidadeOrcamento);
                if (secaoConsumoInterno) secaoConsumoInterno.style.display = 'block';
            }
            
            // Atualizar totais (multiplicados pela quantidade)
            const totais = data.totais || {};
            atualizarTotaisTemplate(totais, quantidadeOrcamento);
            
            // Calcular e exibir margem
            calcularMargemTemplate(totais, quantidadeOrcamento);
        })
        .catch(err => {
            console.error('[Template] Erro:', err);
            if (msgSemTemplate) {
                msgSemTemplate.innerHTML = `<i class="fas fa-exclamation-triangle fa-2x mb-2 text-danger"></i><br>Erro ao carregar ficha técnica`;
                msgSemTemplate.style.display = 'block';
            }
        });
}

/**
 * Renderiza itens do template em uma tabela
 * @param {string} tbodyId - ID do tbody
 * @param {Array} itens - Itens do template
 * @param {number} qtdOrcamento - Quantidade do orçamento para multiplicar
 */
function renderizarItensTemplate(tbodyId, itens, qtdOrcamento = 1) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    
    let html = '';
    itens.forEach(item => {
        const qtdBase = item.quantidade || 0;
        const qtdTotal = qtdBase * qtdOrcamento;
        const custoUnit = item.custo_unitario || 0;
        const custoTotal = qtdTotal * custoUnit;
        
        html += `<tr>
            <td>${item.codigo || '-'}</td>
            <td>${item.nome || item.descricao || '-'}</td>
            <td class="text-center">${qtdTotal.toFixed(2)}</td>
            <td class="text-center">${item.unidade || 'UN'}</td>
            <td class="text-end">${formatarMoeda(custoUnit)}</td>
            <td class="text-end">${formatarMoeda(custoTotal)}</td>
        </tr>`;
    });
    tbody.innerHTML = html;
}

/**
 * Atualiza os totais do template (multiplicados pela quantidade do orçamento)
 */
function atualizarTotaisTemplate(totais, qtdOrcamento = 1) {
    const totalServicos = (totais.servicos || 0) * qtdOrcamento;
    const totalMaterias = (totais.materias_primas || 0) * qtdOrcamento;
    const totalConsumo = (totais.consumo_interno || 0) * qtdOrcamento;
    const totalGeral = totalServicos + totalMaterias + totalConsumo;
    
    // Totais nas tabelas
    const elServicos = document.getElementById('totalServicos');
    const elMaterias = document.getElementById('totalMateriasPrimas');
    const elConsumo = document.getElementById('totalConsumoInterno');
    
    if (elServicos) elServicos.textContent = formatarMoeda(totalServicos);
    if (elMaterias) elMaterias.textContent = formatarMoeda(totalMaterias);
    if (elConsumo) elConsumo.textContent = formatarMoeda(totalConsumo);
    
    // Resumo lateral (também multiplicado)
    const rServicos = document.getElementById('resumoServicos');
    const rMaterias = document.getElementById('resumoMateriasPrimas');
    const rConsumo = document.getElementById('resumoConsumoInterno');
    const rTotal = document.getElementById('resumoCustoTotal');
    
    if (rServicos) rServicos.textContent = formatarMoeda(totalServicos);
    if (rMaterias) rMaterias.textContent = formatarMoeda(totalMaterias);
    if (rConsumo) rConsumo.textContent = formatarMoeda(totalConsumo);
    if (rTotal) rTotal.textContent = formatarMoeda(totalGeral);
}

/**
 * Calcula e exibe a margem de lucro baseada no custo do template e valor de venda
 */
function calcularMargemTemplate(totais, qtdOrcamento = 1) {
    const custoTotal = ((totais.servicos || 0) + (totais.materias_primas || 0) + (totais.consumo_interno || 0)) * qtdOrcamento;
    
    // Obter valor de venda do item selecionado
    const select = document.getElementById('select_item_insumos');
    const selectedOption = select?.options[select.selectedIndex];
    const itemIndex = parseInt(selectedOption?.dataset?.index);
    
    let valorVenda = 0;
    if (typeof itensOrcamento !== 'undefined' && !isNaN(itemIndex) && itensOrcamento[itemIndex]) {
        valorVenda = parseFloat(itensOrcamento[itemIndex].subtotal) || 0;
    }
    
    const valorVendaEl = document.getElementById('resumoValorVenda');
    const margemEl = document.getElementById('resumoMargem');
    
    if (valorVendaEl) {
        valorVendaEl.textContent = formatarMoeda(valorVenda);
    }
    
    if (margemEl) {
        if (valorVenda > 0) {
            const margem = ((valorVenda - custoTotal) / valorVenda) * 100;
            margemEl.textContent = margem.toFixed(1) + '%';
            margemEl.className = margem >= 20 ? 'text-success' : (margem >= 0 ? 'text-warning' : 'text-danger');
        } else {
            margemEl.textContent = '0%';
            margemEl.className = 'text-muted';
        }
    }
}

/**
 * Limpa o resumo do template
 */
function limparResumoTemplate() {
    const campos = ['totalServicos', 'totalMateriasPrimas', 'totalConsumoInterno', 
                    'resumoServicos', 'resumoMateriasPrimas', 'resumoConsumoInterno', 'resumoCustoTotal'];
    campos.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = 'R$ 0,00';
    });
    
    const infoNome = document.getElementById('infoTemplateNome');
    const infoCusto = document.getElementById('infoTemplateCusto');
    const infoTempo = document.getElementById('infoTemplateTempo');
    if (infoNome) infoNome.value = '';
    if (infoCusto) infoCusto.value = '';
    if (infoTempo) infoTempo.value = '';
}

/**
 * Formata valor para moeda BRL
 */
function formatarMoeda(valor) {
    return 'R$ ' + (valor || 0).toFixed(2).replace('.', ',');
}

/**
 * Atualiza a margem de lucro na aba Outros
 */
function atualizarMargemProduto(custoTotal) {
    const valorVendaEl = document.getElementById('resumoValorVenda');
    const margemEl = document.getElementById('resumoMargem');
    
    // Pegar valor total do orçamento
    let valorVenda = 0;
    const totalDoc = document.getElementById('total_documento');
    if (totalDoc) {
        valorVenda = parseFloat(totalDoc.value.replace(/[^\d,.-]/g, '').replace(',', '.')) || 0;
    }
    
    if (valorVendaEl) {
        valorVendaEl.textContent = 'R$ ' + valorVenda.toFixed(2).replace('.', ',');
    }
    
    if (margemEl && custoTotal > 0) {
        const margem = ((valorVenda - custoTotal) / valorVenda) * 100;
        margemEl.textContent = margem.toFixed(1) + '%';
        margemEl.className = margem >= 0 ? 'text-success' : 'text-danger';
    }
}

/**
 * Expande todos os insumos (para produtos compostos)
 */
function expandirTodosInsumos() {
    alert('Funcionalidade em desenvolvimento - expandir árvore de insumos.');
}

/**
 * Adiciona uma tag ao orçamento
 */
function adicionarTag() {
    const input = document.getElementById('inputNovaTag');
    const container = document.getElementById('containerTags');
    
    if (input && container && input.value.trim()) {
        const tag = document.createElement('span');
        tag.className = 'badge bg-secondary me-1 mb-1';
        tag.innerHTML = `${input.value.trim()} <i class="fas fa-times ms-1" style="cursor:pointer" onclick="this.parentElement.remove()"></i>`;
        container.appendChild(tag);
        input.value = '';
    }
}

// =====================================================
// FUNCOES DE CLIENTE
// =====================================================
function centralInfoCliente() {
    const clienteId = document.getElementById('cliente_id').value;
    if (!clienteId) {
        alert('Selecione um cliente primeiro.');
        return;
    }
    // Abrir modal ou redirecionar
    window.open(`/clientes/${clienteId}`, '_blank');
}

function verLimiteCredito() {
    const clienteId = document.getElementById('cliente_id').value;
    const clienteNome = document.getElementById('cliente_nome').value;
    if (!clienteId) {
        alert('Selecione um cliente primeiro.');
        return;
    }
    // Buscar limite de crédito via API
    fetch(`/api/clientes/${clienteId}/limite-credito`)
        .then(r => r.json())
        .then(data => {
            const limite = data.limite || 0;
            const usado = data.usado || 0;
            const disponivel = limite - usado;
            alert(`Cliente: ${clienteNome}\n\nLimite: R$ ${limite.toFixed(2)}\nUsado: R$ ${usado.toFixed(2)}\nDisponível: R$ ${disponivel.toFixed(2)}`);
        })
        .catch(() => {
            alert(`Limite de crédito não configurado para ${clienteNome}.`);
        });
}

function detalharCliente() {
    const clienteId = document.getElementById('cliente_id').value;
    if (!clienteId) {
        alert('Selecione um cliente primeiro.');
        return;
    }
    window.open(`/clientes/${clienteId}`, '_blank');
}

function novoCliente() {
    window.open('/clientes/novo', '_blank');
}

function abrirContatos() {
    const clienteId = document.getElementById('cliente_id').value;
    const clienteNome = document.getElementById('cliente_nome').value;
    if (!clienteId) {
        alert('Selecione um cliente primeiro para ver os contatos.');
        return;
    }
    // Buscar contatos do cliente
    fetch(`/api/clientes/${clienteId}/contatos`)
        .then(r => r.json())
        .then(data => {
            if (data.length === 0) {
                alert(`Nenhum contato cadastrado para ${clienteNome}.`);
                return;
            }
            let msg = `Contatos de ${clienteNome}:\n\n`;
            data.forEach((c, i) => {
                msg += `${i+1}. ${c.nome || 'Sem nome'}\n`;
                if (c.telefone) msg += `   Tel: ${c.telefone}\n`;
                if (c.email) msg += `   Email: ${c.email}\n`;
                if (c.cargo) msg += `   Cargo: ${c.cargo}\n`;
                msg += '\n';
            });
            alert(msg);
        })
        .catch(() => {
            alert(`Erro ao buscar contatos de ${clienteNome}. Contatos podem não estar cadastrados.`);
        });
}

// =====================================================
// INDICADOR DE ABA
// =====================================================
function atualizarIndicadorAba(numero) {
    const indicador = document.getElementById('indicadorAba');
    if (indicador) {
        const nomeAbas = ['Dados', 'Itens', 'Pagamento', 'Transporte', 'Outros', 'Comissao', 'Historico'];
        const nome = nomeAbas[numero - 1] || '';
        indicador.textContent = `Aba ${numero}/7 - ${nome}`;
    }
}

// =====================================================
// VERIFICAR ESTOQUE PRODUZIDO (DNA)
// =====================================================
/**
 * Verifica estoque produzido para o item selecionado na tabela
 * ou o item sendo adicionado (informacional)
 */
function verificarEstoqueItemSelecionado() {
    // Primeiro, verificar se há um produto sendo adicionado
    const produtoIdInput = document.getElementById('produto_id');
    const quantidadeInput = document.getElementById('item_quantidade');
    
    let produtoId = produtoIdInput?.value;
    let quantidade = parseFloat(quantidadeInput?.value) || 1;
    
    // Se não há produto no campo de adição, verificar linha selecionada na tabela
    if (!produtoId) {
        const linhasSelecionadas = document.querySelectorAll('#tbodyItens tr.table-primary, #tbodyItens tr.selected');
        if (linhasSelecionadas.length > 0) {
            const linha = linhasSelecionadas[0];
            produtoId = linha.dataset.produtoId;
            quantidade = parseFloat(linha.dataset.quantidade) || 1;
        }
    }
    
    if (!produtoId) {
        // Tentar pegar o primeiro item da tabela
        const primeiraLinha = document.querySelector('#tbodyItens tr[data-produto-id]');
        if (primeiraLinha) {
            produtoId = primeiraLinha.dataset.produtoId;
            quantidade = parseFloat(primeiraLinha.dataset.quantidade) || 1;
        }
    }
    
    if (!produtoId) {
        mostrarToast('warning', 'Selecione ou adicione um produto primeiro');
        return;
    }
    
    // Verificar se a função existe (do orcamento_dna_estoque.js)
    if (typeof window.verificarEstoqueProduzido === 'function') {
        window.verificarEstoqueProduzido(produtoId, quantidade);
    } else {
        // Fallback: chamar API diretamente
        verificarEstoqueProduzidoAPI(produtoId, quantidade);
    }
}

/**
 * Fallback para verificar estoque se o script DNA não estiver carregado
 */
async function verificarEstoqueProduzidoAPI(produtoId, quantidade) {
    try {
        const params = new URLSearchParams({ quantidade: quantidade });
        const response = await fetch(`/api/orcamento/verificar-estoque-produzido/${produtoId}?${params}`);
        const data = await response.json();
        
        if (data.success) {
            exibirModalEstoqueProduzidoSimples(data);
        } else {
            mostrarToast('warning', data.message || 'Erro ao verificar estoque');
        }
    } catch (error) {
        console.error('[ESTOQUE] Erro:', error);
        mostrarToast('danger', `Erro: ${error.message}`);
    }
}

/**
 * Modal simples para exibir estoque (fallback)
 */
function exibirModalEstoqueProduzidoSimples(dados) {
    const produto = dados.produto_solicitado || {};
    const estoque = dados.estoque_similar || [];
    const resumo = dados.resumo || {};
    
    let html = `
        <div class="modal fade" id="modalEstoqueProduzido" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title"><i class="fas fa-boxes me-2"></i>Verificar Estoque Produzido</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert ${resumo.atende_pedido ? 'alert-success' : 'alert-warning'}">
                            <strong>Produto:</strong> ${produto.nome || '-'}<br>
                            <strong>DNA:</strong> <code>${produto.codigo_dna || 'N/A'}</code><br>
                            <strong>Quantidade desejada:</strong> ${dados.quantidade_desejada}<br>
                            <strong>Total disponível:</strong> ${resumo.total_disponivel || 0}<br>
                            ${dados.mensagem || ''}
                        </div>
                        <h6>Produtos disponíveis (${estoque.length}):</h6>
                        <table class="table table-sm table-striped">
                            <thead><tr><th>Produto</th><th>DNA</th><th>Tipo</th><th class="text-end">Estoque</th></tr></thead>
                            <tbody>
    `;
    
    estoque.forEach(item => {
        html += `<tr>
            <td>${item.produto_nome}<br><small class="text-muted">${item.codigo_interno || ''}</small></td>
            <td><code>${item.codigo_dna || '-'}</code></td>
            <td><span class="badge bg-secondary">${item.tipo_match}</span></td>
            <td class="text-end fw-bold">${item.estoque_disponivel}</td>
        </tr>`;
    });
    
    html += `</tbody></table>
                    </div>
                    <div class="modal-footer">
                        <small class="text-muted me-auto"><i class="fas fa-info-circle"></i> Apenas informacional</small>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remover modal existente
    document.getElementById('modalEstoqueProduzido')?.remove();
    document.body.insertAdjacentHTML('beforeend', html);
    
    const modal = new bootstrap.Modal(document.getElementById('modalEstoqueProduzido'));
    modal.show();
}
