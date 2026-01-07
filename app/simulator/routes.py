from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

simulator_bp = Blueprint('simulator', __name__)

@simulator_bp.route('/simulator', methods=['GET'])
@login_required
def simulator_dashboard():
    """Render the simulator dashboard."""
    return render_template('dashboard.html', title="Simulador de Cenários")

@simulator_bp.route('/simulator/new', methods=['GET', 'POST'])
@login_required
def new_scenario():
    """Create a new simulation scenario."""
    if request.method == 'POST':
        flash('Funcionalidade em desenvolvimento', 'info')
        return redirect(url_for('simulator.simulator_dashboard'))
    return render_template('dashboard.html', title="Novo Cenário de Simulação")
