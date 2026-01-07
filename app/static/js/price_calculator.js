/**
 * Script para formatação de preços e cálculo de markup
 */

$(document).ready(function() {
    // Configurar os campos de preço para aceitar até 8 casas decimais
    $('#cost_price, #price').attr('step', '0.00000001');
    
    // Formatar os campos de preço como moeda brasileira (R$)
    function formatAsCurrency(value) {
        if (!value) return '';
        
        // Converter para número e garantir até 8 casas decimais
        const numValue = parseFloat(value);
        if (isNaN(numValue)) return '';
        
        // Formatar como moeda brasileira
        return numValue.toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 8
        });
    }
    
    // Função para exibir o valor formatado em um elemento ao lado do campo
    function updateFormattedPrice(inputField, formattedField) {
        const value = $(inputField).val();
        if (value) {
            $(formattedField).text(formatAsCurrency(value));
        } else {
            $(formattedField).text('');
        }
    }
    
    // Adicionar elementos para exibir os valores formatados
    $('#cost_price').after('<div class="formatted-price" id="formatted_cost_price"></div>');
    $('#price').after('<div class="formatted-price" id="formatted_price"></div>');
    
    // Atualizar os valores formatados quando os campos mudarem
    $('#cost_price').on('input change', function() {
        updateFormattedPrice('#cost_price', '#formatted_cost_price');
        calculateSalePrice();
    });
    
    $('#price').on('input change', function() {
        updateFormattedPrice('#price', '#formatted_price');
        calculateMargin();
    });
    
    $('#margin').on('input change', function() {
        calculateSalePrice();
    });
    
    // Função para calcular o preço de venda com base no custo e markup
    window.calculateSalePrice = function() {
        const costPrice = parseFloat($('#cost_price').val()) || 0;
        const margin = parseFloat($('#margin').val()) || 0;
        
        if (costPrice > 0 && margin > 0) {
            // Calcular o preço de venda usando markup
            const salePrice = costPrice * (1 + margin / 100);
            
            // Manter até 8 casas decimais
            const formattedSalePrice = salePrice.toFixed(8);
            
            // Atualizar o campo de preço de venda
            $('#price').val(formattedSalePrice);
            
            // Atualizar o valor formatado
            updateFormattedPrice('#price', '#formatted_price');
        }
    };
    
    // Função para calcular a margem quando o preço de venda é alterado manualmente
    window.calculateMargin = function() {
        const costPrice = parseFloat($('#cost_price').val()) || 0;
        const salePrice = parseFloat($('#price').val()) || 0;
        
        if (costPrice > 0 && salePrice > 0) {
            // Calcular a margem com base no preço de venda e custo
            const margin = ((salePrice / costPrice) - 1) * 100;
            
            // Arredondar para duas casas decimais
            const roundedMargin = Math.round(margin * 100) / 100;
            
            // Atualizar o campo de margem
            $('#margin').val(roundedMargin.toFixed(2));
        }
    };
    
    // Inicializar os valores formatados
    updateFormattedPrice('#cost_price', '#formatted_cost_price');
    updateFormattedPrice('#price', '#formatted_price');
});

// Adicionar estilos para os valores formatados
$(document).ready(function() {
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            .formatted-price {
                color: #198754;
                font-weight: bold;
                margin-top: 5px;
                font-size: 0.9rem;
            }
            .input-group .formatted-price {
                margin-left: 10px;
            }
        `)
        .appendTo('head');
});
