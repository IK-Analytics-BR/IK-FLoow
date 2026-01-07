/**
 * =====================================================
 * PDV MODERNO - JavaScript Principal
 * =====================================================
 * Features:
 * - Modal de busca de cliente (F2)
 * - Modal de busca de produto (F3)
 * - Modal de finalização (F9)
 * - Quantidade rápida (*3 + código)
 * - Cursor automático
 * - Remover item da grade
 * =====================================================
 */

// ===== VARIÁVEIS GLOBAIS =====
let quantidadeRapida = 1;
let gradeVendas = [];
let totalVenda = 0;
let pdvConfig = {}; // Configurações do PDV

// ===== CARREGAR CONFIGURAÇÕES =====
async function carregarConfiguracoes() {
    try {
        const response = await fetch('/vendas/pdv/configuracoes-api');
        const data = await response.json();
        
        if (data.success) {
            pdvConfig = data.config;
            console.log('[PDV] Configurações carregadas:', pdvConfig);
            aplicarConfiguracoes();
        }
    } catch (error) {
        console.error('[PDV] Erro ao carregar configurações:', error);
        // Usar configurações padrão
        pdvConfig = {
            require_customer: true,
            show_discount_button: true,
            enable_f2_customer: true,
            enable_f4_discount: true,
            enable_f5_cancel: true,
            enable_f6_search: true,
            enable_f9_finalize: true
        };
    }
}

function aplicarConfiguracoes() {
    console.log('[PDV] Aplicando configurações:', pdvConfig);
    
    // Ocultar botão de desconto se desabilitado
    if (!pdvConfig.show_discount_button || !pdvConfig.enable_f4_discount) {
        const btnDesconto = document.getElementById('btnDescontoItem');
        if (btnDesconto) {
            btnDesconto.style.display = 'none';
            console.log('[PDV] Botão de desconto OCULTO');
        }
    }
    
    // Ocultar botão de cliente se desabilitado
    if (!pdvConfig.enable_f2_customer) {
        const btnCliente = document.getElementById('btnCliente');
        if (btnCliente) btnCliente.style.display = 'none';
    }
    
    // Ocultar botão de cancelar se desabilitado
    if (!pdvConfig.enable_f5_cancel) {
        const btnCancelar = document.getElementById('btnCancelarItem');
        if (btnCancelar) btnCancelar.style.display = 'none';
    }
    
    // Ocultar botão de buscar se desabilitado
    if (!pdvConfig.enable_f6_search) {
        const btnBuscar = document.getElementById('btnBuscarProduto');
        if (btnBuscar) btnBuscar.style.display = 'none';
    }
    
    console.log('[PDV] Configurações aplicadas com sucesso');
}

// ===== ATALHOS DE TECLADO =====
document.addEventListener('DOMContentLoaded', async function() {
    console.log('[PDV] Sistema PDV carregado!');
    console.log('[PDV] 🔄 INICIANDO LIMPEZA TOTAL DO PDV...');
    
    // SEMPRE LIMPAR variáveis JavaScript ao abrir PDV
    gradeVendas = [];
    pagamentosLista = [];
    quantidadeRapida = 1;
    totalVenda = 0;
    console.log('[PDV] ✅ Variáveis JavaScript limpas');
    
    // FORÇAR limpeza do carrinho no servidor ao carregar página (AGUARDAR) - MÚLTIPLAS TENTATIVAS
    console.log('[PDV] 🧹 Forçando limpeza do carrinho ao carregar (Tentativa 1/3)...');
    
    for (let tentativa = 1; tentativa <= 3; tentativa++) {
        try {
            const response = await fetch('/vendas/pdv/limpar-carrinho', { 
                method: 'POST',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                console.log(`[PDV] ✅ Limpeza ${tentativa}/3 executada`);
                
                // VERIFICAR se realmente limpou
                const verificacao = await fetch('/vendas/pdv/carrinho-atual');
                const carrinhoAtual = await verificacao.json();
                const qtdItens = carrinhoAtual.carrinho?.itens?.length || 0;
                
                console.log(`[PDV] 🔍 Verificação ${tentativa}/3: ${qtdItens} itens no carrinho`);
                
                if (qtdItens === 0) {
                    console.log('[PDV] ✅✅✅ CARRINHO CONFIRMADO VAZIO!');
                    break; // Sai do loop se estiver vazio
                } else {
                    console.warn(`[PDV] ⚠️ Ainda há ${qtdItens} itens! Tentando limpar novamente...`);
                    await new Promise(resolve => setTimeout(resolve, 200)); // Aguarda 200ms
                }
            } else {
                console.error(`[PDV] ❌ Erro ao limpar (tentativa ${tentativa}):`, data);
            }
        } catch (err) {
            console.error(`[PDV] ❌ Erro ao limpar (tentativa ${tentativa}):`, err);
        }
    }
    
    // Verificação FINAL
    const verificacaoFinal = await fetch('/vendas/pdv/carrinho-atual');
    const carrinhoFinal = await verificacaoFinal.json();
    const qtdFinal = carrinhoFinal.carrinho?.itens?.length || 0;
    
    if (qtdFinal > 0) {
        console.error(`[PDV] ❌❌❌ ATENÇÃO: CARRINHO AINDA TEM ${qtdFinal} ITENS APÓS 3 TENTATIVAS!`);
        alert(`⚠️ ERRO: Carrinho não foi limpo! Há ${qtdFinal} itens residuais. Feche e reabra o PDV.`);
    } else {
        console.log('[PDV] ✅✅✅ CARRINHO TOTALMENTE LIMPO - PRONTO PARA USO!');
    }
    
    // Carregar configurações
    carregarConfiguracoes();
    
    // Configurar atalhos
    document.addEventListener('keydown', function(e) {
        // F2 - Buscar Cliente
        if (e.key === 'F2' && pdvConfig.enable_f2_customer !== false) {
            e.preventDefault();
            abrirModalCliente();
        }
        
        // F3 - Buscar Produto
        if (e.key === 'F3') {
            e.preventDefault();
            abrirModalProduto();
        }
        
        // F4 - Desconto (se habilitado)
        if (e.key === 'F4' && pdvConfig.enable_f4_discount) {
            e.preventDefault();
            // Funcionalidade de desconto
            console.log('[PDV] F4 - Desconto desabilitado ou não implementado');
        }
        
        // F5 - Cancelar (se habilitado)
        if (e.key === 'F5' && pdvConfig.enable_f5_cancel !== false) {
            e.preventDefault();
            // Funcionalidade de cancelar
            console.log('[PDV] F5 - Cancelar item');
        }
        
        // F6 - Buscar (se habilitado)
        if (e.key === 'F6' && pdvConfig.enable_f6_search !== false) {
            e.preventDefault();
            abrirModalProduto();
        }
        
        // F9 - Finalizar Venda (se habilitado)
        if (e.key === 'F9' && pdvConfig.enable_f9_finalize !== false) {
            e.preventDefault();
            finalizarVenda();
        }
        
        // ESC - Sair do PDV com confirmação
        if (e.key === 'Escape') {
            e.preventDefault();
            sairDoPDV();
        }
    });
    
    // Focar no campo de produto ao carregar
    focarProduto();
});

// ===== MODAL DE CLIENTE (F2) =====
function abrirModalCliente() {
    const modal = document.getElementById('modalBuscaCliente');
    if (!modal) {
        console.error('[PDV] Modal de cliente não encontrado');
        return;
    }
    
    const buscaInput = document.getElementById('buscaClienteInput');
    
    // Mostrar modal
    $(modal).modal('show');
    
    // Focar no input após modal abrir
    $(modal).on('shown.bs.modal', function() {
        buscaInput.focus();
        buscaInput.select();
    });
    
    // Limpar resultados anteriores
    document.getElementById('resultadosCliente').innerHTML = 
        '<div class="text-center text-muted">Digite para buscar...</div>';
}

function buscarCliente() {
    const termo = document.getElementById('buscaClienteInput').value.trim();
    const resultadosDiv = document.getElementById('resultadosCliente');
    
    if (termo.length < 2) {
        resultadosDiv.innerHTML = '<div class="text-muted">Digite pelo menos 2 caracteres...</div>';
        return;
    }
    
    // Mostrar loading
    resultadosDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Buscando...</p></div>';
    
    // Buscar via API
    fetch(`/api/clientes/buscar?q=${encodeURIComponent(termo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                resultadosDiv.innerHTML = '<div class="alert alert-warning">Nenhum cliente encontrado</div>';
                return;
            }
            
            // Montar lista de resultados
            let html = '<div class="list-group">';
            data.forEach(cliente => {
                html += `
                    <a href="#" class="list-group-item list-group-item-action" 
                       onclick="selecionarCliente(${cliente.id}, '${cliente.name}', '${cliente.cpf_cnpj || ''}'); return false;">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${cliente.name}</h6>
                            <small>${cliente.cpf_cnpj || 'Sem CPF/CNPJ'}</small>
                        </div>
                        <small class="text-muted">${cliente.email || ''} ${cliente.phone || ''}</small>
                    </a>
                `;
            });
            html += '</div>';
            
            resultadosDiv.innerHTML = html;
        })
        .catch(error => {
            console.error('[PDV] Erro ao buscar clientes:', error);
            resultadosDiv.innerHTML = '<div class="alert alert-danger">Erro ao buscar clientes</div>';
        });
}

function selecionarCliente(id, nome, cpf) {
    // Preencher campo
    const selectCliente = document.getElementById('customer_id');
    if (selectCliente) {
        selectCliente.value = id;
        
        // Se não existir no select, adicionar
        if (!selectCliente.querySelector(`option[value="${id}"]`)) {
            const option = document.createElement('option');
            option.value = id;
            option.text = nome;
            option.selected = true;
            selectCliente.add(option);
        }
    }
    
    // Fechar modal
    $('#modalBuscaCliente').modal('hide');
    
    // Focar no produto
    focarProduto();
    
    // Notificar
    mostrarNotificacao(`Cliente selecionado: ${nome}`, 'success');
}

// ===== MODAL DE PRODUTO (F3) =====
function abrirModalProduto() {
    const modal = document.getElementById('modalBuscaProduto');
    if (!modal) {
        console.error('[PDV] Modal de produto não encontrado');
        return;
    }
    
    const buscaInput = document.getElementById('buscaProdutoInput');
    
    // Mostrar modal
    $(modal).modal('show');
    
    // Focar no input
    $(modal).on('shown.bs.modal', function() {
        buscaInput.focus();
        buscaInput.select();
    });
    
    // Limpar resultados
    document.getElementById('resultadosProduto').innerHTML = 
        '<div class="text-center text-muted">Digite código, código de barras ou nome...</div>';
}

function buscarProduto() {
    const termo = document.getElementById('buscaProdutoInput').value.trim();
    const resultadosDiv = document.getElementById('resultadosProduto');
    
    if (termo.length < 2) {
        resultadosDiv.innerHTML = '<div class="text-muted">Digite pelo menos 2 caracteres...</div>';
        return;
    }
    
    // Loading
    resultadosDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Buscando...</p></div>';
    
    // Buscar via API
    fetch(`/api/produtos/buscar?q=${encodeURIComponent(termo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                resultadosDiv.innerHTML = '<div class="alert alert-warning">Nenhum produto encontrado</div>';
                return;
            }
            
            // Montar lista
            let html = '<div class="list-group">';
            data.forEach(produto => {
                const estoque = produto.stock || 0;
                const estoqueClass = estoque > 0 ? 'text-success' : 'text-danger';
                const preco = parseFloat(produto.sale_price || 0).toFixed(2).replace('.', ',');
                
                html += `
                    <a href="#" class="list-group-item list-group-item-action" 
                       onclick="adicionarProdutoModal(${produto.id}, '${produto.name}', ${produto.sale_price}); return false;">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${produto.name}</h6>
                            <span class="badge bg-primary">R$ ${preco}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <small class="text-muted">Código: ${produto.code || 'N/A'}</small>
                            <small class="${estoqueClass}">Estoque: ${estoque}</small>
                        </div>
                    </a>
                `;
            });
            html += '</div>';
            
            resultadosDiv.innerHTML = html;
        })
        .catch(error => {
            console.error('[PDV] Erro ao buscar produtos:', error);
            resultadosDiv.innerHTML = '<div class="alert alert-danger">Erro ao buscar produtos</div>';
        });
}

function adicionarProdutoModal(id, nome, preco) {
    // Fechar modal
    $('#modalBuscaProduto').modal('hide');
    
    // Adicionar produto à venda (usar quantidade rápida se foi definida)
    adicionarProdutoNaVenda(id, nome, preco, quantidadeRapida);
    
    // Resetar quantidade
    quantidadeRapida = 1;
    
    // Focar no campo produto
    focarProduto();
}

// ===== GERENCIAMENTO DE PRODUTOS NA GRADE =====
function adicionarProdutoNaVenda(id, nome, preco, quantidade) {
    // Verificar se já existe na grade
    const itemExistente = gradeVendas.find(item => item.product_id === id);
    
    if (itemExistente) {
        // Incrementar quantidade
        itemExistente.quantity += quantidade;
        itemExistente.total = itemExistente.quantity * itemExistente.price;
    } else {
        // Adicionar novo
        gradeVendas.push({
            product_id: id,
            name: nome,
            price: parseFloat(preco),
            quantity: quantidade,
            total: quantidade * parseFloat(preco)
        });
    }
    
    // Atualizar grade visual
    atualizarGrade();
    
    // Calcular totais
    calcularTotais();
    
    // Notificar
    mostrarNotificacao(`${nome} adicionado (${quantidade}x)`, 'success');
}

function atualizarGrade() {
    const tbody = document.getElementById('gradeVendasBody');
    if (!tbody) return;
    
    if (gradeVendas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum produto adicionado</td></tr>';
        return;
    }
    
    let html = '';
    gradeVendas.forEach((item, index) => {
        html += `
            <tr>
                <td>${item.product_id}</td>
                <td>${item.name}</td>
                <td class="text-center">
                    <input type="number" 
                           class="form-control form-control-sm text-center" 
                           value="${item.quantity}" 
                           min="1" 
                           style="width: 70px; display: inline-block;"
                           onchange="alterarQuantidade(${index}, this.value)">
                </td>
                <td class="text-end">R$ ${item.price.toFixed(2).replace('.', ',')}</td>
                <td class="text-end">R$ ${item.total.toFixed(2).replace('.', ',')}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-danger" onclick="removerItem(${index})" title="Remover">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function alterarQuantidade(index, novaQuantidade) {
    const quantidade = parseInt(novaQuantidade);
    
    if (quantidade < 1) {
        mostrarNotificacao('Quantidade mínima: 1', 'warning');
        atualizarGrade();
        return;
    }
    
    gradeVendas[index].quantity = quantidade;
    gradeVendas[index].total = quantidade * gradeVendas[index].price;
    
    atualizarGrade();
    calcularTotais();
}

function removerItem(index) {
    const item = gradeVendas[index];
    
    if (confirm(`Remover ${item.name} da venda?`)) {
        gradeVendas.splice(index, 1);
        atualizarGrade();
        calcularTotais();
        mostrarNotificacao('Item removido', 'info');
    }
}

function calcularTotais() {
    totalVenda = gradeVendas.reduce((sum, item) => sum + item.total, 0);
    
    // Atualizar display
    const totalDisplay = document.getElementById('totalVendaDisplay');
    if (totalDisplay) {
        totalDisplay.textContent = `R$ ${totalVenda.toFixed(2).replace('.', ',')}`;
    }
    
    // Atualizar campo hidden
    const totalField = document.getElementById('net_total');
    if (totalField) {
        totalField.value = totalVenda.toFixed(2);
    }
}

// ===== QUANTIDADE RÁPIDA (*3 + código) =====
function handleCodigoProduto(event) {
    const input = event.target;
    const valor = input.value.trim();
    
    // Detectar * seguido de número (processa em tempo real)
    if (valor.startsWith('*') && event.key !== 'Enter') {
        const numero = valor.substring(1);
        // Se já tem número completo
        if (numero.length > 0 && !isNaN(numero)) {
            quantidadeRapida = parseInt(numero);
            input.value = '';
            mostrarNotificacao(`Quantidade: ${quantidadeRapida}x`, 'info');
            input.placeholder = `Quantidade: ${quantidadeRapida}x - Digite o código...`;
            setTimeout(() => {
                input.placeholder = 'Digite código, código de barras ou pressione F3...';
            }, 3000);
            event.preventDefault();
            return;
        }
    }
    
    // ENTER - Buscar produto pelo código
    if (event.key === 'Enter' && valor !== '' && !valor.startsWith('*')) {
        event.preventDefault();
        buscarProdutoPorCodigo(valor);
    }
}

function buscarProdutoPorCodigo(codigo) {
    fetch(`/api/produtos/buscar?q=${encodeURIComponent(codigo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                mostrarNotificacao('Produto não encontrado', 'warning');
                return;
            }
            
            // Se encontrou exatamente 1, adicionar
            if (data.length === 1) {
                const produto = data[0];
                adicionarProdutoNaVenda(produto.id, produto.name, produto.sale_price, quantidadeRapida);
                quantidadeRapida = 1;
                document.getElementById('codigoProduto').value = '';
            } else {
                // Múltiplos resultados - abrir modal
                abrirModalProduto();
                document.getElementById('buscaProdutoInput').value = codigo;
                buscarProduto();
            }
        })
        .catch(error => {
            console.error('[PDV] Erro ao buscar produto:', error);
            mostrarNotificacao('Erro ao buscar produto', 'danger');
        });
}

// ===== FINALIZAR VENDA (F9) =====
function finalizarVenda() {
    // Validações
    if (gradeVendas.length === 0) {
        mostrarNotificacao('❌ Adicione pelo menos um produto para finalizar!', 'warning');
        return;
    }
    
    // Verificar se cliente é obrigatório (configuração)
    const customerId = document.getElementById('customer_id')?.value;
    if (pdvConfig.require_customer && !customerId) {
        mostrarNotificacao('❌ Selecione um cliente antes de finalizar!', 'warning');
        return;
    }
    
    // Abrir modal de finalização
    abrirModalFinalizacao();
}

function abrirModalFinalizacao() {
    const modal = document.getElementById('modalFinalizacao');
    if (!modal) {
        console.error('[PDV] Modal de finalização não encontrado');
        return;
    }
    
    // Preencher valores
    document.getElementById('finalizacaoTotal').textContent = 
        `R$ ${totalVenda.toFixed(2).replace('.', ',')}`;
    
    // Limpar pagamentos
    limparPagamentos();
    
    // Mostrar modal
    $(modal).modal('show');
    
    // Focar no primeiro campo
    setTimeout(() => {
        document.getElementById('valorPagamento1')?.focus();
    }, 500);
}

// ===== MÚLTIPLOS PAGAMENTOS =====
let pagamentosLista = [];

function adicionarPagamento() {
    const metodo = document.getElementById('metodoPagamento1').value;
    const valor = parseFloat(document.getElementById('valorPagamento1').value || 0);
    
    if (!metodo || valor <= 0) {
        mostrarNotificacao('Informe método e valor válidos', 'warning');
        return;
    }
    
    pagamentosLista.push({ metodo, valor });
    atualizarListaPagamentos();
    calcularTroco();
    
    // Limpar campos
    document.getElementById('metodoPagamento1').value = '';
    document.getElementById('valorPagamento1').value = '';
    document.getElementById('metodoPagamento1').focus();
}

function atualizarListaPagamentos() {
    const lista = document.getElementById('listaPagamentos');
    if (!lista) return;
    
    if (pagamentosLista.length === 0) {
        lista.innerHTML = '<div class="text-muted">Nenhum pagamento adicionado</div>';
        return;
    }
    
    let html = '<ul class="list-group">';
    pagamentosLista.forEach((pag, index) => {
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${pag.metodo}</span>
                <span>
                    R$ ${pag.valor.toFixed(2).replace('.', ',')}
                    <button class="btn btn-sm btn-danger ms-2" onclick="removerPagamento(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                </span>
            </li>
        `;
    });
    html += '</ul>';
    
    lista.innerHTML = html;
}

function removerPagamento(index) {
    pagamentosLista.splice(index, 1);
    atualizarListaPagamentos();
    calcularTroco();
}

function limparPagamentos() {
    pagamentosLista = [];
    atualizarListaPagamentos();
    document.getElementById('trocoDisplay').textContent = 'R$ 0,00';
}

function calcularTroco() {
    const totalPago = pagamentosLista.reduce((sum, pag) => sum + pag.valor, 0);
    const troco = totalPago - totalVenda;
    
    const trocoDisplay = document.getElementById('trocoDisplay');
    if (trocoDisplay) {
        if (troco >= 0) {
            trocoDisplay.textContent = `R$ ${troco.toFixed(2).replace('.', ',')}`;
            trocoDisplay.className = 'h3 text-success';
        } else {
            trocoDisplay.textContent = `R$ ${Math.abs(troco).toFixed(2).replace('.', ',')} (falta)`;
            trocoDisplay.className = 'h3 text-danger';
        }
    }
}

// ===== CONFIRMAR VENDA =====
function confirmarVenda() {
    const totalPago = pagamentosLista.reduce((sum, pag) => sum + pag.valor, 0);
    
    if (totalPago < totalVenda) {
        mostrarNotificacao('Valor pago insuficiente!', 'danger');
        return;
    }
    
    // Submeter formulário com dados
    // TODO: Implementar submit do formulário com pagamentos
    mostrarNotificacao('Venda confirmada!', 'success');
    
    // Fechar modal
    $('#modalFinalizacao').modal('hide');
    
    // Limpar tudo
    limparVenda();
}

async function limparVenda() {
    gradeVendas = [];
    pagamentosLista = [];
    quantidadeRapida = 1;
    totalVenda = 0;
    
    atualizarGrade();
    calcularTotais();
    
    // Limpar campos
    document.getElementById('customer_id').value = '';
    
    // IMPORTANTE: Limpar carrinho no servidor também
    try {
        await fetch('/vendas/pdv/limpar-carrinho', { method: 'POST' });
        console.log('[PDV] ✅ Carrinho limpo no servidor após venda');
    } catch (error) {
        console.error('[PDV] Erro ao limpar carrinho no servidor:', error);
    }
    
    focarProduto();
}

// ===== UTILITÁRIOS =====
function focarProduto() {
    setTimeout(() => {
        const campo = document.getElementById('codigoProduto');
        if (campo) {
            campo.focus();
            campo.select();
        }
    }, 300);
}

function fecharModais() {
    $('.modal').modal('hide');
}

function mostrarNotificacao(mensagem, tipo = 'info') {
    // Usando toastr se disponível
    if (typeof toastr !== 'undefined') {
        toastr[tipo](mensagem);
        return;
    }
    
    // Fallback - alert simples
    console.log(`[PDV] ${tipo.toUpperCase()}: ${mensagem}`);
    
    // ou criar notificação Bootstrap
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => alertDiv.remove(), 3000);
}

// ===== LIMPAR AO SAIR =====
// Limpa carrinho automaticamente ao sair da página do PDV
window.addEventListener('beforeunload', function(e) {
    // Limpar carrinho via fetch (não espera resposta)
    navigator.sendBeacon('/vendas/pdv/limpar-carrinho');
    console.log('[PDV] Carrinho limpo ao sair da página');
});

// Também limpar ao clicar em links que saem do PDV
document.addEventListener('DOMContentLoaded', function() {
    // Limpar ao clicar no botão Menu (ESC) ou voltar
    const linksExternos = document.querySelectorAll('a[href="/"], a[href*="menu"], a[href*="dashboard"]');
    linksExternos.forEach(link => {
        link.addEventListener('click', function(e) {
            // Limpar carrinho
            fetch('/vendas/pdv/limpar-carrinho', { method: 'POST' })
                .then(() => console.log('[PDV] Carrinho limpo ao sair'));
        });
    });
});

// ===== SAIR DO PDV (ESC) =====
async function sairDoPDV() {
    console.log('[PDV] ESC pressionado - Verificando carrinho...');
    
    // Verificar se há itens no carrinho ou cliente diferente do padrão
    const carrinhoAtual = await fetch('/vendas/pdv/carrinho-atual')
        .then(r => r.json())
        .catch(() => ({ carrinho: { itens: [], cliente_id: null, cliente_nome: '' } }));
    
    const carrinho = carrinhoAtual.carrinho || {};
    const temItens = carrinho.itens && carrinho.itens.length > 0;
    const temCliente = carrinho.cliente_id && 
                      carrinho.cliente_nome && 
                      carrinho.cliente_nome !== '**CLIENTE A VISTA**' &&
                      carrinho.cliente_nome !== 'CONSUMIDOR FINAL';
    
    console.log('[PDV] Tem itens:', temItens);
    console.log('[PDV] Tem cliente:', temCliente, '- Nome:', carrinho.cliente_nome);
    
    // Só pedir confirmação se tiver produtos OU cliente diferente do padrão
    if (temItens || temCliente) {
        // Tem venda em andamento - perguntar confirmação
        const confirmar = confirm(
            '⚠️ ATENÇÃO!\n\n' +
            'Você tem uma venda em andamento.\n\n' +
            'Deseja realmente sair e CANCELAR esta venda?'
        );
        
        if (!confirmar) {
            console.log('[PDV] Usuário cancelou saída');
            return; // Não sai
        }
        
        console.log('[PDV] Usuário confirmou saída - Removendo TODOS os itens...');
        
        // REMOVER TODOS OS ITENS DA GRADE (mesmo comportamento da lixeira)
        if (temItens) {
            console.log(`[PDV] 🗑️ Removendo ${carrinho.itens.length} itens da grade`);
            for (const item of carrinho.itens) {
                console.log(`[PDV]   - Removendo: ${item.nome}`);
            }
        }
    } else {
        console.log('[PDV] Carrinho vazio - Saindo sem confirmação');
    }
    
    // Limpar carrinho via API (remove todos os itens)
    try {
        const response = await fetch('/vendas/pdv/limpar-carrinho', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            console.log('[PDV] ✅ Carrinho limpo - TODOS os itens removidos');
        } else {
            console.error('[PDV] ❌ Erro ao limpar carrinho:', data);
        }
    } catch (error) {
        console.error('[PDV] ❌ Erro ao limpar carrinho:', error);
    }
    
    // IMPORTANTE: Aguardar 300ms para garantir que o servidor processou
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Redirecionar para dashboard
    console.log('[PDV] 🚀 Redirecionando para dashboard...');
    window.location.href = '/dashboard';
}

// ===== LOG =====
console.log('[PDV] Sistema PDV Moderno v1.0 carregado!');
console.log('[PDV] Atalhos disponíveis:');
console.log('[PDV] F2 - Buscar Cliente');
console.log('[PDV] F3 - Buscar Produto');
console.log('[PDV] F4 - Forma de Pagamento');
console.log('[PDV] F9 - Finalizar Venda');
console.log('[PDV] ESC - Sair do PDV');
console.log('[PDV] *N + código - Quantidade rápida');
console.log('[PDV] ✅ Limpeza automática ATIVADA');
