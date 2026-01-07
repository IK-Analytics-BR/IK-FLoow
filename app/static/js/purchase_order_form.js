document.addEventListener('DOMContentLoaded', function() {
    // Inicializar Select2 para fornecedores
    $('#supplier_id').select2({
        theme: 'bootstrap-5',
        placeholder: 'Selecione um fornecedor'
    });

    // Inicializar Select2 para produtos
    $('.product-select').select2({
        theme: 'bootstrap-5',
        placeholder: 'Selecione um produto'
    });
    
    // Carregar dados do fornecedor ao iniciar a página se já houver um fornecedor selecionado
    const initialSupplierId = $('#supplier_id').val();
    if (initialSupplierId) {
        loadSupplierData(initialSupplierId);
    }

    // Função para carregar dados do fornecedor
    function loadSupplierData(supplierId) {
        if (!supplierId) return;
        
        // Buscar informações do fornecedor via AJAX
        $.ajax({
            url: '/api/suppliers/' + supplierId,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                console.log('Resposta da API de fornecedor:', data);
                
                // Preencher CNPJ/CPF do fornecedor
                $('#supplier_tax_id').val(data.tax_id || '');
                
                // Preencher outros campos
                $('#contact_name').val(data.contact_name || '');
                $('#delivery_address').val(data.address || '');
                
                // Preencher cidade e estado se disponíveis
                if (data.city && data.state) {
                    let addressText = $('#delivery_address').val();
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
                console.error('Erro ao buscar informações do fornecedor:', error);
                console.error('Status:', status);
                console.error('Resposta:', xhr.responseText);
            }
        });
    }
    
    // Atualizar informações do fornecedor quando selecionado
    $('#supplier_id').on('change', function() {
        const supplierId = $(this).val();
        loadSupplierData(supplierId);
        
        if (!supplierId) {
            $('#supplier_tax_id').val('');
            $('#contact_name').val('');
            $('#delivery_address').val('');
        }
    });

    // Adicionar novo item
    $('#addItem').on('click', function() {
        console.log('Botão Adicionar Item clicado');
        
        try {
            const tbody = $('#itemsTable tbody');
            console.log('Tbody encontrado:', tbody.length > 0);
            
            const template = document.getElementById('itemTemplate');
            console.log('Template encontrado:', template !== null);
            
            if (!template) {
                console.error('Elemento template não encontrado!');
                alert('Erro ao adicionar item: template não encontrado');
                return;
            }
            
            const templateContent = template.content.cloneNode(true);
            console.log('Template clonado com sucesso');
            
            const index = tbody.find('tr').length;
            console.log('Número de linhas existentes:', index);
            
            // Atualizar índices
            const indexCell = templateContent.querySelector('.item-index');
            if (indexCell) {
                indexCell.textContent = index + 1;
            }
            
            // Atualizar nomes dos campos
            const inputs = templateContent.querySelectorAll('[name*="INDEX"]');
            console.log('Inputs encontrados:', inputs.length);
            
            inputs.forEach(input => {
                const oldName = input.name;
                input.name = input.name.replace('INDEX', index);
                console.log(`Nome atualizado: ${oldName} -> ${input.name}`);
            });
            
            // Adicionar à tabela
            tbody.append(templateContent);
            
            // Inicializar Select2 para o novo produto
            $('.product-select').last().select2({
                theme: 'bootstrap-5',
                placeholder: 'Selecione um produto'
            });
            
            // Adicionar event listeners
            setupItemEventListeners(tbody.find('tr').last());
            
            // Recalcular totais
            calculateTotals();
        } catch (error) {
            console.error('Erro ao adicionar item:', error);
            alert('Erro ao adicionar item: ' + error.message);
        }
    });

    // Remover item
    $(document).on('click', '.remove-item', function() {
        const tbody = $('#itemsTable tbody');
        if (tbody.find('tr').length > 1) {
            $(this).closest('tr').remove();
            
            // Renumerar itens
            tbody.find('tr').each(function(index) {
                $(this).find('.item-index').text(index + 1);
                
                // Atualizar nomes dos campos
                $(this).find('[name*="items["]').each(function() {
                    const name = $(this).attr('name');
                    const newName = name.replace(/items\[\d+\]/, 'items[' + index + ']');
                    $(this).attr('name', newName);
                });
            });
            
            // Recalcular totais
            calculateTotals();
        } else {
            alert('O pedido deve ter pelo menos um item.');
        }
    });

    // Configurar event listeners para os itens existentes
    $('#itemsTable tbody tr').each(function() {
        setupItemEventListeners($(this));
    });

    // Calcular totais iniciais
    calculateTotals();

    // Event listeners para campos que afetam o total
    $('#discount_percent, #shipping_cost, #insurance_cost, #other_costs, #tax_value').on('input', calculateTotals);

    // Função para configurar event listeners para um item
    function setupItemEventListeners(row) {
        // Quando selecionar um produto
        row.find('.product-select').on('change', function() {
            const productId = $(this).val();
            console.log('Produto selecionado:', productId);
            
            if (!productId) {
                row.find('.item-unit').val('');
                row.find('.item-price').val('');
                calculateItemTotal(row);
                calculateTotals();
                return;
            }
            
            // Usar dados do option selecionado
            const option = $(this).find('option:selected');
            console.log('Option selecionada:', option.text());
            console.log('Dados do option - unit:', option.data('unit'), 'price:', option.data('price'));
            
            const unit = option.data('unit');
            const price = option.data('price');
            
            // Preencher campos com os dados do option
            row.find('.item-unit').val(unit || '');
            row.find('.item-price').val(price || 0);
            
            // Definir quantidade padrão se estiver vazia
            if (!row.find('.item-quantity').val()) {
                row.find('.item-quantity').val(1);
            }
            
            calculateItemTotal(row);
            calculateTotals();
            
            // Buscar informações detalhadas do produto via API
            console.log('Buscando informações do produto via API:', productId);
            
            $.ajax({
                url: '/api/products/' + productId,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    console.log('Resposta da API de produto:', data);
                    
                    // Preencher unidade de medida se estiver disponível
                    if (data.unit_measure) {
                        console.log('Unidade de medida encontrada:', data.unit_measure);
                        row.find('.item-unit').val(data.unit_measure);
                    }
                    
                    // Usar o último preço de compra ou o preço de custo
                    if (data.last_purchase_price && data.last_purchase_price > 0) {
                        console.log('Último preço de compra encontrado:', data.last_purchase_price);
                        row.find('.item-price').val(data.last_purchase_price);
                        
                        // Adicionar tooltip com informação da última compra
                        if (data.last_purchase_date) {
                            row.find('.item-price').attr('title', `Última compra em ${data.last_purchase_date}`);
                            row.find('.item-price').tooltip({placement: 'top'});
                        }
                    } else if (data.cost_price && data.cost_price > 0) {
                        console.log('Preço de custo encontrado:', data.cost_price);
                        row.find('.item-price').val(data.cost_price);
                    }
                    
                    calculateItemTotal(row);
                    calculateTotals();
                },
                error: function(xhr, status, error) {
                    console.error('Erro ao buscar informações do produto:', error);
                    console.error('Status:', status);
                    console.error('Resposta:', xhr.responseText);
                }
            });
        });
        
        // Quando alterar quantidade, preço ou desconto
        row.find('.item-quantity, .item-price, .item-discount').on('input', function() {
            calculateItemTotal(row);
            calculateTotals();
        });
    }

    // Calcular total de um item
    function calculateItemTotal(row) {
        const quantity = parseFloat(row.find('.item-quantity').val()) || 0;
        const price = parseFloat(row.find('.item-price').val()) || 0;
        const discount = parseFloat(row.find('.item-discount').val()) || 0;
        
        const totalBeforeDiscount = quantity * price;
        const discountAmount = totalBeforeDiscount * (discount / 100);
        const total = totalBeforeDiscount - discountAmount;
        
        // Formatar o valor com 2 casas decimais
        row.find('.item-total').val(total.toFixed(2));
        
        // Adicionar tooltip com detalhes do cálculo
        const tooltipText = `
            Quantidade: ${quantity}
            Preço Unit.: R$ ${price.toFixed(2)}
            Subtotal: R$ ${totalBeforeDiscount.toFixed(2)}
            Desconto (${discount}%): R$ ${discountAmount.toFixed(2)}
            Total: R$ ${total.toFixed(2)}
        `;
        
        row.find('.item-total').attr('title', tooltipText);
        if (!row.find('.item-total').data('bs-tooltip')) {
            row.find('.item-total').tooltip({placement: 'left'});
        }
    }

    // Calcular totais do pedido
    function calculateTotals() {
        let subtotal = 0;
        let itemCount = 0;
        
        // Somar totais dos itens
        $('#itemsTable tbody tr').each(function() {
            const total = parseFloat($(this).find('.item-total').val()) || 0;
            if (total > 0) {
                subtotal += total;
                itemCount++;
            }
        });
        
        // Atualizar subtotal
        $('#subtotal').val(subtotal.toFixed(2));
        
        // Calcular desconto
        const discountPercent = parseFloat($('#discount_percent').val()) || 0;
        const discountValue = subtotal * (discountPercent / 100);
        $('#discount_value').val(discountValue.toFixed(2));
        
        // Outros valores
        const shippingCost = parseFloat($('#shipping_cost').val()) || 0;
        const insuranceCost = parseFloat($('#insurance_cost').val()) || 0;
        const otherCosts = parseFloat($('#other_costs').val()) || 0;
        const taxValue = parseFloat($('#tax_value').val()) || 0;
        
        // Calcular total
        const totalValue = subtotal - discountValue + shippingCost + insuranceCost + otherCosts + taxValue;
        $('#total_value').val(totalValue.toFixed(2));
        
        // Atualizar resumo do pedido
        const resumoHtml = `
            <div class="alert alert-info mt-3">
                <h5>Resumo do Pedido</h5>
                <p><strong>${itemCount}</strong> ${itemCount === 1 ? 'item' : 'itens'} no pedido</p>
                <p>Subtotal: R$ ${subtotal.toFixed(2)}</p>
                ${discountValue > 0 ? `<p>Desconto (${discountPercent}%): R$ ${discountValue.toFixed(2)}</p>` : ''}
                ${shippingCost > 0 ? `<p>Frete: R$ ${shippingCost.toFixed(2)}</p>` : ''}
                ${insuranceCost > 0 ? `<p>Seguro: R$ ${insuranceCost.toFixed(2)}</p>` : ''}
                ${otherCosts > 0 ? `<p>Outros custos: R$ ${otherCosts.toFixed(2)}</p>` : ''}
                ${taxValue > 0 ? `<p>Impostos: R$ ${taxValue.toFixed(2)}</p>` : ''}
                <p class="fw-bold">Total: R$ ${totalValue.toFixed(2)}</p>
            </div>
        `;
        
        // Adicionar ou atualizar o resumo
        $('#order-summary').html(resumoHtml);
    }
});
