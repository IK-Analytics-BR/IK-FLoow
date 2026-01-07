/**
 * Funções para verificação de documentos (CNPJ/CPF) em tempo real
 */

// Função para verificar se um CNPJ/CPF já existe no banco de dados
function checkDocumentExists(documentValue, entityType) {
    // Limpar o valor do documento (remover caracteres especiais)
    const cleanValue = documentValue.replace(/[^\d]/g, '');
    
    // Se o valor estiver vazio ou for muito curto, não fazer a verificação
    if (!cleanValue || cleanValue.length < 8) {
        clearDocumentFeedback();
        return;
    }
    
    // Mostrar indicador de carregamento
    showLoadingIndicator();
    
    // Fazer requisição AJAX para verificar se o documento já existe
    $.ajax({
        url: `/api/check-document?document_value=${encodeURIComponent(cleanValue)}&entity_type=${entityType}`,
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            hideLoadingIndicator();
            
            if (response.exists) {
                // Documento já existe, mostrar modal
                showDuplicateModal(response);
            } else {
                // Documento não existe, mostrar feedback positivo
                showDocumentFeedback('success', 'CNPJ/CPF disponível para cadastro');
                setTimeout(() => {
                    clearDocumentFeedback();
                }, 3000);
            }
        },
        error: function(xhr, status, error) {
            hideLoadingIndicator();
            console.error('Erro ao verificar documento:', error);
        }
    });
}

// ==========================
// Validações de CPF e CNPJ
// ==========================

function isValidCPF(cpfRaw) {
    const cpf = String(cpfRaw).replace(/\D/g, '');
    if (!cpf || cpf.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(cpf)) return false; // todos os dígitos iguais

    let sum = 0;
    for (let i = 0; i < 9; i++) sum += parseInt(cpf.charAt(i), 10) * (10 - i);
    let rev = 11 - (sum % 11);
    if (rev === 10 || rev === 11) rev = 0;
    if (rev !== parseInt(cpf.charAt(9), 10)) return false;

    sum = 0;
    for (let i = 0; i < 10; i++) sum += parseInt(cpf.charAt(i), 10) * (11 - i);
    rev = 11 - (sum % 11);
    if (rev === 10 || rev === 11) rev = 0;
    return rev === parseInt(cpf.charAt(10), 10);
}

function isValidCNPJ(cnpjRaw) {
    const cnpj = String(cnpjRaw).replace(/\D/g, '');
    if (!cnpj || cnpj.length !== 14) return false;
    if (/^(\d)\1{13}$/.test(cnpj)) return false; // todos os dígitos iguais

    const calcDigit = (base) => {
        let length = base.length;
        let numbers = base.substring(0, length);
        let pos = length - 7;
        let sum = 0;
        for (let i = length; i >= 1; i--) {
            sum += parseInt(numbers.charAt(length - i), 10) * pos--;
            if (pos < 2) pos = 9;
        }
        let result = sum % 11;
        return result < 2 ? 0 : 11 - result;
    };

    const d1 = calcDigit(cnpj.substring(0, 12));
    const d2 = calcDigit(cnpj.substring(0, 12) + String(d1));
    return cnpj.endsWith(String(d1) + String(d2));
}

function showInvalidDocument(message) {
    showDocumentFeedback('danger', message);
}

// Função para mostrar o modal de documento duplicado
function showDuplicateModal(data) {
    // Criar o modal dinamicamente
    const modalHtml = `
    <div class="modal fade" id="duplicateDocumentModal" tabindex="-1" aria-labelledby="duplicateDocumentModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-warning text-dark">
                    <h5 class="modal-title" id="duplicateDocumentModalLabel">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Documento já cadastrado
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-warning">
                        <p><strong>Atenção!</strong> O CNPJ/CPF informado já está cadastrado para:</p>
                        <p class="fs-5">${data.entity_name}</p>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header bg-light">
                                    <i class="fas fa-info-circle me-2"></i>
                                    Informações do cadastro existente
                                </div>
                                <div class="card-body">
                                    <p><strong>CNPJ/CPF:</strong> ${data.entity_cnpj}</p>
                                    <p><strong>Nome:</strong> ${data.entity_name}</p>
                                    <p><strong>Cidade/UF:</strong> ${data.entity_city}/${data.entity_state}</p>
                                    <p><strong>Telefone:</strong> ${data.entity_phone}</p>
                                    <p><strong>Email:</strong> ${data.entity_email}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-light">
                                    <i class="fas fa-question-circle me-2"></i>
                                    O que deseja fazer?
                                </div>
                                <div class="card-body">
                                    <p>Escolha uma das opções abaixo:</p>
                                    <div class="d-grid gap-2">
                                        <a href="/${data.entity_type === 'fornecedor' ? 'fornecedores' : data.entity_type + 's'}/editar/${data.entity_id}" class="btn btn-primary">
                                            <i class="fas fa-edit me-2"></i>
                                            Editar cadastro existente
                                        </a>
                                        <a href="/${data.entity_type === 'fornecedor' ? 'fornecedores' : data.entity_type + 's'}/visualizar/${data.entity_id}" class="btn btn-info">
                                            <i class="fas fa-eye me-2"></i>
                                            Visualizar cadastro existente
                                        </a>
                                        <button type="button" class="btn btn-danger mt-2" id="forceCreateBtn">
                                            <i class="fas fa-exclamation-triangle me-2"></i>
                                            Forçar criação de novo cadastro
                                        </button>
                                        <button type="button" class="btn btn-secondary mt-2" data-bs-dismiss="modal">
                                            <i class="fas fa-times me-2"></i>
                                            Cancelar
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // Remover modal anterior se existir
    $('#duplicateDocumentModal').remove();
    
    // Adicionar o modal ao corpo do documento
    $('body').append(modalHtml);
    
    // Mostrar o modal
    const duplicateModal = new bootstrap.Modal(document.getElementById('duplicateDocumentModal'));
    duplicateModal.show();
    
    // Adicionar evento para quando o modal for fechado
    document.getElementById('duplicateDocumentModal').addEventListener('hidden.bs.modal', function () {
        // Remover os estilos indesejados do body
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
    });
    
    // Adicionar evento ao botão de forçar criação
    document.getElementById('forceCreateBtn').addEventListener('click', function() {
        // Fechar o modal
        duplicateModal.hide();
        
        // Remover os estilos indesejados do body
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
        
        // Adicionar um campo oculto ao formulário para indicar que é uma criação forçada
        const form = document.querySelector('form');
        
        // Verificar se já existe um campo force_create
        let forceCreateInput = form.querySelector('input[name="force_create"]');
        if (!forceCreateInput) {
            forceCreateInput = document.createElement('input');
            forceCreateInput.type = 'hidden';
            forceCreateInput.name = 'force_create';
            form.appendChild(forceCreateInput);
        }
        forceCreateInput.value = 'true';
        
        // Mostrar mensagem de aviso
        showDocumentFeedback('warning', '<strong>Atenção!</strong> Você está criando um cadastro com CNPJ/CPF duplicado.');
    });
}

// Função para mostrar feedback sobre o documento
function showDocumentFeedback(type, message) {
    // Remover feedback anterior
    clearDocumentFeedback();
    
    // Criar elemento de feedback
    const feedbackDiv = $('<div>')
        .addClass(`alert alert-${type} mt-2 document-feedback`)
        .html(message);
    
    // Adicionar feedback após o campo de CNPJ/CPF
    $('#cnpj').after(feedbackDiv);
}

// Função para limpar feedback sobre o documento
function clearDocumentFeedback() {
    $('.document-feedback').remove();
}

// Função para mostrar indicador de carregamento
function showLoadingIndicator() {
    clearDocumentFeedback();
    const loadingDiv = $('<div>')
        .addClass('document-feedback text-center mt-2')
        .html('<i class="fas fa-spinner fa-spin"></i> Verificando...');
    $('#cnpj').after(loadingDiv);
}

// Função para esconder indicador de carregamento
function hideLoadingIndicator() {
    $('.document-feedback').remove();
}

// Inicializar eventos quando o documento estiver pronto
$(document).ready(function() {
    // Verificar tipo de formulário (cliente ou fornecedor)
    const isClientForm = window.location.pathname.includes('/clientes/');
    const isSupplierForm = window.location.pathname.includes('/fornecedores/');
    
    if (isClientForm || isSupplierForm) {
        const entityType = isClientForm ? 'cliente' : 'fornecedor';
        
        // Adicionar evento de verificação ao campo de CNPJ/CPF quando perder o foco
        $('#cnpj').on('blur', function() {
            const raw = $(this).val();
            const digits = (raw || '').replace(/\D/g, '');

            clearDocumentFeedback();

            if (!digits) return; // sem valor, não valida

            // Verificar tamanho válido (CPF 11, CNPJ 14)
            if (![11, 14].includes(digits.length)) {
                showInvalidDocument('Documento inválido. Informe um CPF (11 dígitos) ou CNPJ (14 dígitos).');
                return;
            }

            // Validar conforme o tamanho
            const valid = digits.length === 11 ? isValidCPF(digits) : isValidCNPJ(digits);
            if (!valid) {
                showInvalidDocument('Documento inválido. Verifique o CPF/CNPJ informado.');
                return;
            }

            // Apenas se válido, verificar duplicidade
            checkDocumentExists(digits, entityType);
        });
        
        // Adicionar evento para limpar feedback quando o campo for alterado
        $('#cnpj').on('input', function() {
            clearDocumentFeedback();
        });

        // Bloquear envio do formulário se CPF/CNPJ inválido
        $('form').on('submit', function(e) {
            const input = $('#cnpj');
            if (!input.length) return; // sem campo, não valida
            const digits = (input.val() || '').replace(/\D/g, '');
            if (!digits || ![11, 14].includes(digits.length)) {
                e.preventDefault();
                showInvalidDocument('Documento inválido. Informe um CPF (11 dígitos) ou CNPJ (14 dígitos).');
                input.focus();
                return false;
            }
            const valid = digits.length === 11 ? isValidCPF(digits) : isValidCNPJ(digits);
            if (!valid) {
                e.preventDefault();
                showInvalidDocument('Documento inválido. Verifique o CPF/CNPJ informado.');
                input.focus();
                return false;
            }
            return true;
        });
    }
});
