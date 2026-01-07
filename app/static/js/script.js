// Script personalizado para o Sistema de Gestão de Suprimentos

// Função para inicializar tooltips do Bootstrap
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Função para inicializar popovers do Bootstrap
function initPopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Função para confirmar exclusão
function confirmarExclusao(event, mensagem) {
    if (!confirm(mensagem || 'Tem certeza que deseja excluir este item?')) {
        event.preventDefault();
        return false;
    }
    return true;
}

// Função para formatar campos de CNPJ
function formatarCNPJ(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 14) {
        value = value.slice(0, 14);
    }
    
    if (value.length > 12) {
        value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
    } else if (value.length > 8) {
        value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d+)$/, '$1.$2.$3/$4');
    } else if (value.length > 5) {
        value = value.replace(/^(\d{2})(\d{3})(\d+)$/, '$1.$2.$3');
    } else if (value.length > 2) {
        value = value.replace(/^(\d{2})(\d+)$/, '$1.$2');
    }
    
    input.value = value;
}

// Função para formatar campos de telefone
function formatarTelefone(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 11) {
        value = value.slice(0, 11);
    }
    
    if (value.length > 10) {
        value = value.replace(/^(\d{2})(\d{5})(\d{4})$/, '($1) $2-$3');
    } else if (value.length > 6) {
        value = value.replace(/^(\d{2})(\d{4})(\d+)$/, '($1) $2-$3');
    } else if (value.length > 2) {
        value = value.replace(/^(\d{2})(\d+)$/, '($1) $2');
    }
    
    input.value = value;
}

// Função para formatar campos de CEP
function formatarCEP(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 8) {
        value = value.slice(0, 8);
    }
    
    if (value.length > 5) {
        value = value.replace(/^(\d{5})(\d{3})$/, '$1-$2');
    }
    
    input.value = value;
}

// Inicializa os componentes quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initPopovers();
    
    // Adiciona formatação para campos específicos
    document.querySelectorAll('.cnpj-mask').forEach(function(input) {
        input.addEventListener('input', function() { formatarCNPJ(this); });
    });
    
    document.querySelectorAll('.telefone-mask').forEach(function(input) {
        input.addEventListener('input', function() { formatarTelefone(this); });
    });
    
    document.querySelectorAll('.cep-mask').forEach(function(input) {
        input.addEventListener('input', function() { formatarCEP(this); });
    });
    
    // Adiciona confirmação para links de exclusão
    document.querySelectorAll('.confirmar-exclusao').forEach(function(link) {
        link.addEventListener('click', function(event) {
            return confirmarExclusao(event, this.getAttribute('data-mensagem'));
        });
    });
});
