/**
 * JavaScript para o módulo de Romaneio de Vendas
 */

// Função para calcular o total de um item
function calcularTotalItem(row) {
    var quantidade = parseFloat($(row).find('.quantidade-input').val()) || 0;
    var preco = parseFloat($(row).find('.preco-input').val()) || 0;
    var total = quantidade * preco;
    $(row).find('.total-input').val(total.toFixed(2));
    return total;
}

// Função para calcular o total do pedido
function calcularTotalPedido(containerId, totalId) {
    var total = 0;
    $('#' + containerId + ' .item-row').each(function() {
        total += calcularTotalItem(this);
    });
    $('#' + totalId).text(total.toFixed(2));
}

// Função para inicializar os eventos do romaneio
function initRomaneio(visitaId) {
    // Adicionar item ao pedido
    $('#add-item' + visitaId).click(function() {
        var newRow = $('#items-container' + visitaId + ' .item-row').first().clone();
        newRow.find('input').val('');
        newRow.find('select').val('');
        $('#items-container' + visitaId).append(newRow);
        
        // Recalcular totais quando os valores mudarem
        newRow.find('.quantidade-input, .preco-input').on('input', function() {
            calcularTotalPedido('items-container' + visitaId, 'total-pedido' + visitaId);
        });
        
        // Remover item
        newRow.find('.remove-item').click(function() {
            $(this).closest('.item-row').remove();
            calcularTotalPedido('items-container' + visitaId, 'total-pedido' + visitaId);
        });
    });
    
    // Inicializar eventos para a primeira linha
    $('#items-container' + visitaId + ' .quantidade-input, #items-container' + visitaId + ' .preco-input').on('input', function() {
        calcularTotalPedido('items-container' + visitaId, 'total-pedido' + visitaId);
    });
    
    $('#items-container' + visitaId + ' .remove-item').click(function() {
        if ($('#items-container' + visitaId + ' .item-row').length > 1) {
            $(this).closest('.item-row').remove();
            calcularTotalPedido('items-container' + visitaId, 'total-pedido' + visitaId);
        }
    });
}
