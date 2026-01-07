/**
 * Função para exibir badge de ambiente e modelo NFe
 * @param {string} ambiente - 'producao' ou 'homologacao'
 * @param {string} modelo - 'antigo' ou 'reforma'
 */
function exibirBadgeAmbiente(ambiente, modelo) {
    const badgeContainer = document.getElementById('badge-ambiente');
    const badgeAmbiente = document.getElementById('badge-ambiente-texto');
    const badgeModelo = document.getElementById('badge-modelo-texto');
    
    if (!badgeContainer || !badgeAmbiente || !badgeModelo) {
        console.warn('[NFE] Elementos de badge não encontrados');
        return;
    }
    
    // Configurar badge de ambiente
    if (ambiente === 'producao') {
        badgeAmbiente.className = 'badge bg-danger';
        badgeAmbiente.innerHTML = '<i class="fas fa-exclamation-triangle"></i> PRODUÇÃO';
    } else {
        badgeAmbiente.className = 'badge bg-warning text-dark';
        badgeAmbiente.innerHTML = '<i class="fas fa-flask"></i> HOMOLOGAÇÃO';
    }
    
    // Configurar badge de modelo
    if (modelo === 'reforma') {
        badgeModelo.className = 'badge bg-success';
        badgeModelo.innerHTML = '<i class="fas fa-star"></i> REFORMA (IBS/CBS/IS)';
    } else {
        badgeModelo.className = 'badge bg-secondary';
        badgeModelo.innerHTML = '<i class="fas fa-file-alt"></i> ANTIGO';
    }
    
    // Exibir container
    badgeContainer.style.display = 'block';
    
    console.log(`[NFE] Badge exibido: ${ambiente.toUpperCase()} - ${modelo.toUpperCase()}`);
}
