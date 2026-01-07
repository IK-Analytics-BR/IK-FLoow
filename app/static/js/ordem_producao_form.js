// ========================================
// ORDEM DE PRODUÇÃO - FORMULÁRIO COMPLETO
// ========================================

// Variáveis globais
let templateAtual = null;
let modalAdicionarItem, modalTemplate;
let tipoItemAtual = '';
let modalBuscaProduto;
let linhaProdutoSelecionada = -1;
let contadorItens = {
    servico: 0,
    materia_prima: 0,
    consumo_interno: 0
};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    modalAdicionarItem = new bootstrap.Modal(document.getElementById('modalAdicionarItem'));
    modalTemplate = new bootstrap.Modal(document.getElementById('modalTemplate'));
    const modalBuscaProdutoEl = document.getElementById('modalBuscaProduto');
    if (modalBuscaProdutoEl) {
        modalBuscaProduto = bootstrap.Modal.getOrCreateInstance(modalBuscaProdutoEl);
    }
    
    // Event listeners
    document.getElementById('modal_produto_id').addEventListener('change', atualizarDadosProduto);
    document.getElementById('modal_quantidade').addEventListener('input', calcularTotalModal);
    document.getElementById('modal_custo_unitario').addEventListener('input', calcularTotalModal);

    const btnBuscarProduto = document.getElementById('btnBuscarProduto');
    if (btnBuscarProduto) {
        btnBuscarProduto.addEventListener('click', abrirBuscaProdutoFinal);
    }

    const btnPesquisarProduto = document.getElementById('btnPesquisarProduto');
    if (btnPesquisarProduto) {
        btnPesquisarProduto.addEventListener('click', pesquisarProdutosFinais);
    }

    const btnSelecionarProduto = document.getElementById('btnSelecionarProduto');
    if (btnSelecionarProduto) {
        btnSelecionarProduto.addEventListener('click', selecionarProdutoFinalDestacado);
    }

    const buscaInput = document.getElementById('busca_produto_input');
    if (buscaInput) {
        buscaInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const tbody = document.getElementById('tbodyProdutos');
                const rows = tbody ? tbody.querySelectorAll('.produto-row') : [];
                if (rows.length > 0 && linhaProdutoSelecionada >= 0) {
                    selecionarProdutoFinalDestacado();
                } else {
                    pesquisarProdutosFinais();
                }
            } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                navegarListaProdutos(e);
            }
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'F2') {
            const modalEl = document.getElementById('modalBuscaProduto');
            const modalAberto = modalEl && modalEl.classList.contains('show');
            if (!modalAberto) {
                e.preventDefault();
                abrirBuscaProdutoFinal();
            }
        }
    });
});

function abrirBuscaProdutoFinal() {
    const modalEl = document.getElementById('modalBuscaProduto');
    if (!modalEl) return;

    linhaProdutoSelecionada = -1;
    const tbody = document.getElementById('tbodyProdutos');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Digite para buscar...</td></tr>';
    }

    const input = document.getElementById('busca_produto_input');
    if (input) input.value = '';

    modalEl.addEventListener('shown.bs.modal', function foca() {
        const el = document.getElementById('busca_produto_input');
        if (el) el.focus();
        modalEl.removeEventListener('shown.bs.modal', foca);
    });

    if (modalBuscaProduto) {
        modalBuscaProduto.show();
    } else {
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
}

function pesquisarProdutosFinais() {
    const termo = (document.getElementById('busca_produto_input') || {}).value || '';
    if (termo.length < 2) {
        alert('Digite pelo menos 2 caracteres para buscar.');
        return;
    }

    const tbody = document.getElementById('tbodyProdutos');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Buscando...</td></tr>';

    fetch(`/industria/ordem-producao/api/buscar-produtos-producao?q=${encodeURIComponent(termo)}`)
        .then(r => r.json())
        .then(data => {
            if (!Array.isArray(data) || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Nenhum produto encontrado.</td></tr>';
                return;
            }

            let html = '';
            data.forEach((p, idx) => {
                const codigo = p.codigo || p.id;
                const nome = p.nome || '';
                const unidade = p.unidade || 'UN';
                const custo = parseFloat(p.custo || 0);

                html += `<tr style="cursor:pointer" class="produto-row"
                            data-idx="${idx}"
                            data-id="${p.id}"
                            data-codigo="${codigo}"
                            data-nome="${String(nome).replace(/\"/g, '&quot;').replace(/"/g, '&quot;')}"
                            data-unidade="${unidade}"
                            data-custo="${custo}">
                    <td>${codigo}</td>
                    <td>${nome}</td>
                    <td>${unidade}</td>
                    <td class="text-end">R$ ${custo.toFixed(2).replace('.', ',')}</td>
                </tr>`;
            });
            tbody.innerHTML = html;

            tbody.querySelectorAll('.produto-row').forEach(row => {
                row.addEventListener('click', function() {
                    tbody.querySelectorAll('.produto-row').forEach(r => r.classList.remove('table-primary'));
                    this.classList.add('table-primary');
                    linhaProdutoSelecionada = parseInt(this.dataset.idx);
                });
                row.addEventListener('dblclick', function() {
                    selecionarProdutoFinal(this.dataset.id, this.dataset.codigo, this.dataset.nome);
                });
            });

            linhaProdutoSelecionada = 0;
            const first = tbody.querySelector('.produto-row');
            if (first) first.classList.add('table-primary');
        })
        .catch(() => {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger py-3">Erro ao buscar produtos.</td></tr>';
        });
}

function navegarListaProdutos(e) {
    const tbody = document.getElementById('tbodyProdutos');
    if (!tbody) return;
    const rows = tbody.querySelectorAll('.produto-row');
    if (!rows || rows.length === 0) return;

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        linhaProdutoSelecionada = Math.min(linhaProdutoSelecionada + 1, rows.length - 1);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        linhaProdutoSelecionada = Math.max(linhaProdutoSelecionada - 1, 0);
    }

    rows.forEach((r, i) => r.classList.toggle('table-primary', i === linhaProdutoSelecionada));
    if (rows[linhaProdutoSelecionada]) {
        rows[linhaProdutoSelecionada].scrollIntoView({ block: 'nearest' });
    }
}

function selecionarProdutoFinalDestacado() {
    const tbody = document.getElementById('tbodyProdutos');
    if (!tbody) return;
    const rows = tbody.querySelectorAll('.produto-row');
    if (linhaProdutoSelecionada >= 0 && rows[linhaProdutoSelecionada]) {
        const row = rows[linhaProdutoSelecionada];
        selecionarProdutoFinal(row.dataset.id, row.dataset.codigo, row.dataset.nome);
    } else {
        alert('Selecione um produto da lista primeiro.');
    }
}

function selecionarProdutoFinal(id, codigo, nome) {
    const produtoIdEl = document.getElementById('produto_id');
    const produtoCodigoEl = document.getElementById('produto_codigo');
    const produtoNomeEl = document.getElementById('produto_nome');

    if (produtoIdEl) produtoIdEl.value = id;
    if (produtoCodigoEl) produtoCodigoEl.value = codigo || id;
    if (produtoNomeEl) produtoNomeEl.value = nome || '';

    const modalEl = document.getElementById('modalBuscaProduto');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl) || bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.hide();
    }
}

// ========================================
// VERIFICAR TEMPLATE
// ========================================
function verificarTemplate() {
    const produtoId = document.getElementById('produto_id').value;
    
    if (!produtoId) {
        alert('Selecione um produto primeiro!');
        return;
    }
    
    fetch(`/industria/ordem-producao/verificar-template/${produtoId}`)
        .then(r => r.json())
        .then(data => {
            if (data.existe) {
                templateAtual = data;
                mostrarModalTemplate(data);
            } else {
                alert('❌ Nenhuma Ficha Técnica encontrada para este produto.\n\nVocê precisará adicionar os itens manualmente nas abas:\n• Mão de Obra\n• Matéria Prima\n• Consumo Interno');
            }
        })
        .catch(error => {
            alert('Erro ao verificar Ficha Técnica: ' + error);
        });
}

function mostrarModalTemplate(data) {
    const html = `
        <div class="alert alert-info">
            <h6><strong>Produto:</strong> ${data.template.nome || 'Template'}</h6>
            <p class="mb-0"><strong>Versão:</strong> v${data.template.versao}</p>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h6>💰 Custo Base (Ficha Técnica)</h6>
                        <h4 class="text-primary">R$ ${data.template.custo_base.toFixed(2)}</h4>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h6>💵 Custo Atual (Preços Atuais)</h6>
                        <h4 class="${data.template.variacao_percentual > 0 ? 'text-danger' : 'text-success'}">
                            R$ ${data.template.custo_atual.toFixed(2)}
                        </h4>
                        <small class="${data.template.variacao_percentual > 0 ? 'text-danger' : 'text-success'}">
                            ${data.template.variacao_percentual > 0 ? '⬆️' : '⬇️'} 
                            ${Math.abs(data.template.variacao_percentual).toFixed(1)}%
                        </small>
                    </div>
                </div>
            </div>
        </div>
        
        <h6>📋 Itens da Ficha Técnica (${data.itens.length})</h6>
        <div class="table-responsive">
            <table class="table table-sm table-bordered">
                <thead class="table-light">
                    <tr>
                        <th>Tipo</th>
                        <th>Item</th>
                        <th>Qtd</th>
                        <th>Custo Unit. Base</th>
                        <th>Custo Unit. Atual</th>
                        <th>Variação</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.itens.map(item => `
                        <tr>
                            <td>
                                ${item.tipo_item === 'servico' ? '🔧' : 
                                  item.tipo_item === 'materia_prima' ? '📦' : '🧰'}
                            </td>
                            <td>${item.produto_nome}</td>
                            <td>${item.quantidade} ${item.unidade_medida || ''}</td>
                            <td>R$ ${item.custo_unitario_base.toFixed(2)}</td>
                            <td>R$ ${item.custo_unitario_atual.toFixed(2)}</td>
                            <td class="${item.variacao_percentual > 0 ? 'text-danger' : 'text-success'}">
                                ${item.variacao_percentual.toFixed(1)}%
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('conteudoTemplate').innerHTML = html;
    modalTemplate.show();
}

function usarTemplate() {
    if (!templateAtual) return;
    
    // Marcar que usou template
    document.getElementById('usou_template').value = '1';
    document.getElementById('template_usado_id').value = templateAtual.template.id;
    document.getElementById('custo_total_template').value = templateAtual.template.custo_base;
    
    // Limpar tabelas
    limparTabela('servico');
    limparTabela('materia_prima');
    limparTabela('consumo_interno');
    
    // Adicionar itens do template
    templateAtual.itens.forEach(item => {
        adicionarItemNaTabela(
            item.tipo_item,
            item.produto_id,
            item.produto_nome,
            item.quantidade,
            item.unidade_medida || '',
            item.custo_unitario_atual,
            item.custo_unitario_base,
            true // veio do template
        );
    });
    
    // Atualizar totais
    atualizarTotais();
    
    modalTemplate.hide();
    alert(`✅ Ficha Técnica carregada com sucesso!\n\n${templateAtual.itens.length} itens foram adicionados.\n\nVocê pode editar ou adicionar mais itens nas abas correspondentes.`);
}

// ========================================
// ADICIONAR ITEM MANUAL
// ========================================
function adicionarItem(tipo) {
    tipoItemAtual = tipo;
    
    const titulos = {
        'servico': '🔧 Adicionar Serviço / Mão de Obra',
        'materia_prima': '📦 Adicionar Matéria Prima',
        'consumo_interno': '🧰 Adicionar Item de Consumo'
    };
    
    document.getElementById('modalAdicionarItemTitulo').textContent = titulos[tipo];
    
    // Limpar campos
    document.getElementById('modal_produto_id').value = '';
    document.getElementById('modal_quantidade').value = '';
    document.getElementById('modal_unidade').value = '';
    document.getElementById('modal_custo_unitario').value = '';
    document.getElementById('modal_total_preview').textContent = '0,00';
    
    // Carregar produtos do tipo
    carregarProdutosPorTipo(tipo);
    
    modalAdicionarItem.show();
}

function carregarProdutosPorTipo(tipo) {
    const select = document.getElementById('modal_produto_id');
    select.innerHTML = '<option value="">Carregando...</option>';
    
    fetch(`/industria/ordem-producao/buscar-produtos-por-tipo?tipo=${tipo}`)
        .then(r => r.json())
        .then(produtos => {
            select.innerHTML = '<option value="">Selecione...</option>';
            produtos.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = `${p.name} - R$ ${p.cost_price.toFixed(2)}`;
                option.dataset.nome = p.name;
                option.dataset.preco = p.cost_price;
                option.dataset.unidade = p.unit_measure || '';
                select.appendChild(option);
            });
        })
        .catch(error => {
            select.innerHTML = '<option value="">Erro ao carregar</option>';
            alert('Erro ao carregar produtos: ' + error);
        });
}

function atualizarDadosProduto() {
    const select = document.getElementById('modal_produto_id');
    const option = select.options[select.selectedIndex];
    
    if (option && option.value) {
        document.getElementById('modal_unidade').value = option.dataset.unidade || '';
        document.getElementById('modal_custo_unitario').value = option.dataset.preco || '0';
        calcularTotalModal();
    }
}

function calcularTotalModal() {
    const qtd = parseFloat(document.getElementById('modal_quantidade').value) || 0;
    const custo = parseFloat(document.getElementById('modal_custo_unitario').value) || 0;
    const total = qtd * custo;
    document.getElementById('modal_total_preview').textContent = total.toFixed(2);
}

function confirmarAdicaoItem() {
    const select = document.getElementById('modal_produto_id');
    const option = select.options[select.selectedIndex];
    
    if (!option || !option.value) {
        alert('Selecione um produto!');
        return;
    }
    
    const produtoId = option.value;
    const produtoNome = option.dataset.nome;
    const quantidade = parseFloat(document.getElementById('modal_quantidade').value);
    const unidade = document.getElementById('modal_unidade').value;
    const custoUnitario = parseFloat(document.getElementById('modal_custo_unitario').value);
    
    if (!quantidade || quantidade <= 0) {
        alert('Informe uma quantidade válida!');
        return;
    }
    
    if (!custoUnitario || custoUnitario < 0) {
        alert('Informe um custo unitário válido!');
        return;
    }
    
    // Adicionar na tabela
    adicionarItemNaTabela(tipoItemAtual, produtoId, produtoNome, quantidade, unidade, custoUnitario, 0, false);
    
    // Atualizar totais
    atualizarTotais();
    
    // Fechar modal
    modalAdicionarItem.hide();
}

// ========================================
// MANIPULAÇÃO DE TABELAS
// ========================================
function adicionarItemNaTabela(tipo, produtoId, produtoNome, quantidade, unidade, custoUnitario, custoTemplate, veioTemplate) {
    const tbody = document.getElementById(`tbody-${tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servicos'}`);
    
    // Remover linha vazia se existir
    const emptyRow = tbody.querySelector('.empty-row');
    if (emptyRow) {
        emptyRow.remove();
    }
    
    const id = ++contadorItens[tipo];
    const total = quantidade * custoUnitario;
    
    // Ajustar nome do campo para backend
    const fieldName = tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servico';
    
    const tr = document.createElement('tr');
    tr.dataset.id = id;
    tr.dataset.produtoId = produtoId;
    tr.innerHTML = `
        <td>
            ${produtoNome}
            <input type="hidden" name="${fieldName}_produto_id[]" value="${produtoId}">
            <input type="hidden" name="${fieldName}_veio_template[]" value="${veioTemplate ? '1' : '0'}">
            <input type="hidden" name="${fieldName}_custo_template[]" value="${custoTemplate}">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm" name="${fieldName}_quantidade[]" 
                   value="${quantidade}" step="0.01" min="0.01" onchange="atualizarTotais()" required>
        </td>
        <td>${unidade}</td>
        <td>
            <input type="number" class="form-control form-control-sm" name="${fieldName}_custo_unitario[]" 
                   value="${custoUnitario}" step="0.01" min="0" onchange="atualizarTotais()" required>
        </td>
        <td class="total-item"><strong>R$ ${total.toFixed(2)}</strong></td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="removerItem(this, '${tipo}')">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(tr);
}

function removerItem(btn, tipo) {
    if (confirm('Deseja remover este item?')) {
        btn.closest('tr').remove();
        
        // Verificar se ficou vazio
        const tbody = document.getElementById(`tbody-${tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servicos'}`);
        if (tbody.children.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="6" class="text-center text-muted">
                        Nenhum item adicionado.
                    </td>
                </tr>
            `;
        }
        
        atualizarTotais();
    }
}

function limparTabela(tipo) {
    const tbody = document.getElementById(`tbody-${tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servicos'}`);
    tbody.innerHTML = '';
    contadorItens[tipo] = 0;
}

// ========================================
// ATUALIZAR TOTAIS
// ========================================
function atualizarTotais() {
    const tipos = ['servico', 'materia_prima', 'consumo_interno'];
    const totais = {};
    let totalGeral = 0;
    let totalItens = 0;
    
    tipos.forEach(tipo => {
        const tbodyId = tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servicos';
        const tbody = document.getElementById(`tbody-${tbodyId}`);
        const rows = tbody.querySelectorAll('tr:not(.empty-row)');
        
        let subtotal = 0;
        rows.forEach(row => {
            const qtdInput = row.querySelector(`input[name="${tipo}_quantidade[]"]`);
            const custoInput = row.querySelector(`input[name="${tipo}_custo_unitario[]"]`);
            
            if (qtdInput && custoInput) {
                const qtd = parseFloat(qtdInput.value) || 0;
                const custo = parseFloat(custoInput.value) || 0;
                const total = qtd * custo;
                
                row.querySelector('.total-item').innerHTML = `<strong>R$ ${total.toFixed(2)}</strong>`;
                subtotal += total;
                totalItens++;
            }
        });
        
        totais[tipo] = subtotal;
        totalGeral += subtotal;
        
        // Atualizar subtotal da tabela
        const subtotalId = tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servicos';
        document.getElementById(`subtotal-${subtotalId}`).textContent = `R$ ${subtotal.toFixed(2)}`;
        
        // Atualizar resumo
        document.getElementById(`resumo-${subtotalId}`).textContent = `R$ ${subtotal.toFixed(2)}`;
        
        // Atualizar quantidade
        const qtdId = tipo === 'materia_prima' ? 'materia' : tipo === 'consumo_interno' ? 'consumo' : 'servicos';
        document.getElementById(`qtd-${qtdId}`).textContent = rows.length;
    });
    
    // Atualizar total geral
    document.getElementById('total-geral').textContent = `R$ ${totalGeral.toFixed(2)}`;
    document.getElementById('total-itens').textContent = totalItens;
}
