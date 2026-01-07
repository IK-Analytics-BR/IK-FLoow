// Script simplificado para o formulário de pedidos de compra
// Evita conflitos com outros scripts usando funções anônimas imediatas

(function() {
    // Função para carregar dados do fornecedor
    function loadSupplierData(supplierId) {
        if (!supplierId) return;
        
        console.log('Carregando dados do fornecedor:', supplierId);
        
        // Requisição AJAX simples sem jQuery
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/suppliers/' + supplierId, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        console.log('Dados do fornecedor:', data);
                        
                        // Preencher campos com os dados do fornecedor
                        document.getElementById('supplier_tax_id').value = data.tax_id || '';
                        document.getElementById('contact_name').value = data.contact_name || '';
                        document.getElementById('delivery_address').value = data.address || '';
                        
                        // Adicionar cidade e estado ao endereço se disponíveis
                        if (data.city && data.state) {
                            var addressText = document.getElementById('delivery_address').value;
                            if (addressText && !addressText.includes(data.city)) {
                                addressText += '\n' + data.city + ' - ' + data.state;
                                if (data.zip_code) {
                                    addressText += '\nCEP: ' + data.zip_code;
                                }
                                document.getElementById('delivery_address').value = addressText;
                            }
                        }
                    } catch (e) {
                        console.error('Erro ao processar dados do fornecedor:', e);
                    }
                } else {
                    console.error('Erro ao buscar fornecedor:', xhr.status);
                }
            }
        };
        xhr.send();
    }
    
    // Função para carregar dados do produto
    function loadProductData(productId, row) {
        if (!productId) return;
        
        console.log('Carregando dados do produto:', productId);
        
        // Requisição AJAX simples sem jQuery
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/products/' + productId, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        console.log('Dados do produto:', data);
                        
                        // Preencher campos com os dados do produto
                        var unitInput = row.querySelector('.item-unit');
                        var priceInput = row.querySelector('.item-price');
                        
                        if (unitInput) unitInput.value = data.unit_measure || '';
                        if (priceInput) {
                            if (data.last_purchase_price && data.last_purchase_price > 0) {
                                priceInput.value = data.last_purchase_price;
                            } else if (data.cost_price && data.cost_price > 0) {
                                priceInput.value = data.cost_price;
                            }
                        }
                        
                        // Calcular total
                        calculateItemTotal(row);
                        calculateOrderTotal();
                    } catch (e) {
                        console.error('Erro ao processar dados do produto:', e);
                    }
                } else {
                    console.error('Erro ao buscar produto:', xhr.status);
                }
            }
        };
        xhr.send();
    }
    
    // Função para calcular o total de um item
    function calculateItemTotal(row) {
        var quantity = parseFloat(row.querySelector('.item-quantity').value) || 0;
        var price = parseFloat(row.querySelector('.item-price').value) || 0;
        var discount = parseFloat(row.querySelector('.item-discount').value) || 0;
        
        var totalBeforeDiscount = quantity * price;
        var discountAmount = totalBeforeDiscount * (discount / 100);
        var total = totalBeforeDiscount - discountAmount;
        
        row.querySelector('.item-total').value = total.toFixed(2);
    }
    
    // Função para calcular o total do pedido
    function calculateOrderTotal() {
        var subtotal = 0;
        var rows = document.querySelectorAll('#itemsTable tbody tr');
        
        rows.forEach(function(row) {
            var total = parseFloat(row.querySelector('.item-total').value) || 0;
            subtotal += total;
        });
        
        document.getElementById('subtotal').value = subtotal.toFixed(2);
        
        var discountPercent = parseFloat(document.getElementById('discount_percent').value) || 0;
        var discountValue = subtotal * (discountPercent / 100);
        document.getElementById('discount_value').value = discountValue.toFixed(2);
        
        var shippingCost = parseFloat(document.getElementById('shipping_cost').value) || 0;
        var insuranceCost = parseFloat(document.getElementById('insurance_cost').value) || 0;
        var otherCosts = parseFloat(document.getElementById('other_costs').value) || 0;
        var taxValue = parseFloat(document.getElementById('tax_value').value) || 0;
        
        var totalValue = subtotal - discountValue + shippingCost + insuranceCost + otherCosts + taxValue;
        document.getElementById('total_value').value = totalValue.toFixed(2);
        
        // Atualizar resumo do pedido
        updateOrderSummary(subtotal, discountPercent, discountValue, shippingCost, insuranceCost, otherCosts, taxValue, totalValue, rows.length);
    }
    
    // Função para atualizar o resumo do pedido
    function updateOrderSummary(subtotal, discountPercent, discountValue, shippingCost, insuranceCost, otherCosts, taxValue, totalValue, itemCount) {
        var summaryHtml = '<div class="alert alert-info mt-3">' +
            '<h5>Resumo do Pedido</h5>' +
            '<p><strong>' + itemCount + '</strong> ' + (itemCount === 1 ? 'item' : 'itens') + ' no pedido</p>' +
            '<p>Subtotal: R$ ' + subtotal.toFixed(2) + '</p>';
        
        if (discountValue > 0) {
            summaryHtml += '<p>Desconto (' + discountPercent.toFixed(2) + '%): R$ ' + discountValue.toFixed(2) + '</p>';
        }
        
        if (shippingCost > 0) {
            summaryHtml += '<p>Frete: R$ ' + shippingCost.toFixed(2) + '</p>';
        }
        
        if (insuranceCost > 0) {
            summaryHtml += '<p>Seguro: R$ ' + insuranceCost.toFixed(2) + '</p>';
        }
        
        if (otherCosts > 0) {
            summaryHtml += '<p>Outros custos: R$ ' + otherCosts.toFixed(2) + '</p>';
        }
        
        if (taxValue > 0) {
            summaryHtml += '<p>Impostos: R$ ' + taxValue.toFixed(2) + '</p>';
        }
        
        summaryHtml += '<p class="fw-bold">Total: R$ ' + totalValue.toFixed(2) + '</p>' +
            '</div>';
        
        document.getElementById('order-summary').innerHTML = summaryHtml;
    }
    
    // Função para adicionar um novo item
    function addNewItem() {
        var tbody = document.querySelector('#itemsTable tbody');
        var template = document.getElementById('itemTemplate');
        
        if (!template) {
            console.error('Template não encontrado!');
            return;
        }
        
        var clone = document.importNode(template.content, true);
        var index = tbody.querySelectorAll('tr').length;
        
        // Atualizar índice
        var indexCell = clone.querySelector('.item-index');
        if (indexCell) {
            indexCell.textContent = index + 1;
        }
        
        // Atualizar nomes dos campos
        var inputs = clone.querySelectorAll('[name*="INDEX"]');
        inputs.forEach(function(input) {
            input.name = input.name.replace('INDEX', index);
        });
        
        // Adicionar à tabela
        tbody.appendChild(clone);
        
        // Adicionar event listeners para o novo item
        var newRow = tbody.lastElementChild;
        setupItemEventListeners(newRow);
        
        // Calcular totais
        calculateOrderTotal();
    }
    
    // Função para remover um item
    function removeItem(button) {
        var tbody = document.querySelector('#itemsTable tbody');
        var rows = tbody.querySelectorAll('tr');
        
        if (rows.length > 1) {
            var row = button.closest('tr');
            row.parentNode.removeChild(row);
            
            // Renumerar itens
            rows = tbody.querySelectorAll('tr');
            rows.forEach(function(row, index) {
                row.querySelector('.item-index').textContent = index + 1;
                
                // Atualizar nomes dos campos
                row.querySelectorAll('[name*="items["]').forEach(function(input) {
                    var name = input.name;
                    var newName = name.replace(/items\[\d+\]/, 'items[' + index + ']');
                    input.name = newName;
                });
            });
            
            // Calcular totais
            calculateOrderTotal();
        } else {
            alert('O pedido deve ter pelo menos um item.');
        }
    }
    
    // Função para configurar event listeners para um item
    function setupItemEventListeners(row) {
        // Event listener para seleção de produto
        var productSelect = row.querySelector('.product-select');
        if (productSelect) {
            productSelect.addEventListener('change', function() {
                var productId = this.value;
                if (productId) {
                    loadProductData(productId, row);
                } else {
                    row.querySelector('.item-unit').value = '';
                    row.querySelector('.item-price').value = '';
                    calculateItemTotal(row);
                    calculateOrderTotal();
                }
            });
        }
        
        // Event listeners para quantidade, preço e desconto
        var quantityInput = row.querySelector('.item-quantity');
        var priceInput = row.querySelector('.item-price');
        var discountInput = row.querySelector('.item-discount');
        
        if (quantityInput) {
            quantityInput.addEventListener('input', function() {
                calculateItemTotal(row);
                calculateOrderTotal();
            });
        }
        
        if (priceInput) {
            priceInput.addEventListener('input', function() {
                calculateItemTotal(row);
                calculateOrderTotal();
            });
        }
        
        if (discountInput) {
            discountInput.addEventListener('input', function() {
                calculateItemTotal(row);
                calculateOrderTotal();
            });
        }
        
        // Event listener para botão de remover
        var removeButton = row.querySelector('.remove-item');
        if (removeButton) {
            removeButton.addEventListener('click', function() {
                removeItem(this);
            });
        }
    }
    
    // Função principal executada quando o DOM estiver pronto
    function init() {
        console.log('Inicializando formulário de pedidos de compra simplificado...');
        
        // Event listener para o fornecedor
        var supplierSelect = document.getElementById('supplier_id');
        if (supplierSelect) {
            supplierSelect.addEventListener('change', function() {
                var supplierId = this.value;
                if (supplierId) {
                    loadSupplierData(supplierId);
                } else {
                    document.getElementById('supplier_tax_id').value = '';
                    document.getElementById('contact_name').value = '';
                    document.getElementById('delivery_address').value = '';
                }
            });
            
            // Carregar dados do fornecedor se já estiver selecionado
            if (supplierSelect.value) {
                loadSupplierData(supplierSelect.value);
            }
        }
        
        // Event listener para o botão de adicionar item
        var addItemButton = document.getElementById('addItem');
        if (addItemButton) {
            addItemButton.addEventListener('click', addNewItem);
        }
        
        // Configurar event listeners para os itens existentes
        var rows = document.querySelectorAll('#itemsTable tbody tr');
        rows.forEach(function(row) {
            setupItemEventListeners(row);
        });
        
        // Event listeners para campos que afetam o total
        ['discount_percent', 'shipping_cost', 'insurance_cost', 'other_costs', 'tax_value'].forEach(function(id) {
            var element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', calculateOrderTotal);
            }
        });
        
        // Calcular totais iniciais
        calculateOrderTotal();
    }
    
    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
