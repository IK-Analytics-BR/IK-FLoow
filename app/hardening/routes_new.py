from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

hardening_bp = Blueprint('hardening', __name__)

@hardening_bp.route('/audit-logs', methods=['GET'])
@login_required
def audit_logs():
    """Exibe os logs de auditoria."""
    # Verificar se o usuário é administrador
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html', title="Logs de Auditoria")

@hardening_bp.route('/backups', methods=['GET'])
@login_required
def backups():
    """Exibe a lista de backups disponíveis."""
    # Verificar se o usuário é administrador
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html', title="Gerenciamento de Backups")
