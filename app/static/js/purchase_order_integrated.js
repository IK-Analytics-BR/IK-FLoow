/**
 * Script integrado para o formulário de pedidos de compra
 * Compatível com o restante do sistema e evita conflitos
 */

// Usar IIFE para evitar poluição do escopo global
(function() {
    // Verificar se o jQuery está disponível
    if (typeof jQuery === 'undefined') {
        console.error('jQuery não está disponível. Este script requer jQuery.');
        return;
    }

    // Verificar se o Bootstrap está disponível
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap não está disponível. Este script requer Bootstrap.');
        return;
    }

    // Função para carregar dados do fornecedor
    function loadSupplierData(supplierId) {
        if (!supplierId) return;
        
        console.log('Carregando dados do fornecedor:', supplierId);
        
        // Mostrar indicador de carregamento
        $('#supplier_tax_id').val('Carregando...');
        
        // Usar jQuery para fazer a requisição AJAX
        $.ajax({
            url: '/api/suppliers/' + supplierId,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                console.log('Dados do fornecedor:', data);
                
                // Preencher campos com os dados do fornecedor
                $('#supplier_tax_id').val(data.tax_id || '');
                $('#contact_name').val(data.contact_name || '');
                $('#delivery_address').val(data.address || '');
                
                // Adicionar cidade e estado ao endereço se disponíveis
                if (data.city && data.state) {
                    var addressText = $('#delivery_address').val();
                    if (addressText && !addressText.includes(data.city)) {
                        addressText += '\n' + data.city + ' - ' + data.state;
                        if (data.zip_code) {
                            addressText += '\nCEP: ' + data.zip_code;
                        }
                        $('#delivery_address').val(addressText);
                    }
                }
            },
            error: function(xhr, status, error) {
                console.error('Erro ao buscar fornecedor:', error);
                $('#supplier_tax_id').val('');
            }
        });
    }
    
    // Função para carregar dados do produto
    function loadProductData(productId, row) {
        if (!productId) return;
        
        console.log('Carregando dados do produto:', productId);
        
        // Mostrar indicador de carregamento
        row.find('.item-unit').val('Carregando...');
        row.find('.item-price').val('');
        
        // Usar jQuery para fazer a requisição AJAX
        $.ajax({
            url: '/api/products/' + productId,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                console.log('Dados do produto:', data);
                
                // Preencher campos com os dados do produto
                row.find('.item-unit').val(data.unit_measure || '');
                
                // Usar o último preço de compra ou o preço de custo
                if (data.last_purchase_price && data.last_purchase_price > 0) {
                    row.find('.item-price').val(data.last_purchase_price);
                    
                    // Adicionar tooltip com informação da última compra
                    if (data.last_purchase_date) {
                        row.find('.item-price').attr('title', 'Última compra em ' + data.last_purchase_date);
                        
                        // Inicializar tooltip se o Bootstrap estiver disponível
                        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                            var tooltip = new bootstrap.Tooltip(row.find('.item-price')[0], {
                                placement: 'top'
                            });
                        }
                    }
                } else if (data.cost_price && data.cost_price > 0) {
                    row.find('.item-price').val(data.cost_price);
                }
                
                // Calcular total
                calculateItemTotal(row);
                calculateOrderTotal();
            },
            error: function(xhr, status, error) {
                console.error('Erro ao buscar produto:', error);
                row.find('.item-unit').val('');
                row.find('.item-price').val('');
            }
        });
    }
    
    // Função para calcular o total de um item
    function calculateItemTotal(row) {
        var quantity = parseFloat(row.find('.item-quantity').val()) || 0;
        var price = parseFloat(row.find('.item-price').val()) || 0;
        var discount = parseFloat(row.find('.item-discount').val()) || 0;
        
        var totalBeforeDiscount = quantity * price;
        var discountAmount = totalBeforeDiscount * (discount / 100);
        var total = totalBeforeDiscount - discountAmount;
        
        row.find('.item-total').val(total.toFixed(2));
        
        // Adicionar tooltip com detalhes do cálculo
        var tooltipText = 'Quantidade: ' + quantity + '\n' +
                         'Preço Unit.: R$ ' + price.toFixed(2) + '\n' +
                         'Subtotal: R$ ' + totalBeforeDiscount.toFixed(2) + '\n' +
                         'Desconto (' + discount + '%): R$ ' + discountAmount.toFixed(2) + '\n' +
                         'Total: R$ ' + total.toFixed(2);
        
        row.find('.item-total').attr('title', tooltipText);
        
        // Inicializar tooltip se o Bootstrap estiver disponível
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            var tooltip = new bootstrap.Tooltip(row.find('.item-total')[0], {
                placement: 'left'
            });
        }
    }
    
    // Função para calcular o total do pedido
    function calculateOrderTotal() {
        var subtotal = 0;
        var itemCount = 0;
        
        // Somar totais dos itens
        $('#itemsTable tbody tr').each(function() {
            var total = parseFloat($(this).find('.item-total').val()) || 0;
            if (total > 0) {
                subtotal += total;
                itemCount++;
            }
        });
        
        // Atualizar subtotal
        $('#subtotal').val(subtotal.toFixed(2));
        
        // Calcular desconto
        var discountPercent = parseFloat($('#discount_percent').val()) || 0;
        var discountValue = subtotal * (discountPercent / 100);
        $('#discount_value').val(discountValue.toFixed(2));
        
        // Outros valores
        var shippingCost = parseFloat($('#shipping_cost').val()) || 0;
        var insuranceCost = parseFloat($('#insurance_cost').val()) || 0;
        var otherCosts = parseFloat($('#other_costs').val()) || 0;
        var taxValue = parseFloat($('#tax_value').val()) || 0;
        
        // Calcular total
        var totalValue = subtotal - discountValue + shippingCost + insuranceCost + otherCosts + taxValue;
        $('#total_value').val(totalValue.toFixed(2));
        
        // Atualizar resumo do pedido
        updateOrderSummary(subtotal, discountPercent, discountValue, shippingCost, insuranceCost, otherCosts, taxValue, totalValue, itemCount);
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
        
        $('#order-summary').html(summaryHtml);
    }
    
    // Função para adicionar um novo item
    function addNewItem() {
        var tbody = $('#itemsTable tbody');
        var template = document.getElementById('itemTemplate');
        
        if (!template) {
            console.error('Template não encontrado!');
            return;
        }
        
        var clone = document.importNode(template.content, true);
        var index = tbody.find('tr').length;
        
        // Atualizar índice
        var indexCell = $(clone).find('.item-index');
        if (indexCell.length) {
            indexCell.text(index + 1);
        }
        
        // Atualizar nomes dos campos
        $(clone).find('[name*="INDEX"]').each(function() {
            var oldName = $(this).attr('name');
            $(this).attr('name', oldName.replace('INDEX', index));
        });
        
        // Adicionar à tabela
        tbody.append(clone);
        
        // Inicializar Select2 para o novo produto se disponível
        if ($.fn.select2) {
            tbody.find('tr').last().find('.product-select').select2({
                theme: 'bootstrap-5',
                placeholder: 'Selecione um produto'
            });
        }
        
        // Adicionar event listeners para o novo item
        setupItemEventListeners(tbody.find('tr').last());
        
        // Calcular totais
        calculateOrderTotal();
    }
    
    // Função para remover um item
    function removeItem(button) {
        var tbody = $('#itemsTable tbody');
        var rows = tbody.find('tr');
        
        if (rows.length > 1) {
            var row = $(button).closest('tr');
            row.remove();
            
            // Renumerar itens
            tbody.find('tr').each(function(index) {
                $(this).find('.item-index').text(index + 1);
                
                // Atualizar nomes dos campos
                $(this).find('[name*="items["]').each(function() {
                    var name = $(this).attr('name');
                    var newName = name.replace(/items\[\d+\]/, 'items[' + index + ']');
                    $(this).attr('name', newName);
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
        row.find('.product-select').on('change', function() {
            var productId = $(this).val();
            if (productId) {
                loadProductData(productId, row);
            } else {
                row.find('.item-unit').val('');
                row.find('.item-price').val('');
                calculateItemTotal(row);
                calculateOrderTotal();
            }
        });
        
        // Event listeners para quantidade, preço e desconto
        row.find('.item-quantity, .item-price, .item-discount').on('input', function() {
            calculateItemTotal(row);
            calculateOrderTotal();
        });
        
        // Event listener para botão de remover
        row.find('.remove-item').on('click', function() {
            removeItem(this);
        });
    }
    
    // Função principal executada quando o DOM estiver pronto
    function init() {
        console.log('Inicializando formulário de pedidos de compra integrado...');
        
        // Inicializar Select2 para fornecedores se disponível
        if ($.fn.select2) {
            $('#supplier_id').select2({
                theme: 'bootstrap-5',
                placeholder: 'Selecione um fornecedor'
            });
            
            // Inicializar Select2 para produtos se disponível
            $('.product-select').select2({
                theme: 'bootstrap-5',
                placeholder: 'Selecione um produto'
            });
        }
        
        // Event listener para o fornecedor
        $('#supplier_id').on('change', function() {
            var supplierId = $(this).val();
            if (supplierId) {
                loadSupplierData(supplierId);
            } else {
                $('#supplier_tax_id').val('');
                $('#contact_name').val('');
                $('#delivery_address').val('');
            }
        });
        
        // Carregar dados do fornecedor se já estiver selecionado
        var initialSupplierId = $('#supplier_id').val();
        if (initialSupplierId) {
            loadSupplierData(initialSupplierId);
        }
        
        // Event listener para o botão de adicionar item
        $('#addItem').on('click', addNewItem);
        
        // Configurar event listeners para os itens existentes
        $('#itemsTable tbody tr').each(function() {
            setupItemEventListeners($(this));
        });
        
        // Event listeners para campos que afetam o total
        $('#discount_percent, #shipping_cost, #insurance_cost, #other_costs, #tax_value').on('input', calculateOrderTotal);
        
        // Calcular totais iniciais
        calculateOrderTotal();
    }
    
    // Inicializar quando o DOM estiver pronto
    $(document).ready(init);
})();
