from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import os
import pandas as pd
import matplotlib.pyplot as plt  # Para gráficos
import io  # Para manipulação de PDFs e imagens na memória
import base64
import pdfplumber  # Para manipulação de PDFs
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

# Instância do SQLAlchemy
db = SQLAlchemy(app)

# Modelo de usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Criar o banco de dados e as tabelas
with app.app_context():
    db.create_all()

# Função de autenticação (para proteger rotas)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth-token')
        if not token:
            return redirect(url_for('login'))
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['GET', 'POST'])
def register():

    token = request.cookies.get('auth-token')

    if token:
        return render_template('calculadora.html')
    
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

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    token = request.cookies.get('auth-token')

    if token:
        return render_template('calculadora.html')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            response = jsonify({'token': token, 'message': 'Login bem-sucedido!'})
            response.set_cookie('auth-token', token, httponly=True)
            return response, 200  # Retorna um JSON com status 200

        return jsonify({'message': 'Credenciais inválidas.'}), 401

    return render_template('auth/login.html')



# Função para criar relatórios PDF
def criar_relat_pdf(sx, slbr):
    data = {
        'Alternativa': ['Aposentadoria 1', 'Aposentadoria 2'],
        'Valor Benefício': [slbr * 0.7, slbr * 0.8]  # Exemplo fictício
    }
    df = pd.DataFrame(data)
    pdf_path = 'RelatInss.pdf'
    df.to_csv(pdf_path, index=False)  # Simulação de criação de PDF (use fpdf ou reportlab para PDF real)
    return df

# Função para verificar o arquivo CNIS (PDF)
def verifica_cnis():
    pdf_path = r'F:\PYTHON T1\CNIS\CNIS.pdf'
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        if "CNIS" in text:
            return True
        else:
            return False

# Função para gerar gráficos (renda desejada e possível)
def gerar_grafico(tipo, salario_bruto):
    fig, ax = plt.subplots()
    if tipo == 'desejada':
        categorias = ['Aposentadoria 1', 'Aposentadoria 2']
        valores = [salario_bruto * 0.7, salario_bruto * 0.8]
    else:  # Renda possível
        categorias = ['Renda Possível 1', 'Renda Possível 2']
        valores = [salario_bruto * 0.5, salario_bruto * 0.6]

    ax.bar(categorias, valores)
    ax.set_xlabel('Opções')
    ax.set_ylabel('Valor')
    ax.set_title('Comparação de Benefícios')

    # Salvar o gráfico como PDF
    graph_pdf_path = 'grafico.pdf'
    fig.savefig(graph_pdf_path)
    return graph_pdf_path

# Rota para upload do CNIS e verificação
@app.route('/upload_cnis', methods=['POST'])
def upload_cnis():
    if 'cnis_pdf' not in request.files:
        flash('Nenhum arquivo selecionado!', 'error')
        return redirect(url_for('dashboard'))

    file = request.files['cnis_pdf']
    if not file.filename.lower().endswith('.pdf'):
        flash('O arquivo deve ser um PDF!', 'error')
        return redirect(url_for('dashboard'))

    file_path = os.path.join('assets', 'cnis.pdf')
    file.save(file_path)

    # Verifica se o arquivo CNIS é válido
    if verifica_cnis():
        flash('Arquivo CNIS carregado com sucesso!', 'success')
    else:
        flash('Arquivo CNIS inválido!', 'error')

    return redirect(url_for('dashboard'))

# Rota para calcular benefício e gerar relatório
@app.route('/calcular_beneficio', methods=['POST'])
@token_required
def calcular_beneficio():
    sexo = request.form.get('sexo')
    salario_bruto = request.form.get('salario_bruto')

    if not sexo or not salario_bruto:
        flash('Preencha todos os campos corretamente!', 'error')
        return redirect(url_for('dashboard'))

    try:
        salario_bruto = float(salario_bruto)
    except ValueError:
        flash('O salário bruto deve ser um número válido.', 'error')
        return redirect(url_for('dashboard'))

    # Simular o cálculo do benefício
    relatorio = criar_relat_pdf(sexo, salario_bruto)
    
    # Gerar gráfico com base nos cálculos
    gerar_grafico('desejada', salario_bruto)

    flash('Cálculo do benefício realizado com sucesso!', 'success')
    return render_template('calculadora.html', relatorio=relatorio)

# Rota para download do relatório PDF
@app.route('/download_pdf')
@token_required
def download_pdf():
    pdf_path = 'RelatInss.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    flash('Arquivo PDF não encontrado.', 'error')
    return redirect(url_for('dashboard'))

# Rota para download do gráfico PDF
@app.route('/download_graph_pdf')
@token_required
def download_graph_pdf():
    graph_pdf_path = 'grafico.pdf'
    if os.path.exists(graph_pdf_path):
        return send_file(graph_pdf_path, as_attachment=True)
    flash('Arquivo gráfico PDF não encontrado.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/calculadora')
@token_required
def dashboard():
    return render_template('calculadora.html')

@app.route('/perfil')
@token_required
def perfil():
    return render_template('perfil.html')

@app.route('/')
@token_required
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
@token_required
def contato():
    return render_template('contato.html')

@app.route('/getUser', methods=['POST'])
@token_required
def getUser():
    getUser = request.cookies.get('auth-token')

    if not getUser:
        flash('token não encontrado')
        return render_template('perfil.html')
    
    return 

# Rota para logout
@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.set_cookie('auth-token', '', expires=0)
    flash('Logout realizado com sucesso.')
    return response


if __name__ == '__main__':
    app.run(debug=True)
