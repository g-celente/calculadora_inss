from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import os
import pandas as pd
import base64

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Para desativar warnings de modificações no SQLAlchemy
app.config['SECRET_KEY'] = 'supersecretkey'  # Necessário para usar sessões e tokens JWT

# Instância do SQLAlchemy
db = SQLAlchemy(app)

# Modelo de usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Criar o banco de dados e as tabelas
with app.app_context():
    db.create_all()  # Isso cria as tabelas no banco de dados SQLite

# Rota para registrar novos usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, 'pbkdf2:sha256')

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registro realizado com sucesso!')
        return redirect(url_for('login'))

    return render_template('auth/registro.html')

# Rota para login de usuários e retornar token JWT
@app.route('/login', methods=['POST', 'GET'])
def login():
    # Redireciona para o dashboard se o usuário já estiver logado
    if 'auth-token' in request.cookies:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            # Define o cookie
            response = jsonify({'message': 'Login bem-sucedido!'})
            response.set_cookie('auth-token', token, httponly=True)  # Armazena o token no cookie

            return response

        return jsonify({'message': 'Email ou senha inválidos.'}), 401

    return render_template('auth/login.html')

pdf_path = r'F:\PYTHON T1\CNIS\RelatInss.pdf'
graph_pdf_path = r'F:\PYTHON T1\CNIS\RND.pdf'

# Rota para baixar o relatório PDF
@app.route('/calcular_beneficio', methods=['POST'])
def calcular_beneficio():
    sexo = request.form.get('sexo')
    salario_bruto = request.form.get('salario_bruto')

    if not sexo or not salario_bruto:
        flash('Preencha todos os campos corretamente!', 'error')
        return redirect(url_for('index'))

    try:
        salario_bruto = float(salario_bruto)
    except ValueError:
        flash('O salário bruto deve ser um número válido.', 'error')
        return redirect(url_for('index'))

    # Simular o cálculo do benefício INSS
    relatorio = criar_relat_pdf(sexo, salario_bruto)

    flash('Cálculo do benefício realizado com sucesso!', 'success')
    return render_template('calculadora.html', relatorio=relatorio)

# Rota para upload do arquivo CNIS
@app.route('/upload_cnis', methods=['POST'])
def upload_cnis():
    if 'cnis_pdf' not in request.files:
        flash('Nenhum arquivo selecionado!', 'error')
        return redirect(url_for('index'))

    file = request.files['cnis_pdf']
    if not file.filename.lower().endswith('.pdf'):
        flash('O arquivo deve ser um PDF!', 'error')
        return redirect(url_for('index'))

    file_path = os.path.join('assets', 'cnis.pdf')
    file.save(file_path)

    flash('Arquivo CNIS carregado com sucesso!', 'success')
    return redirect(url_for('index'))

# Rota para baixar o relatório PDF
@app.route('/download_pdf')
def download_pdf():
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=False)
    else:
        flash('Arquivo PDF não encontrado.', 'error')
        return redirect(url_for('index'))

# Rota para baixar o gráfico PDF
@app.route('/download_graph_pdf')
def download_graph_pdf():
    if os.path.exists(graph_pdf_path):
        return send_file(graph_pdf_path, as_attachment=False)
    else:
        flash('Arquivo gráfico PDF não encontrado.', 'error')
        return redirect(url_for('index'))

def criar_relat_pdf(sexo, salario_bruto):
    # Simular a criação de relatório em formato PDF ou tabela de resultado
    data = {
        'Alternativa': ['Aposentadoria 1', 'Aposentadoria 2'],
        'Valor Benefício': [2000, 2500]
    }
    return pd.DataFrame(data)

# Exemplo de rota de dashboard (que requer o token JWT)
@app.route('/')  # Protege a rota com o decorator
def dashboard():
    token = request.cookies.get('auth-token')
    if not token:
        return redirect(url_for('login'))
    
    if token:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
        return render_template('calculadora.html')
    return redirect(url_for('login'))  # Redireciona se não houver token

# Rota para o logout (opcional para remover sessão)
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
