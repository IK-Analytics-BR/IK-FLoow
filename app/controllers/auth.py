from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, ChangePasswordForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Nome de usuário ou senha inválidos', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = db.func.now()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Rota para logout de usuários."""
    logout_user()
    flash('Você foi desconectado com sucesso', 'success')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            name=form.name.data,
            role='user'
        )
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        
        flash('Parabéns, você está registrado! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Registro', form=form)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Rota para alteração de senha."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('Senha atual incorreta', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.password = form.new_password.data
        db.session.commit()
        flash('Sua senha foi atualizada com sucesso', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/change_password.html', title='Alterar Senha', form=form)
