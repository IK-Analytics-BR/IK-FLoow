// Script para busca de NCM e CFOP

// Função para buscar NCM quando o campo perder o foco
$(document).ready(function() {
    // Busca de NCM ao perder o foco
    $('#ncm').on('blur', function() {
        var codigo = $(this).val();
        
        if (codigo.length > 0) {
            // Buscar detalhes do NCM
            $.ajax({
                url: '/api/ncms/' + codigo,
                dataType: 'json',
                success: function(data) {
                    if (data.success) {
                        $('#ncm_description').val(data.ncm.descricao);
                    } else {
                        $('#ncm_description').val('');
                    }
                },
                error: function() {
                    $('#ncm_description').val('');
                }
            });
        } else {
            $('#ncm_description').val('');
        }
    });
    
    // Busca de CFOP ao perder o foco
    $('#cfop_in, #cfop_out').on('blur', function() {
        var codigo = $(this).val();
        var targetDescField = $(this).attr('id') === 'cfop_in' ? 'cfop_in_description' : 'cfop_out_description';
        
        if (codigo.length > 0) {
            // Buscar detalhes do CFOP
            $.ajax({
                url: '/api/cfops/' + codigo,
                dataType: 'json',
                success: function(data) {
                    if (data.success) {
                        $('#' + targetDescField).val(data.cfop.descricao);
                    } else {
                        $('#' + targetDescField).val('');
                    }
                },
                error: function() {
                    $('#' + targetDescField).val('');
                }
            });
        } else {
            $('#' + targetDescField).val('');
        }
    });
    
    // Função para abrir o modal de busca de NCM
    $('#searchNcmBtn').on('click', function() {
        $('#ncmSearchModal').modal('show');
    });
    
    // Função para abrir o modal de busca de CFOP
    $('#searchCfopInBtn, #searchCfopOutBtn').on('click', function() {
        var targetField = $(this).closest('.input-group').find('input').attr('id');
        var targetDescField = targetField === 'cfop_in' ? 'cfop_in_description' : 'cfop_out_description';
        
        $('#targetCfopField').val(targetField);
        $('#targetCfopDescField').val(targetDescField);
        $('#cfopSearchModal').modal('show');
    });
    
    // Buscar NCMs quando o botão for clicado
    $('#ncmSearchButton').on('click', function() {
        searchNCM();
    });
    
    // Buscar NCMs quando Enter for pressionado no campo de busca
    $('#ncmSearchInput').on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            searchNCM();
        }
    });
    
    // Função para buscar NCMs
    function searchNCM() {
        var searchTerm = $('#ncmSearchInput').val();
        
        if (searchTerm.length < 3) {
            alert('Digite pelo menos 3 caracteres para buscar.');
            return;
        }
        
        // Limpar a tabela de resultados
        $('#ncmResultsTable tbody').empty();
        
        // Mostrar indicador de carregamento
        $('#ncmResultsTable tbody').append('<tr><td colspan="3" class="text-center">Carregando...</td></tr>');
        
        // Buscar NCMs via API
        $.ajax({
            url: '/api/ncms/search',
            data: { term: searchTerm },
            dataType: 'json',
            success: function(data) {
                // Limpar a tabela de resultados
                $('#ncmResultsTable tbody').empty();
                
                if (data.results && data.results.length > 0) {
                    // Adicionar resultados à tabela
                    data.results.forEach(function(item) {
                        var parts = item.text.split(' - ');
                        var codigo = parts[0];
                        var descricao = parts.slice(1).join(' - ');
                        
                        var row = '<tr>' +
                            '<td>' + codigo + '</td>' +
                            '<td>' + descricao + '</td>' +
                            '<td>' +
                                '<button class="btn btn-sm btn-primary select-ncm-btn" data-codigo="' + codigo + '" data-descricao="' + descricao + '">' +
                                '<i class="fas fa-check"></i> Selecionar' +
                                '</button>' +
                            '</td>' +
                        '</tr>';
                        
                        $('#ncmResultsTable tbody').append(row);
                    });
                } else {
                    $('#ncmResultsTable tbody').append('<tr><td colspan="3" class="text-center">Nenhum NCM encontrado para "' + searchTerm + '"</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                $('#ncmResultsTable tbody').empty();
                $('#ncmResultsTable tbody').append('<tr><td colspan="3" class="text-center">Erro ao buscar NCMs: ' + error + '</td></tr>');
                console.error('Erro na busca de NCM:', xhr.responseText);
            }
        });
    }
    
    // Selecionar NCM quando o botão for clicado
    $(document).on('click', '.select-ncm-btn', function() {
        var codigo = $(this).data('codigo');
        var descricao = $(this).data('descricao');
        
        // Preencher os campos do formulário
        $('#ncm').val(codigo);
        $('#ncm_description').val(descricao);
        
        // Fechar o modal
        $('#ncmSearchModal').modal('hide');
    });
    
    // Buscar CFOPs quando o botão for clicado
    $('#cfopSearchButton').on('click', function() {
        searchCFOP();
    });
    
    // Buscar CFOPs quando Enter for pressionado no campo de busca
    $('#cfopSearchInput').on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            searchCFOP();
        }
    });
    
    // Função para buscar CFOPs
    function searchCFOP() {
        var searchTerm = $('#cfopSearchInput').val();
        
        if (searchTerm.length < 2) {
            alert('Digite pelo menos 2 caracteres para buscar.');
            return;
        }
        
        // Limpar a tabela de resultados
        $('#cfopResultsTable tbody').empty();
        
        // Mostrar indicador de carregamento
        $('#cfopResultsTable tbody').append('<tr><td colspan="3" class="text-center">Carregando...</td></tr>');
        
        // Buscar CFOPs via API
        $.ajax({
            url: '/api/cfops/search',
            data: { term: searchTerm },
            dataType: 'json',
            success: function(data) {
                // Limpar a tabela de resultados
                $('#cfopResultsTable tbody').empty();
                
                if (data.results && data.results.length > 0) {
                    // Adicionar resultados à tabela
                    data.results.forEach(function(item) {
                        var parts = item.text.split(' - ');
                        var codigo = parts[0];
                        var descricao = parts.slice(1).join(' - ');
                        
                        var row = '<tr>' +
                            '<td>' + codigo + '</td>' +
                            '<td>' + descricao + '</td>' +
                            '<td>' +
                                '<button class="btn btn-sm btn-primary select-cfop-btn" data-codigo="' + codigo + '" data-descricao="' + descricao + '">' +
                                '<i class="fas fa-check"></i> Selecionar' +
                                '</button>' +
                            '</td>' +
                        '</tr>';
                        
                        $('#cfopResultsTable tbody').append(row);
                    });
                } else {
                    $('#cfopResultsTable tbody').append('<tr><td colspan="3" class="text-center">Nenhum CFOP encontrado para "' + searchTerm + '"</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                $('#cfopResultsTable tbody').empty();
                $('#cfopResultsTable tbody').append('<tr><td colspan="3" class="text-center">Erro ao buscar CFOPs: ' + error + '</td></tr>');
                console.error('Erro na busca de CFOP:', xhr.responseText);
            }
        });
    }
    
    // Selecionar CFOP quando o botão for clicado
    $(document).on('click', '.select-cfop-btn', function() {
        var codigo = $(this).data('codigo');
        var descricao = $(this).data('descricao');
        
        // Preencher os campos do formulário
        var targetField = $('#targetCfopField').val();
        var targetDescField = $('#targetCfopDescField').val();
        
        $('#' + targetField).val(codigo);
        $('#' + targetDescField).val(descricao);
        
        // Fechar o modal
        $('#cfopSearchModal').modal('hide');
    });
});
