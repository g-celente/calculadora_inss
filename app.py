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
import pdfplumber 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas # Para manipulação de PDFs
import pandas as pd
from werkzeug.utils import secure_filename


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
    name = db.Column(db.String(200), nullable= False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Criar o banco de dados e as tabelas
with app.app_context():
    db.create_all()

# Função para verificar o arquivo CNIS (PDF)
def verifica_cnis(file_path):
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        if "CNIS" in text:
            return True
        else:
            return False

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


# Função de autenticação (para proteger rotas)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth-token')  # Por exemplo, obtendo o token do cabeçalho de autorização

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
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['password_confirmation']
        hashed_password = generate_password_hash(password, 'pbkdf2:sha256')

        if password != confirm_password:
            error_password = 'As senhas não conhecidem'
            return render_template('auth/registro.html', error_password=error_password)

        user = User.query.filter_by(email=email).first()

        if user:
            error = 'Usuário Já Registrado'
            return render_template('auth/registro.html', error=error)

        new_user = User(name=name, email=email, password=hashed_password)
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


@app.route('/gerar_relat_pdf', methods=['POST'])
def criar_relat_pdf():
    salario_bruto = request.form.get('salario_bruto')
    try:
        salario_bruto = float(salario_bruto)
    except ValueError:
        flash('O salário bruto deve ser um número válido.', 'error')
        return redirect(url_for('dashboard'))

    # Cálculos simplificados para as alternativas de aposentadoria
    beneficio1 = salario_bruto * 0.70
    beneficio2 = salario_bruto * 0.80

    # Criar o gráfico de barras
    fig, ax = plt.subplots()
    ax.bar(['Aposentadoria 1 (70%)', 'Aposentadoria 2 (80%)'], [beneficio1, beneficio2])
    ax.set_ylabel('Valor do Benefício (R$)')
    ax.set_title('Simulação de Benefícios de Aposentadoria')

    # Salvar o gráfico como uma imagem em memória
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)

    # Criar o arquivo PDF
    pdf_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'relatorio_inss.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Relatório de Benefício INSS")
    c.drawString(100, 730, f"Salário Bruto: R$ {salario_bruto:.2f}")
    c.drawString(100, 710, f"Alternativa 1 (70%): R$ {beneficio1:.2f}")
    c.drawString(100, 690, f"Alternativa 2 (80%): R$ {beneficio2:.2f}")

    c.showPage()
    c.save()

    return send_file(pdf_path, as_attachment=True)
# Função para criar relatórios PDF
# Função para gerar gráficos (renda desejada e possível)
@app.route('/gerar_grafico_pdf', methods=['POST'])
def gerar_grafico_pdf():
    salario_bruto = request.form.get('salario_bruto')
    try:
        salario_bruto = float(salario_bruto)
    except ValueError:
        flash('O salário bruto deve ser um número válido.', 'error')
        return redirect(url_for('dashboard'))

    # Simulação de cálculos de aposentadoria para gráfico
    beneficios = [salario_bruto * 0.70, salario_bruto * 0.80]
    alternativas = ['Aposentadoria 1', 'Aposentadoria 2']

    # Gera o gráfico usando matplotlib
    fig, ax = plt.subplots()
    ax.bar(alternativas, beneficios, color=['blue', 'green'])
    ax.set_ylabel('Valor do Benefício (R$)')
    ax.set_title('Comparação das Opções de Aposentadoria')

    # Salva o gráfico como um arquivo PDF
    graph_pdf_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'grafico_beneficio.pdf')
    fig.savefig(graph_pdf_path)

    # Enviar o PDF do gráfico para download
    return send_file(graph_pdf_path, as_attachment=True)


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
        flash('Nenhum arquivo foi enviado.', 'error')
        return redirect(url_for('dashboard'))

    file = request.files['cnis_pdf']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('dashboard'))

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        if verifica_cnis(file_path):
            flash('CNIS verificado com sucesso!', 'success')
        else:
            flash('O arquivo não contém um CNIS válido.', 'error')

        return redirect(url_for('dashboard'))
    else:
        flash('Por favor, faça o upload de um arquivo PDF válido.', 'error')
        return redirect(url_for('dashboard'))

# Rota para calcular benefício e gerar relatório
@app.route('/calcular_beneficio', methods=['POST'])
def calcular_beneficio():
    sexo = request.form.get('sexo')
    salario_bruto = request.form.get('salario_bruto')

    # Validação dos dados
    if not sexo or not salario_bruto:
        flash('Preencha todos os campos corretamente!', 'error')
        return redirect(url_for('dashboard'))

    try:
        salario_bruto = float(salario_bruto)
    except ValueError:
        flash('O salário bruto deve ser um número válido.', 'error')
        return redirect(url_for('dashboard'))

    # Simulação de cálculo de benefício com regras simplificadas
    if salario_bruto <= 1212.00:
        beneficio = salario_bruto * 0.75  # Exemplo de faixa mais baixa
    elif salario_bruto <= 2427.35:
        beneficio = salario_bruto * 0.80  # Faixa intermediária
    else:
        beneficio = salario_bruto * 0.85  # Faixa mais alta

    # Passa para o template o valor do benefício
    return render_template('resultado.html', beneficio=beneficio)

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

@app.route('/getUser', methods=['GET'])
@token_required
def getUser():
    token = request.cookies.get('auth-token')

    if not token:
        flash('Token não encontrado.')
        return render_template('perfil.html')

    try:
        # Decodificando o token para obter o user_id
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']

        # Buscando o usuário no banco de dados
        user = User.query.get(user_id)
        if user is None:
            flash('Usuário não encontrado.')
            return render_template('perfil.html')

        # Retornando os dados do usuário para o template
        return render_template('perfil.html', user=user)

    except jwt.ExpiredSignatureError:
        flash('Token expirado.')
        return render_template('perfil.html')
    except jwt.InvalidTokenError:
        flash('Token inválido.')
        return render_template('perfil.html')

@app.route('/alterarSenha', methods=['POST'])
@token_required
def alterarSenha():
    token = request.cookies.get('auth-token')
    new_password = request.form.get('new_password')

    if not token or not new_password:
        flash('Token ou nova senha não encontrados.')
        return redirect(url_for('perfil'))

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        user = User.query.get(user_id)

        if user is None:
            flash('Usuário não encontrado.')
            return redirect(url_for('perfil'))

        # Atualizar a senha
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        flash('Senha alterada com sucesso!')
        return redirect(url_for('perfil'))

    except jwt.ExpiredSignatureError:
        flash('Token expirado.')
        return redirect(url_for('perfil'))
    except jwt.InvalidTokenError:
        flash('Token inválido.')
        return redirect(url_for('perfil'))

@app.route('/forgotPassword', methods=['POST', 'GET'])
def forgotPassword():

    if request.method == 'POST':
        email = request.form['email']

        user = User.query.filter_by(email=email).first()

        if not user:
            error_email = 'Email não cadastrado no sistema'
            return render_template('auth/resetPassword.html', error_email=error_email)
        
        newPassword = request.form['password']
        confirm_password = request.form['password_confirmation']

        if newPassword != confirm_password:
            error_password = 'As senhas não coincidem'
            return render_template('auth/resetPassword.html', error_password=error_password)

        user.password = generate_password_hash(newPassword)
        db.session.commit()
        print('senha alterada com sucesso')
        return render_template('auth/login.html')
        
    return render_template('auth/resetPassword.html')

@token_required
@app.route('/remakePassword', methods=['POST'])
def mudarSenha():
    token = request.form.get('token')  # Obtenha o token do formulário
    nova_senha = request.form.get('new_password')
    confirmar_senha = request.form.get('confirm_password')

    if nova_senha != confirmar_senha:
        senha_error = 'As senhas não coincidem.'
        return render_template('perfil.html', senha_error=senha_error)

    try:
        # Decodificando o token JWT
        decoded_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_data.get('user_id')

        # Obtendo o usuário pelo ID
        user = User.query.get(user_id)  # Usando SQLAlchemy para obter o usuário

        if user is None:
            flash('Usuário não encontrado.', 'error')
            return redirect('/getUser')

        # Atualizando a senha do usuário
        user.password = generate_password_hash(nova_senha)
        db.session.commit() 
        
        senha_mensagem = 'Senha Alterada com Sucesso!' # Salva as alterações no banco de dados
        return render_template('perfil.html', senha_mensagem=senha_mensagem)

    except jwt.ExpiredSignatureError:
        flash('O token de autenticação expirou.', 'error')
        return redirect('/getUser')

    except jwt.DecodeError:
        flash('Token inválido.', 'error')
        return redirect('/getUser')

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', 'error')
        return redirect('/getUser')      

# Rota para logout
@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.set_cookie('auth-token', '', expires=0)
    flash('Logout realizado com sucesso.')
    return response


if __name__ == '__main__':
    app.run(debug=True)
