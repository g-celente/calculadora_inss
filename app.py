from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import matplotlib.pyplot as plt  # Para gráficos
import io  # Para manipulação de PDFs e imagens na memória
import base64
import pdfplumber 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas # Para manipulação de PDF
from werkzeug.utils import secure_filename
import numpy as np
from scipy.optimize import fminbound
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import base64
import os
from io import BytesIO
import pandas as pd
import locale
from flask_mail import Mail, Message
import matplotlib.image as mpimg
from reportlab.platypus import Image
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

EMPREGADOS_FILE = "./static/assets/arquivos/empregados.xlsx"
EMPRESAS_FILE = "./static/assets/arquivos/empresas.xlsx"

# Modelo de usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable= False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=True)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True, nullable=False)
    qtd_func = db.Column(db.Integer, nullable=False)
    prazo = db.Column(db.Integer, nullable=False)
    dt_inicio = db.Column(db.String(200), nullable=False)
    nota = db.Column(db.String(200), nullable=False)
    qtd_func_rest = db.Column(db.Integer, nullable=False)

class UserAdm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

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

def panel_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth-token')

        if not token:
            return redirect(url_for('panelLogin'))
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return redirect(url_for('panelLogin'))
        return f(*args, **kwargs)
    return decorated

def criar_relat_pdf(SX,SLBRT, cnis_path):

    try:
        SX = int(SX)

        import os
        # Caminho para o arquivo Excel
        path = os.path.join(app.root_path, 'static', 'assets', 'arquivos', 'series.xlsx')

        # Nome da aba que contém as colunas
        sheet_name = 'myseries'

        # Ler as primeiras quatro colunas da aba especificada
        series = pd.read_excel(path, sheet_name=sheet_name, usecols="A:D")

        # Remover linhas com dados faltantes
        series.dropna(inplace=True)

        # Renomear as colunas
        series.columns = ['Mes', 'Correcao', 'Minimo', 'Teto']    

        #Definicao do Salario Bruto para calculo
        if SLBRT > series['Teto'].max():
            SLBRT = series['Teto'].max()
        else:
            if SLBRT < series['Minimo'].max():
                SLBRT = series['Minimo'].max()

        #ENCONTRA CPF,NOME... e outros dados na pagina 1 

        import pdfplumber
        import re

        pdf_path = cnis_path

        # Use pdfplumber para extrair texto e informações de layout
        with pdfplumber.open(pdf_path) as pdf:
            D_V = []#recebe pares datas&valores filtrados
            for i in range(1):  # ajusta numero de paginas extraidas
                page = pdf.pages[i]
                text = page.extract_text()
                lines = text.split('\n')#transforma cada linha em uma string
                #print(elements)
                #print(page)
                pare = 0
                datext = 0
                for line in lines:
                    if "Civil" in line or "Benefício" in line:#para a busca/for ao encontrar a palavra Civil em alguma linha 
                        break
                    if pare == 1:
                        break
                    elements = re.findall(r'\S+', line)#transforma linha/string em uma lista com os elementos da string
                    #print(elements)

                    for i in range(len(elements)):
                        # Verifica se o elemento atual é 'Previdenciário::'
                        if datext == 1:
                            DTEXT = elements[i]
                            datext = 0
                        if elements[i] == 'Previdenciário':
                            datext = 1

                        # Verifica se o elemento atual é 'NIT:'
                        if elements[i] == 'NIT:':
                            NIT = elements[i + 1]
                        # Verifica se o elemento atual é 'CPF:'    
                        if elements[i] == 'CPF:':
                            CPF = elements[i + 1]

                        if elements[i] == 'Nome:':
                            NOME = " ".join(elements[i + 1:])

                        if elements[i] == 'nascimento:':
                            NASCI = elements[i + 1]

                        if elements[i] == 'mãe:':
                            MAE = " ".join(elements[i + 1:])
                            pare = 1

        #CALCULA IDADE ATUAL

        from datetime import datetime

        # Converter a string em um objeto datetime
        data_nascimento = datetime.strptime(NASCI, '%d/%m/%Y')

        # Data atual
        data_atual = datetime.now()

        # Calcular a diferença entre as datas
        idade_anos = data_atual.year - data_nascimento.year
        idade_meses = data_atual.month - data_nascimento.month

        # Ajustar meses se a data de nascimento for posterior à data atual neste ano
        if data_atual.month < data_nascimento.month:
            idade_anos -= 1
            idade_meses = 12 - abs(idade_meses)

        # Criar a string de idade formatada
        IDATUAL = f'{idade_anos} anos e {idade_meses} mês(es)'

        #ENCONTRA PARES DATAS&REMUNERACÃO no cnis e cria lista D_V

        import pdfplumber
        import re

        # Use pdfplumber para extrair texto e informações de layout
        with pdfplumber.open(pdf_path) as pdf:
            D_V = []#recebe pares datas&valores filtrados
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')#transforma cada linha em uma string
                #print(lines)
                #print(page)
                for line in lines:
                    if "Civil" in line or "Benefício" in line:#para a busca/for ao encontrar a palavra Civil em alguma linha 
                        break
                    #print(line)
                    elements = re.findall(r'\S+', line)#transforma linha/string em uma lista com os elementos da string
                    #print(elements)

                    corresponde = [] # recebe os pares data&valor de cada linha filtrados
                    padraoD= r'(?<![\w/])(\d{2}/\d{4})(?![\w/])'
                    padraoN= r'(\d{1,3}(?:\.\d{3})*(?:,\d{2}))'
                    for elemento in elements:
                        if re.search(padraoD, elemento):#filtra data com padraoD
                            #print(elemento)
                            corresponde.append(elemento)
                            #print(corresponde)
                        if re.search(padraoN, elemento):#filtra valor com padraoN 
                            #print(elemento)
                            corresponde.append(elemento)
                            #print(corresponde)
                            #filtra um valor numerico em alguma linha qdo 2 valores sao consecutivos
                            if re.search(padraoN,corresponde[-1]) is not None and re.search(padraoN, elemento) is not None and len(corresponde) % 2 != 0 :
                                corresponde.pop(-2)
                                #print(corresponde)

                    if len(corresponde)> 1:#filtra data com padrao isolada em alguma linha
                        D_V.extend(corresponde)#receve os pares D&V de cada linha apos filtros


        # Divida os elementos de D_V em datas (comp) e valores (remu)
        comp = D_V[::2]
        remu = D_V[1::2]

        # Crie um DataFrame a partir das duas listas
        extpr = pd.DataFrame({'comp': comp, 'remu': remu})

        # Converta a coluna 'comp' em formato de data
        extpr['comp'] = pd.to_datetime(extpr['comp'], format='%m/%Y', errors='coerce')

        # Trate os valores na coluna 'remu' para remover pontos, substituir vírgulas e converter para float
        extpr['remu'] = extpr['remu'].str.replace(r'[^\d,]', '', regex=True).str.replace(',', '.', regex=True).astype(float)

        # Agrupe as linhas por 'comp' e some os valores em 'remu'
        extpr = extpr.groupby('comp', as_index=False)['remu'].sum()

        # Ordene o DataFrame pela coluna 'comp' em ordem crescente
        #extpr = extpr.sort_values(by='comp')
        extpr.sort_values(by='comp', inplace=True)
        extpr['AdicDt'] = 0

        # Contando o número de linhas
        CTB = len(extpr)

        # Dividindo o valor de CTB por 12 e obtendo o resto da divisão
        resultado_anos = CTB // 12
        resto_meses = CTB % 12

        # Construindo a frase com os resultados
        CTBf = f"{resultado_anos} ano(s) e {resto_meses} mês(es) ({CTB} contribuições)"

        #print(CTBf)

        # Defina a data de referência
        DatRef = pd.to_datetime('11/2019', format='%m/%Y')

        # Mesclar os DataFrames usando a coluna 'comp'
        extpr = pd.merge(extpr, series[['Mes', 'Correcao', 'Minimo', 'Teto']], left_on='comp', right_on='Mes', how='left')

        # Remover a coluna extra 'Mes' que foi adicionada durante a mesclagem
        extpr.drop(columns=['Mes'], inplace=True)

        #FILTRA E CONTA AS REMUNERACOES MENORES QUE SAL MINIMO ANTES E APOS PEC103

        nrosal_a = extpr.query('remu < Minimo & comp <= @DatRef').shape[0]
        nrosal_d = extpr.query('remu < Minimo & comp > @DatRef').shape[0]
        nrosal_t = nrosal_a + nrosal_d
        #print(nrosal_a,nrosal_d,nrosal_t)

        #Condicoes para nota em relatorio
        if nrosal_t == 0:
            Texsalmin=f"<b>NENHUMA</b> contribuição com valor do salário base abaixo do Salário Mínimo ! O que poderia não entrar na contagem do tempo de contribuição e carência !"
        else:
            Texsalmin=f"<b>{nrosal_t} contribuição(ões)</b> com valor do salário base abaixo do Salário Mínimo. Esta quantidade pode não entrar na contagem do tempo de contribuição e carência.  Atenção !"

        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        # Imprimir o DataFrame
        #print(extpr)
        pd.reset_option('display.max_rows')
        pd.reset_option('display.max_columns')

        # Inicialize a coluna 'SalCorr' com valores zero
        extpr['SalCorr'] = 0

        # Iterar sobre as linhas do DataFrame
        for index, row in extpr.iterrows():
            # Aplicar as condições para calcular 'SalCorr' para cada linha
            if row['Correcao'] > 0:
                if row['remu'] >= row['Minimo'] and row['remu'] <= row['Teto']:
                    extpr.at[index, 'SalCorr'] = round(row['remu'] * row['Correcao'], 2) 
                elif row['remu'] > row['Teto']:
                    extpr.at[index, 'SalCorr'] = round(row['Teto'] * row['Correcao'], 2)
                elif row['remu'] > 0 and row['remu'] < row['Minimo']:
                    extpr.at[index, 'SalCorr'] = round(row['Minimo'] * row['Correcao'], 2)# rever row[Minomo] para row['remu']

        # Filtrar as linhas onde 'SalCorr' é maior que zero
        salcorr = extpr[extpr['SalCorr'] > 0]

        # Ordenar o DataFrame 'salcorr' por 'SalCorr' do maior para o menor
        salcorr = salcorr.sort_values(by='SalCorr', ascending=True)
        salcorr = salcorr.reset_index(drop=True)
        SalMedio = round(salcorr['SalCorr'].mean(),2)

        # Criar uma nova coluna 'CorrAcum' em 'salcorr'
        salcorr['CorrAcum'] = 0  # Inicializar a nova coluna com valores zero

        # Definir o valor da primeira linha como o valor máximo de 'SalCorr'
        salcorr.at[salcorr.index[0], 'CorrAcum'] = salcorr['SalCorr'].min()

        # Calcular os valores acumulados para as linhas subsequentes
        for i in range(1, len(salcorr)):
            salcorr.at[salcorr.index[i], 'CorrAcum'] = salcorr.at[salcorr.index[i-1], 'CorrAcum'] + salcorr.at[salcorr.index[i], 'SalCorr']

        salcorr['Qtd'] = range(1, len(salcorr) + 1)

        #CALCULO BENEFICIO COM/SEM OTIMIZACAO REGRA IDADE C CONTRIBUIC0ES EFETUADAS
        # Inicialize a coluna 'Media' com valores zero
        salcorr['Media'] = 0
        salcorr['Adic'] = 0
        salcorr['BenOtim'] = 0

        # Iterar sobre as linhas do DataFrame
        #SX=1 # 1 masculino via formulario
        DatIng = extpr['comp'].min()
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        for index in salcorr.index:
            if (DatIng > DatRef) and SX == 1:
                carencia60 = 20
            else:
                carencia60 = 15
            #Controla quantidade maxima parcelas retirada para calculo media
            if (len(extpr) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):# and (salcorr.loc[index, 'Qtd'] < len(salcorr)):
            #if (salcorr.loc[index, 'Qtd'] < len(salcorr)) and (len(extpr) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
                if len(salcorr) - salcorr.loc[index, 'Qtd'] >= 108:
                    divisor = len(salcorr) - salcorr.loc[index, 'Qtd']
                else:
                    divisor = 108

                salcorr.loc[index, 'Media'] = round((salcorr['CorrAcum'].max() - salcorr.loc[index, 'CorrAcum']) / divisor,2)
            else:
                salcorr.loc[index, 'Media'] = 0

            #Calculo Adicional
            if SX == 1:
                carencia2 = 20
            else:
                carencia2 = 15
            if int((len(extpr) - salcorr.loc[index, 'Qtd']) / 12) - carencia2 > 0:
                adicional = (int((len(extpr) - salcorr.loc[index, 'Qtd']) / 12) - carencia2) * 0.02 * salcorr.loc[index, 'Media']
                salcorr.loc[index, 'Adic']=round(adicional,2)
            else:
                adicional = 0
            salcorr.loc[index, 'BenOtim'] = round(salcorr.loc[index, 'Media']*0.6 + adicional,2)

        #Benefici Com Otimizacao
        BenCOtim = round(salcorr['BenOtim'].max(),2)
        #print(BenCOtim)
        rmvd = (salcorr['BenOtim'] > 0).sum()
        #print("Número de elementos removidos", rmvd)

        #Beneficio Sem Otiminizacao
        if len(salcorr) >= 108:
            divsemotim = len(salcorr)
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(extpr)/12)-carencia2)*0.02),2)
        else:
            divsemotim = 108
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(extpr)/12)-carencia2)*0.02),2)
        #print(BenSOtim)

        #Definicao de BENEFICIO SEM projecao de idade: BNFCspi
        if max(BenCOtim, BenSOtim) > series['Teto'].max():
            BNFCspi = series['Teto'].max()
        else:
            if max(BenCOtim, BenSOtim) < series['Minimo'].max():
                BNFCspi = series['Minimo'].max()
            else:
                BNFCspi = max(BenCOtim, BenSOtim)
        #print(BNFCspi)

        #Condicoes para nota em relatorio
        if (DatIng > DatRef) and SX == 1:
            if len(salcorr)>=240:
                TexBnfIdd=f"{len(salcorr)} contribuições realizadas válidas para calculo cumprem a carência mínima de 240 contribuições para Aposentaria por Idade. Mesmo que não realize mais nenhuma contribuição <b>adquiriu o direito de receber</b> a partir de 65 anos o benefício de Aposentadoria por Idade com valor de no <b>mínimo R$ {BNFCspi}</b>"
            else:
                TexBnfIdd=f"{len(salcorr)} contribuições realizadas ainda NÃO cumprem a carência mínima de 240 contribuições para Aposentadoria por Idade aos 65 anos."
        if (DatIng < DatRef) and SX == 1:
            if len(salcorr)>=180:
                TexBnfIdd=f"{len(salcorr)} contribuições realizadas válidas para calculo cumprem a carência mínima de 180 contribuições para Aposentaria por Idade. Mesmo que não realize mais nenhuma contribuição <b>adquiriu o direito de receber</b> a partir de 65 anos o benefício de Aposentadoria por Idade com valor de no <b>mínimo R$ {BNFCspi}</b>"
            else:
                TexBnfIdd=f"{len(salcorr)} contribuições realizadas ainda NÃO cumprem a carência mínima de 180 contribuições para Aposentadoria por Idade aos 65 anos."
        if SX == 0:
            if len(salcorr)>=180:
                TexBnfIdd=f"{len(salcorr)} contribuições realizadas válidas para calculo cumprem a carência mínima de 180 contribuições para Aposentaria por Idade. Mesmo que não realize mais nenhuma contribuição <b>adquiriu o direito de receber</b> a partir de 62 anos o benefício de Aposentadoria por Idade com valor de no <b>mínimo R$ {BNFCspi}</b>"
            else:
                TexBnfIdd=f"{len(salcorr)} contribuições realizadas ainda NÃO cumprem a carência mínima de 180 contribuições para Aposentadoria por Idade aos 62 anos."

        #CALCULA IDADE PARA REGRA DE IDADE
        #REGRA IDADE: ADICIONA linhas em df=extpr para completar linhas para a idade e carencia min para H/M

        from datetime import datetime, timedelta

        #XXXXXXXXXXXXXXXXXXX

        IDADE = extpr.copy() #cria df p aposentadoria por idade (apargar linhas acima de xxxxxx)
        #print(extpr)

        #Ajusta carencia em funcao do sexo,idade e ingresso no inss  p aposent por idade
        #SX = 1  # Substitua pelo sexo real (1 para masculino, 0 para feminino)
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y')  # Data da reforma
        DatIng = IDADE['comp'].min()  # Data de ingresso provisória

        print(DatRef)
        print(DatIng)
        print(SX)

        if SX == 1 and DatIng < DatRef:
            print('CHEGUEI AQUI PRIMEIRO IF')
            CARid = 180
            idade_final = 65
        elif SX == 1 and DatIng >= DatRef: 
            print('CHEGUEI AQUI SEGUNDO IF') # Use >= para cobrir todos os casos
            CARid = 240
            idade_final = 65
        elif SX == 0:
            print('CHEGUEI AQUI TERCEIRO IF')
            CARid = 180
            idade_final = 62
        else:
            print('NADA AVE')
            CARid = 180
            idade_final = 65


        # Definir a data de nascimento
        nasc_str = NASCI
        nasc = pd.to_datetime(nasc_str, format='%d/%m/%Y')# usando ddta do cnis

        mes_idade_final = nasc + pd.DateOffset(years=idade_final)
        mes_idade_final = mes_idade_final.replace(day=1)
        #print('mes final:',mes_idade_final)

        # Adicionar linhas adicionais até que o número de linhas seja igual a CARid

        ctb_CaRid=0 # conta contrib por carencia obrigatoria
        if len(IDADE) < CARid:
            # Criar linha adicional com o próximo mês em relacao data atual
            if IDADE['comp'].max() < datetime.now():
                ctb_CaRid=1
                #next_month = pd.Timestamp.now() + pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                IDADE = pd.concat([IDADE, new_row], ignore_index=True)
                #print('linha adicional mes atual por carencia')

            while len(IDADE) < CARid:
                #next_month = extpr['comp'].max() + timedelta(days=30)
                next_month = IDADE['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                IDADE = pd.concat([IDADE, new_row], ignore_index=True)
                ctb_CaRid = ctb_CaRid+1

        # Adicionar linhas até que o número de linhas alcance a idade final
        ctb_id=0 # conta contrib por idade (facultativa)
        if IDADE['comp'].max() < mes_idade_final and mes_idade_final > datetime.now():
            # Criar linha adicional com o próximo mês em relacao data atual
            if IDADE['comp'].max() < datetime.now() and ctb_CaRid == 0: # ctb_CaRid == 0,data atual ja atualizada
                ctb_id=1
                #next_month = pd.Timestamp.now() + pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                IDADE = pd.concat([IDADE, new_row], ignore_index=True)
                #print('linha adicional mes atual por idade')

            # Verificar a condição para adicionar linhas adicionais até alcancar idade final
            while IDADE['comp'].max() <= mes_idade_final and mes_idade_final > datetime.now():
                next_month = IDADE['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                IDADE = pd.concat([IDADE, new_row], ignore_index=True)
                ctb_id=ctb_id+1

        #LOCALIZA A DATA DE APOSENTADORIA POR IDADE
        import locale
        from datetime import datetime
        soma_adicdt = IDADE['AdicDt'].sum()
        #print("A soma dos valores do campo 'AdicDt' é:", soma_adicdt)

        # Converter para objetos date
        mes_idade_final_data = mes_idade_final.date()
        IDADE_comp_data = IDADE['comp'].dt.date
        # Encontrar igualdade entre as datas
        igualdade_datas = mes_idade_final_data == IDADE_comp_data

        if IDADE['AdicDt'].sum() == 0:
            if IDADE.loc[CARid - 1, 'comp'] >= mes_idade_final:

                dt_ap_id = IDADE.loc[CARid - 1, 'comp'].strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("data por carencia:", dt_ap_id)
            else:

                dt_ap_id = mes_idade_final.strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("Data por idade:", dt_ap_id)
        else:
            dt_ap_id = IDADE['comp'].max().strftime('%b/%Y').capitalize()
            locale.setlocale(locale.LC_TIME, '')
            #print("data carencia e idade 'comp' é:", dt_ap_id)

        #CALCULO BENEFICIO IDADE PROJETANDO IDADE/SALARIO p REGRA IDADE C/S OTIMIZACAO

        #valor simulado de salario bruto futuro (neste caso salario bruto medio de salarios ate o momento)
        SalMedio= round(IDADE.loc[(IDADE['AdicDt'] == 0) & (IDADE['Correcao'] > 0), 'SalCorr'].sum()/ len(IDADE.loc[(IDADE['AdicDt'] == 0) & (IDADE['Correcao'] > 0)]),2)
        #print(SalMedio)
        # Substituir os valores zero na coluna 'remu' pelo valor simulado de 'SalMedio'
        IDADE.loc[IDADE['AdicDt'] == 1, 'remu'] = SLBRT

        IDADE.drop(columns=['Correcao'], inplace=True)
        IDADE.drop(columns=['Minimo'], inplace=True)
        IDADE.drop(columns=['Teto'], inplace=True)
        # Converter colunas 'comp' e 'Mes' para o tipo de dado datetime
        IDADE['comp'] = pd.to_datetime(IDADE['comp'])
        series['Mes'] = pd.to_datetime(series['Mes'])
        # Formatando para conter apenas a data, sem as informações de hora
        IDADE['comp'] = IDADE['comp'].dt.date
        series['Mes'] = series['Mes'].dt.date

        # Mesclar os DataFrames usando a coluna 'comp'
        IDADE = pd.merge(IDADE, series[['Mes', 'Correcao', 'Minimo', 'Teto']], left_on='comp', right_on='Mes', how='left')
        # Remover a coluna extra 'Mes' que foi adicionada durante a mesclagem
        IDADE.drop(columns=['Mes'], inplace=True)

        # Iterar sobre as linhas do DataFrame para corrigir remuneracao
        for index, row in IDADE.iterrows():
            # Aplicar as condições para calcular 'SalCorr' para cada linha
            if row['Correcao'] > 0:
                if row['remu'] >= row['Minimo'] and row['remu'] <= row['Teto']:
                    IDADE.at[index, 'SalCorr'] = round(row['remu'] * row['Correcao'], 2) 
                elif row['remu'] > row['Teto']:
                    IDADE.at[index, 'SalCorr'] = round(row['Teto'] * row['Correcao'], 2)
                elif row['remu'] > 0 and row['remu'] < row['Minimo']:
                    IDADE.at[index, 'SalCorr'] = round(row['Minimo'] * row['Correcao'], 2)#reverter para row['Minimo'] p 'remu'

        #salcorr=Filtr0 das linhas onde 'SalCorr' é maior que zero (todas contribuicoes apos jun94)
        salcorr = IDADE[IDADE['SalCorr'] > 0]

        # Ordenar o DataFrame 'salcorr' por 'SalCorr' do maior para o menor
        salcorr = salcorr.sort_values(by='SalCorr', ascending=True)
        salcorr = salcorr.reset_index(drop=True)

        # Criar uma nova coluna 'CorrAcum' em 'salcorr'
        salcorr['CorrAcum'] = 0  # Inicializar a nova coluna com valores zero

        # Definir o valor da primeira linha como o valor máximo de 'SalCorr'
        salcorr.at[salcorr.index[0], 'CorrAcum'] = salcorr['SalCorr'].min()

        # Calcular os valores acumulados para as linhas subsequentes
        for i in range(1, len(salcorr)):
            salcorr.at[salcorr.index[i], 'CorrAcum'] = salcorr.at[salcorr.index[i-1], 'CorrAcum'] + salcorr.at[salcorr.index[i], 'SalCorr']

        # Criar uma nova coluna 'Qtd' em 'salcorr'
        salcorr['Qtd'] = range(1, len(salcorr) + 1)

        #CALCULO BENEFICIO COM/SEM OTIMIZACAO REGRA IDADE C CONTRIBUIC0ES EFETUADAS
        # Inicialize a coluna 'Media' com valores zero
        salcorr['Media'] = 0
        salcorr['Adic'] = 0
        salcorr['BenOtim'] = 0

        # Iterar sobre as linhas do DataFrame
        #SX=1 # 1 masculino via formulario
        DatIng = extpr['comp'].min()
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        for index in salcorr.index:
            if (DatIng > DatRef) and SX == 1:
                carencia60 = 20
            else:
                carencia60 = 15
            #Controla quantidade maxima parcelas retirada para calculo media
            if (len(IDADE) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
            #if (salcorr.loc[index, 'Qtd'] < len(salcorr)) and (len(IDADE) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
                if len(salcorr) - salcorr.loc[index, 'Qtd'] >= 108:
                    divisor = len(salcorr) - salcorr.loc[index, 'Qtd']
                else:
                    divisor = 108

                salcorr.loc[index, 'Media'] = round((salcorr['CorrAcum'].max() - salcorr.loc[index, 'CorrAcum']) / divisor,2)
            else:
                salcorr.loc[index, 'Media'] = 0

            #Calculo Beneficio por ano Adicional
            if SX == 1:
                carencia2 = 20
            else:
                carencia2 = 15
            if int((len(IDADE) - salcorr.loc[index, 'Qtd']) / 12) - carencia2 > 0:
                adicional = (int((len(IDADE) - salcorr.loc[index, 'Qtd']) / 12) - carencia2) * 0.02 * salcorr.loc[index, 'Media']
                salcorr.loc[index, 'Adic']=round(adicional,2)
            else:
                adicional = 0
            salcorr.loc[index, 'BenOtim'] = round(salcorr.loc[index, 'Media']*0.6 + adicional,2)

        #Beneficio Com Otimizacao
        BenCOtim = round(salcorr['BenOtim'].max(),2)
        #print(BenCOtim)
        rmvd = (salcorr['BenOtim'] > 0).sum()
        #print("Número de elementos removidos", rmvd)

        #Beneficio Sem Otiminizacao
        if len(salcorr) >= 108:
            divsemotim = len(salcorr)
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(IDADE)/12)-carencia2)*0.02),2)
        else:
            divsemotim = 108
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(IDADE)/12)-carencia2)*0.02),2)
        #print(BenSOtim)
        #Definicao de BENEFICIO
        if max(BenCOtim, BenSOtim) > series['Teto'].max():
            BNFC = series['Teto'].max()
        else:
            if max(BenCOtim, BenSOtim) < series['Minimo'].max():
                BNFC = series['Minimo'].max()
            else:
                BNFC = max(BenCOtim, BenSOtim)

        #PARAMETROS DE APOSENTADORIA IDADE PARA TABELA PDF DE RELATORIO
        # INDICA Benefício Estimado DE APOSENTADORIA POR IDADE
        vlr_id = BNFC

        # Criar a variável string 'bnf_id' com formatação para exibir todas as casas decimais
        bnf_id = 'R$ {:.2f}'.format(vlr_id)

        # INDICA NRO ESTIMADO DE CONTRIBUICOES FUTURAS P APOSENTADORIA POR IDADE

        if IDADE['AdicDt'].sum() > 0:
            ctr_id = IDADE['AdicDt'].sum()
        else:
            ctr_id = 0
        #print("nro 'ctr_id':", ctr_id)

        # INDICA VALOR DA CONTRIBUICAO ATE APOSENTADORIA POR IDADE
        slr_ctr = SLBRT

        if IDADE['AdicDt'].sum() > 0:
            parcela = 'R$ {:.2f}'.format(slr_ctr)
        else:
            parcela = '0'
        #print("valor 'slr_ctr':", parcela)

        # Criando o DataFrame 'ATNTV' com rótulos dos campos organizados em uma palavra por linha
        ATNTV = pd.DataFrame({
            'Regra': ['Idade'],
            'Data Aposentadoria': [dt_ap_id],
            'Benefício Estimado': [bnf_id],
            'Número Futuro Contribuições': [ctr_id],
            'Salário Futuro Bruto': [parcela]})

        #CALCULA IDADE PARA REGRA DE PONTOS
        #REGRA PONTOS: ADICIONA linhas em df=extpr para completar linhas para a idade e carencia min para H/M
        from datetime import datetime, timedelta
        #XXXXXXXXXXXXXXXXXXX
        pts = extpr.copy() #cria df p aposentadoria por pontos (apargar linhas acima de xxxxxx)
        #print(extpr)
        #nasc = pd.to_datetime('01/06/2020', format='%d/%m/%Y')

        #Ajusta carencia e tabela pts em funcao do sexo, tbm verifica regra de ptos qto data de ingresso
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        DatIng = pts['comp'].min() #data de ingresso provisoria (ajustar por data na linha Seq1 do cnis...)
        #print(DatIng)

        #Verifica regra de ptos qto data de ingresso do contribuine
        if DatIng <= DatRef:  # Verificando se a condição é verdadeira
            Regptos=1 #indicando COM DIREITO PONTOS
        else:
            Regptos=0 #indicando SEM DIREITO PONTOS

        #Ajusta carencia e tabela pts em funcao do sexo
        #SX = 1  # Substitua pelo sexo real (1 para masculino, 0 para feminino)
        if SX == 1:# and DatIng < DatRef:
            CARpts = 420
            #TabPts = [(2022, 1), (2023, 3), (2025, 7)]
            TabPts= [(2019, 96), (2020, 97), (2021, 98),(2022, 99), (2023, 100), (2024, 101),\
                    (2025, 102), (2026, 103), (2027, 104),(2028, 105), (2029, 105), (2030, 105),\
                    (2031, 105), (2032, 105), (2033, 105)]
            SupPts = (2034, 105)
        if SX == 0:# and DatIng < DatRef:
            CARpts = 360
            TabPts = [(2019, 86), (2020, 87), (2021, 88),(2022, 89), (2023, 90), (2024, 91),\
                    (2025, 92), (2026, 93), (2027, 94),(2028, 95), (2029, 96), (2030, 97),\
                    (2031, 98), (2032, 99), (2033, 100)]
            SupPts = (2034, 100)

        # Definir a data de nascimento
        nasc_str = NASCI
        nasc = pd.to_datetime(nasc_str, format='%d/%m/%Y')# usando ddta do cnis

        # Calcular o mês correspondente à idade final de sseurança para pontos
        idade_final = 80 # idade final em anos, usar idade igual a 70 p  dar boa margem
        #print(idade_final)
        mes_idade_final = nasc + pd.DateOffset(years=idade_final)
        mes_idade_final = mes_idade_final.replace(day=1)        

        #CARpts = 39 #eliminar esta linha qdo possivel
        if len(pts) < CARpts or pts['comp'].max() < mes_idade_final:
            if pts['comp'].max() < datetime.now():
                #next_month = pd.Timestamp.now()#+ pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1) 
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                pts = pd.concat([pts, new_row], ignore_index=True)

            while len(pts) < CARpts or pts['comp'].max() < mes_idade_final: 
                next_month = pts['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                pts = pd.concat([pts, new_row], ignore_index=True)

        # Preencher os campos 'Ano', 'nroctrb', 'num_meses' e 'pontos' com as regras fornecidas
        pts['Ano'] = pts['comp'].dt.year
        pts.reset_index(drop=True, inplace=True)
        pts['nroctrb'] = pts.index + 1
        pts['num_meses'] = ((pts['comp'].dt.year - nasc.year) * 12 + pts['comp'].dt.month - nasc.month)+1
        pts['pontos'] = ((pts['nroctrb'] + pts['num_meses']) // 12).astype(int) 

        # Criar DataFrame vazio
        LPS = pd.DataFrame(columns=pts.columns)

        # Para cada tupla na lista
        for tupla in TabPts:
            ano, pontos = tupla

            # Filtrar o DataFrame 'extpr' para incluir apenas as linhas onde o campo 'comp' é maior ou igual a '11/2019' e 'nroctrb' é maior ou igual a CARpts 
            resultado = pts[(pts['comp'] >= pd.to_datetime('11/2019', format='%m/%Y')) & (pts['nroctrb'] >= CARpts)]
            # Filtrar o resultado para encontrar as linhas com os valores da tupla nos campos 'Ano' e 'pontos'
            resultado = resultado.query('Ano == @ano and pontos == @pontos')

            # Anexar as linhas encontradas ao DataFrame 'LPS'
            LPS = pd.concat([LPS, resultado])

        # Resetar o índice do DataFrame 'LPS'
        LPS.reset_index(drop=True, inplace=True)

        # Filtrar o DataFrame 'extpr' para encontrar as linhas com os valores da tupla 'SupPts'
        #resultado_sup = extpr[(extpr['Ano'] >= SupPts[0]) & (extpr['pontos'] >= SupPts[1])]
        resultado_sup = pts[(pts['Ano'] >= SupPts[0]) & (pts['pontos'] >= SupPts[1]) & (pts['comp'] >= pd.to_datetime('11/2019', format='%m/%Y')) & (pts['nroctrb'] >= CARpts)]
        # Concatenar as linhas encontradas no DataFrame 'LPS'
        LPS = pd.concat([LPS, resultado_sup])

        # Resetar o índice do DataFrame 'LPS'
        LPS.reset_index(drop=True, inplace=True)

        LPS = LPS.iloc[[0]]

        # Extrair a data do campo 'comp' no formato 'mm/aaaa' para a variável Datpts
        Datpts = LPS['comp'].dt.strftime('%m/%Y').iloc[0] #ELIMINAR QDO POSSIVELM REDUNDANTE...

        # Extrair o valor do campo 'nroctrb' para a variável Ctrpts
        Ctrpts = LPS['nroctrb'].iloc[0]

        # Filtrar o DataFrame 'extpr' pelo campo 'nroctrb' e 'AdicDt'
        #Ctrpts=5
        condicao_copia = (pts['AdicDt'] == 0) | (pts['nroctrb'] <= Ctrpts)

        # Criar DataFrame 'Pontos' vazio
        Pontos = pd.DataFrame(columns=pts.columns)

        # Usar pd.concat para concatenar os DataFrames
        Pontos = pd.concat([Pontos, pts[condicao_copia]], ignore_index=True)

        #CALCULO BENEFICIO PONTOS PROJETANDO IDADE/SALARIO p REGRA PONTOS C/S OTIMIZACAO

        #valor simulado de salario bruto futuro (neste caso salario bruto medio de salarios ate o momento)
        SalMedio= round(Pontos.loc[(Pontos['AdicDt'] == 0) & (Pontos['Correcao'] > 0), 'SalCorr'].sum()/ len(Pontos.loc[(Pontos['AdicDt'] == 0) & (Pontos['Correcao'] > 0)]),2)
        #print(SalMedio)
        # Substituir os valores zero na coluna 'remu' pelo valor simulado de 'SalMedio'
        Pontos.loc[Pontos['AdicDt'] == 1, 'remu'] = SLBRT

        Pontos.drop(columns=['Correcao'], inplace=True)
        Pontos.drop(columns=['Minimo'], inplace=True)
        Pontos.drop(columns=['Teto'], inplace=True)
        # Converter colunas 'comp' e 'Mes' para o tipo de dado datetime
        Pontos['comp'] = pd.to_datetime(Pontos['comp'])
        series['Mes'] = pd.to_datetime(series['Mes'])
        # Formatando para conter apenas a data, sem as informações de hora
        Pontos['comp'] = Pontos['comp'].dt.date
        series['Mes'] = series['Mes'].dt.date

        # Mesclar os DataFrames usando a coluna 'comp'
        Pontos = pd.merge(Pontos, series[['Mes', 'Correcao', 'Minimo', 'Teto']], left_on='comp', right_on='Mes', how='left')
        # Remover a coluna extra 'Mes' que foi adicionada durante a mesclagem
        Pontos.drop(columns=['Mes'], inplace=True)

        # Iterar sobre as linhas do DataFrame para corrigir remuneracao
        for index, row in Pontos.iterrows():
            # Aplicar as condições para calcular 'SalCorr' para cada linha
            if row['Correcao'] > 0:
                if row['remu'] >= row['Minimo'] and row['remu'] <= row['Teto']:
                    Pontos.at[index, 'SalCorr'] = round(row['remu'] * row['Correcao'], 2) 
                elif row['remu'] > row['Teto']:
                    Pontos.at[index, 'SalCorr'] = round(row['Teto'] * row['Correcao'], 2)
                elif row['remu'] > 0 and row['remu'] < row['Minimo']:
                    Pontos.at[index, 'SalCorr'] = round(row['Minimo'] * row['Correcao'], 2)#reverter para row['Minimo'] p 'remu'

        #salcorr=Filtr0 das linhas onde 'SalCorr' é maior que zero (todas contribuicoes apos jun94)
        salcorr = Pontos[Pontos['SalCorr'] > 0]

        # Ordenar o DataFrame 'salcorr' por 'SalCorr' do maior para o menor
        salcorr = salcorr.sort_values(by='SalCorr', ascending=True)
        salcorr = salcorr.reset_index(drop=True)

        # Criar uma nova coluna 'CorrAcum' em 'salcorr'
        salcorr['CorrAcum'] = 0  # Inicializar a nova coluna com valores zero

        # Definir o valor da primeira linha como o valor máximo de 'SalCorr'
        salcorr.at[salcorr.index[0], 'CorrAcum'] = salcorr['SalCorr'].min()

        # Calcular os valores acumulados para as linhas subsequentes
        for i in range(1, len(salcorr)):
            salcorr.at[salcorr.index[i], 'CorrAcum'] = salcorr.at[salcorr.index[i-1], 'CorrAcum'] + salcorr.at[salcorr.index[i], 'SalCorr']

        # Criar uma nova coluna 'Qtd' em 'salcorr'
        salcorr['Qtd'] = range(1, len(salcorr) + 1)

        #CALCULO BENEFICIO COM/SEM OTIMIZACAO REGRA IDADE C CONTRIBUIC0ES EFETUADAS
        # Inicialize a coluna 'Media' com valores zero
        salcorr['Media'] = 0
        salcorr['Adic'] = 0
        salcorr['BenOtim'] = 0

        # Iterar sobre as linhas do DataFrame
        #SX=1 # 1 masculino via formulario
        DatIng = extpr['comp'].min()
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        for index in salcorr.index:
            if SX == 1:
                carencia60 = 35
            else:
                carencia60 = 30
            #Controla quantidade maxima parcelas retirada para calculo media
            if (len(Pontos) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
            #if (salcorr.loc[index, 'Qtd'] < len(salcorr)) and (len(IDADE) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
                if len(salcorr) - salcorr.loc[index, 'Qtd'] >= 108:
                    divisor = len(salcorr) - salcorr.loc[index, 'Qtd']
                else:
                    divisor = 108

                salcorr.loc[index, 'Media'] = round((salcorr['CorrAcum'].max() - salcorr.loc[index, 'CorrAcum']) / divisor,2)
            else:
                salcorr.loc[index, 'Media'] = 0

            #Calculo Beneficio por ano Adicional
            if SX == 1:
                carencia2 = 20
            else:
                carencia2 = 15
            if int((len(Pontos) - salcorr.loc[index, 'Qtd']) / 12) - carencia2 > 0:
                adicional = (int((len(Pontos) - salcorr.loc[index, 'Qtd']) / 12) - carencia2) * 0.02 * salcorr.loc[index, 'Media']
                salcorr.loc[index, 'Adic']=round(adicional,2)
            else:
                adicional = 0
            salcorr.loc[index, 'BenOtim'] = round(salcorr.loc[index, 'Media']*0.6 + adicional,2)

        #Beneficio Com Otimizacao
        BenCOtim = round(salcorr['BenOtim'].max(),2)
        #print(BenCOtim)
        rmvd = (salcorr['BenOtim'] > 0).sum()
        #print("Número de elementos removidos", rmvd)

        #Beneficio Sem Otiminizacao
        if len(salcorr) >= 108:
            divsemotim = len(salcorr)
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(Pontos)/12)-carencia2)*0.02),2)
        else:
            divsemotim = 108
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(Pontos)/12)-carencia2)*0.02),2)
        BNFC = max(BenCOtim, BenSOtim)

        #Definicao de BENEFICIO
        if max(BenCOtim, BenSOtim) > series['Teto'].max():
            BNFC = series['Teto'].max()
        else:
            if max(BenCOtim, BenSOtim) < series['Minimo'].max():
                BNFC = series['Minimo'].max()
            else:
                BNFC = max(BenCOtim, BenSOtim)

        #LOCALIZA A DATA DE APOSENTADORIA POR PONTOS
        if Regptos==1:
            dt_ap_pt = LPS['comp'].dt.strftime('%b/%Y').iloc[0].capitalize()
            locale.setlocale(locale.LC_TIME, '')
            #print("Data por pontos:", dt_ap_pt)
        else:
            #nao faz sentido, so p dar vasao ao fluxo e a variavel recever ALGUM VALOR...
            dt_ap_pt = pts['comp'].max().strftime('%b/%Y').capitalize()
            locale.setlocale(locale.LC_TIME, '')
            #print("data carencia e idade 'comp' é:", dt_ap_pt)

        # INDICA Benefício Estimado DE APOSENTADORIA POR PONTOS
        if Regptos==1:
            vlr_pt = BNFC
            # Criar a variável string 'bnf_pt' com formatação para exibir todas as casas decimais
            bnf_pt= 'R$ {:.2f}'.format(vlr_pt)
        else:
            vlr_pt = 0
            bnf_pt= 'R$ {:.2f}'.format(vlr_pt)

        # INDICA NRO ESTIMADO DE CONTRIBUICOES FUTURAS P APOSENTADORIA POR PONTOS

        if Pontos['AdicDt'].sum() > 0:
            ctr_pt = Pontos['AdicDt'].sum()
        else:
            ctr_pt = 0

        # INDICA VALOR DA CONTRIBUICAO ATE APOSENTADORIA POR PONTOS
        slr_ctr = SLBRT

        if Pontos['AdicDt'].sum() > 0:
            parcela = 'R$ {:.2f}'.format(slr_ctr)
        else:
            parcela = '0'

        if Regptos==1:
            #new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
            new_row = pd.DataFrame({
            'Regra': ['Pontos'],
            'Data Aposentadoria': [dt_ap_pt],
            'Benefício Estimado': [bnf_pt],
            'Número Futuro Contribuições': [ctr_pt],
            'Salário Futuro Bruto': [parcela]})

            ATNTV = pd.concat([ATNTV, new_row], ignore_index=True)

        #REGRA IDADE PROGRESSIVA: ADICIONA linhas em df=extpr para completar linhas para a idade e carencia min para H/M
        from datetime import datetime, timedelta

        prgv = extpr.copy() #cria df p aposentadoria progressiva (apargar linhas acima de xxxxxx)

        #Ajusta carencia e tabela pts em funcao do sexo, tbm verifica regra de ptos qto data de ingresso
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        DatIng = prgv['comp'].min() #data de ingresso provisoria (ajustar por data na linha Seq1 do cnis...)

        #Verifica regra de idade progressiva qto data de ingresso do contribuinte
        if DatIng <= DatRef:  # Verificando se a condição é verdadeira
            Regprg=1 #indicando COM DIREITO Id Progressiva
        else:
            Regprg=0 #indicando SEM DIREITO d Progressiva

        #Ajusta carencia e tabela pts em funcao do sexo
        #SX = 1  # Substitua pelo sexo real (1 para masculino, 0 para feminino)
        if SX == 1:# and DatIng < DatRef:
            CARprg = 420
            #TabPrg = [(2024, 4), (2025, 4.5), (2026, 5)]
            TabPrg = [(2019, 61), (2020, 61.5), (2021, 62),(2022, 62.1), (2023, 63), (2024, 63.5),\
                    (2025, 64), (2026, 64.5), (2027, 65),(2028, 65), (2029, 65), (2030, 65),(2031, 65)]
            #SupPrg = (2028, 65)
            SupPrg = (2032, 65)
        if SX == 0:# and DatIng < DatRef:
            CARprg = 360
            #TabPrg = [(2024, 4), (2025, 4.5), (2026, 5)]
            TabPrg = [(2019, 56), (2020, 56.5), (2021, 57),(2022, 57.5), (2023, 58), (2024, 58.5),\
                    (2025, 59), (2026, 59.5), (2027, 60),(2028, 60.5), (2029, 61), (2030, 61.5),(2031, 62)]
            #SupPrg = (2027, 6)
            SupPrg = (2032, 62)


        # Definir a data de nascimento
        nasc_str = NASCI
        nasc = pd.to_datetime(nasc_str, format='%d/%m/%Y')# usando ddta do cnis

        #nasc = pd.to_datetime('01/12/2018', format='%d/%m/%Y')
        #print(nasc)
        # Calcular o mês correspondente à idade final de sseurança para pontos
        idade_final = 80 # idade final em anos, usar idade igual a 70 para dar margem
        #print(idade_final)
        mes_idade_final = nasc + pd.DateOffset(years=idade_final)
        mes_idade_final = mes_idade_final.replace(day=1)        

        #CARprg = 39 #eliminar esta linha qdo possivel
        if (len(prgv) < CARprg or prgv['comp'].max() < mes_idade_final):
            if prgv['comp'].max() < datetime.now():
                #next_month = pd.Timestamp.now()#+ pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1) 
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                prgv = pd.concat([prgv, new_row], ignore_index=True)

            while len(prgv) < CARprg or prgv['comp'].max() < mes_idade_final: 
                next_month = prgv['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                prgv = pd.concat([prgv, new_row], ignore_index=True)

        # CRIA E Preenchr os campos 'Ano', 'nroctrb', 'num_meses' com as regras
        prgv['Ano'] = prgv['comp'].dt.year
        prgv.reset_index(drop=True, inplace=True)
        prgv['nroctrb'] = prgv.index + 1
        prgv['idade'] = ((((prgv['comp'].dt.year - nasc.year) * 12 + prgv['comp'].dt.month - nasc.month) ) / 12).round(1)

        # Criar DataFrame vazio
        LPS = pd.DataFrame(columns=prgv.columns)

        # Para cada tupla na lista
        for tupla in TabPrg:
            ano, idade = tupla

            # Filtrar o DataFrame 'extpr' para incluir apenas as linhas onde o campo 'comp' é maior ou igual a '11/2019' e 'nroctrb' é maior ou igual a CARpts 
            resultado = prgv[(prgv['comp'] >= pd.to_datetime('11/2019', format='%m/%Y')) & (prgv['nroctrb'] >= CARprg)]
            # Filtrar o resultado para encontrar as linhas com os valores da tupla nos campos 'Ano' e 'idade'
            resultado = resultado.query('Ano == @ano and idade == @idade')

            # Anexar as linhas encontradas ao DataFrame 'LPS'
            LPS = pd.concat([LPS, resultado])

        # Resetar o índice do DataFrame 'LPS'
        LPS.reset_index(drop=True, inplace=True)

        # Filtrar o DataFrame 'extpr' para encontrar as linhas com os valores da tupla 'SupPts'
        #resultado_sup = extpr[(extpr['Ano'] >= SupPts[0]) & (extpr['pontos'] >= SupPts[1])]
        resultado_sup = prgv[(prgv['Ano'] >= SupPrg[0]) & (prgv['idade'] >= SupPrg[1]) & (prgv['comp'] >= pd.to_datetime('11/2019', format='%m/%Y')) & (prgv['nroctrb'] >= CARprg)]
        # Concatenar as linhas encontradas no DataFrame 'LPS'
        LPS = pd.concat([LPS, resultado_sup])

        # Resetar o índice do DataFrame 'LPS'
        LPS.reset_index(drop=True, inplace=True)

        LPS = LPS.iloc[[0]]

        # Extrair a data do campo 'comp' no formato 'mm/aaaa' para a variável Datpts
        Datprg = LPS['comp'].dt.strftime('%m/%Y').iloc[0]

        # Extrair o valor do campo 'nroctrb' para a variável Ctrpts
        Ctrprg = LPS['nroctrb'].iloc[0]

        # Filtrar o DataFrame 'extpr' pelo campo 'nroctrb' e 'AdicDt'
        #Ctrprg=5
        condicao_copia = (prgv['AdicDt'] == 0) | (prgv['nroctrb'] <= Ctrprg)

        # Criar DataFrame 'Pontos' vazio
        Progressiva = pd.DataFrame(columns=prgv.columns)

        # Usar pd.concat para concatenar os DataFrames
        Progressiva = pd.concat([Progressiva, prgv[condicao_copia]], ignore_index=True)

        #CALCULO BENEFICIO IDADE PROGRESSIVA PROJETANDO IDADE/SALARIO C/S OTIMIZACAO

        #valor simulado de salario bruto futuro (neste caso salario bruto medio de salarios ate o momento)
        SalMedio= round(Progressiva.loc[(Progressiva['AdicDt'] == 0) & (Progressiva['Correcao'] > 0), 'SalCorr'].sum()/ len(Progressiva.loc[(Progressiva['AdicDt'] == 0) & (Progressiva['Correcao'] > 0)]),2)
        #print(SalMedio)
        # Substituir os valores zero na coluna 'remu' pelo valor simulado de 'SalMedio'
        Progressiva.loc[Progressiva['AdicDt'] == 1, 'remu'] = SLBRT

        Progressiva.drop(columns=['Correcao'], inplace=True)
        Progressiva.drop(columns=['Minimo'], inplace=True)
        Progressiva.drop(columns=['Teto'], inplace=True)
        # Converter colunas 'comp' e 'Mes' para o tipo de dado datetime
        Progressiva['comp'] = pd.to_datetime(Progressiva['comp'])
        series['Mes'] = pd.to_datetime(series['Mes'])
        # Formatando para conter apenas a data, sem as informações de hora
        Progressiva['comp'] = Progressiva['comp'].dt.date
        series['Mes'] = series['Mes'].dt.date

        # Mesclar os DataFrames usando a coluna 'comp'
        Progressiva = pd.merge(Progressiva, series[['Mes', 'Correcao', 'Minimo', 'Teto']], left_on='comp', right_on='Mes', how='left')
        # Remover a coluna extra 'Mes' que foi adicionada durante a mesclagem
        Progressiva.drop(columns=['Mes'], inplace=True)

        # Iterar sobre as linhas do DataFrame para corrigir remuneracao
        for index, row in Progressiva.iterrows():
            # Aplicar as condições para calcular 'SalCorr' para cada linha
            if row['Correcao'] > 0:
                if row['remu'] >= row['Minimo'] and row['remu'] <= row['Teto']:
                    Progressiva.at[index, 'SalCorr'] = round(row['remu'] * row['Correcao'], 2) 
                elif row['remu'] > row['Teto']:
                    Progressiva.at[index, 'SalCorr'] = round(row['Teto'] * row['Correcao'], 2)
                elif row['remu'] > 0 and row['remu'] < row['Minimo']:
                    Progressiva.at[index, 'SalCorr'] = round(row['Minimo'] * row['Correcao'], 2)#reverter para row['Minimo'] p 'remu'

        #salcorr=Filtr0 das linhas onde 'SalCorr' é maior que zero (todas contribuicoes apos jun94)
        salcorr = Progressiva[Progressiva['SalCorr'] > 0]

        # Ordenar o DataFrame 'salcorr' por 'SalCorr' do maior para o menor
        salcorr = salcorr.sort_values(by='SalCorr', ascending=True)
        salcorr = salcorr.reset_index(drop=True)

        # Criar uma nova coluna 'CorrAcum' em 'salcorr'
        salcorr['CorrAcum'] = 0  # Inicializar a nova coluna com valores zero

        # Definir o valor da primeira linha como o valor máximo de 'SalCorr'
        salcorr.at[salcorr.index[0], 'CorrAcum'] = salcorr['SalCorr'].min()

        # Calcular os valores acumulados para as linhas subsequentes
        for i in range(1, len(salcorr)):
            salcorr.at[salcorr.index[i], 'CorrAcum'] = salcorr.at[salcorr.index[i-1], 'CorrAcum'] + salcorr.at[salcorr.index[i], 'SalCorr']

        # Criar uma nova coluna 'Qtd' em 'salcorr'
        salcorr['Qtd'] = range(1, len(salcorr) + 1)

        #CALCULO BENEFICIO COM/SEM OTIMIZACAO REGRA IDADE C CONTRIBUIC0ES EFETUADAS
        # Inicialize a coluna 'Media' com valores zero
        salcorr['Media'] = 0
        salcorr['Adic'] = 0
        salcorr['BenOtim'] = 0

        # Iterar sobre as linhas do DataFrame
        #SX=1 # 1 masculino via formulario
        DatIng = extpr['comp'].min()
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        for index in salcorr.index:
            if SX == 1:
                carencia60 = 35
            else:
                carencia60 = 30
            #Controla quantidade maxima parcelas retirada para calculo media
            if (len(Progressiva) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
            #if (salcorr.loc[index, 'Qtd'] < len(salcorr)) and (len(IDADE) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
                if len(salcorr) - salcorr.loc[index, 'Qtd'] >= 108:
                    divisor = len(salcorr) - salcorr.loc[index, 'Qtd']
                else:
                    divisor = 108

                salcorr.loc[index, 'Media'] = round((salcorr['CorrAcum'].max() - salcorr.loc[index, 'CorrAcum']) / divisor,2)
            else:
                salcorr.loc[index, 'Media'] = 0

            #Calculo Beneficio por ano Adicional
            if SX == 1:
                carencia2 = 20
            else:
                carencia2 = 15
            if int((len(Progressiva) - salcorr.loc[index, 'Qtd']) / 12) - carencia2 > 0:
                adicional = (int((len(Progressiva) - salcorr.loc[index, 'Qtd']) / 12) - carencia2) * 0.02 * salcorr.loc[index, 'Media']
                salcorr.loc[index, 'Adic']=round(adicional,2)
            else:
                adicional = 0
            salcorr.loc[index, 'BenOtim'] = round(salcorr.loc[index, 'Media']*0.6 + adicional,2)

        #Beneficio Com Otimizacao
        BenCOtim = round(salcorr['BenOtim'].max(),2)
        #print(BenCOtim)
        rmvd = (salcorr['BenOtim'] > 0).sum()
        #print("Número de elementos removidos", rmvd)

        #Beneficio Sem Otiminizacao
        if len(salcorr) >= 108:
            divsemotim = len(salcorr)
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(Progressiva)/12)-carencia2)*0.02),2)
        else:
            divsemotim = 108
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim)*(0.6+(int(len(Progressiva)/12)-carencia2)*0.02),2)

        BNFC = max(BenCOtim, BenSOtim)

        #Definicao de BENEFICIO
        if max(BenCOtim, BenSOtim) > series['Teto'].max():
            BNFC = series['Teto'].max()
        else:
            if max(BenCOtim, BenSOtim) < series['Minimo'].max():
                BNFC = series['Minimo'].max()
            else:
                BNFC = max(BenCOtim, BenSOtim)

        #LOCALIZA A DATA DE APOSENTADORIA PROGRESSIVA
        if Regprg==1:
            dt_ap_prg = LPS['comp'].dt.strftime('%b/%Y').iloc[0].capitalize()
            locale.setlocale(locale.LC_TIME, '')
            #print("Data por progressiva:", dt_ap_prg)
        else:
            #nao faz sentido, so p dar vazao ao fluxo
            dt_ap_prg = prgv['comp'].max().strftime('%b/%Y').capitalize()
            locale.setlocale(locale.LC_TIME, '')

        # INDICA Benefício Estimado DE APOSENTADORIA PROGRESSIVA
        if Regprg==1:
            vlr_prg = BNFC
            # Criar a variável string 'bnf_pt' com formatação para exibir todas as casas decimais
            bnf_prg= 'R$ {:.2f}'.format(vlr_prg)
        else:
            vlr_prg = 0
            bnf_prg= 'R$ {:.2f}'.format(vlr_prg)

        # INDICA NRO ESTIMADO DE CONTRIBUICOES FUTURAS P APOSENTADORIA PROGRESSIVA
        if Progressiva['AdicDt'].sum() > 0:
            ctr_prg = Progressiva['AdicDt'].sum()
        else:
            ctr_prg=0
        #print("nro 'ctr_prg':", ctr_prg)

        # INDICA VALOR DA CONTRIBUICAO ATE APOSENTADORIA POR PROGRESSIVA
        slr_ctr = SLBRT

        if Progressiva['AdicDt'].sum() > 0:
            parcela = 'R$ {:.2f}'.format(slr_ctr)
        else:
            parcela = '0'

        if Regprg==1:
            new_row = pd.DataFrame({
            'Regra': ['Progressiva'],
            'Data Aposentadoria': [dt_ap_prg],
            'Benefício Estimado': [bnf_prg],
            'Número Futuro Contribuições': [ctr_prg],
            'Salário Futuro Bruto': [parcela]})

            ATNTV = pd.concat([ATNTV, new_row], ignore_index=True)

        #REGRA PEDAGIO 100: ADICIONA linhas em df=extpr para completar linhas para a idade e carencia min para H/M
        from datetime import datetime, timedelta

        pdg100 = extpr.copy()

        #Ajusta carencia e tabela pts em funcao do sexo, tbm verifica regra de ptos qto data de ingresso
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        DatIng = pdg100['comp'].min() #data de ingresso provisoria (ajustar por data na linha Seq1 do cnis...)
        #print(DatIng)

        #Ajusta carencia e tabela pts em funcao do sexo
        #SX = 1  # Substitua pelo sexo real (1 para masculino, 0 para feminino)
        if SX == 1:# and DatIng < DatRef:
            CAR100 = 420
            idade_final = 60 # idade final em anos
        if SX == 0:# and DatIng < DatRef:
            CAR100 = 360
            idade_final = 57 # idade final em anos

        #Verifica nro de contribuicoes ate nov19
        ctb100pre = pdg100.loc[pdg100['comp'] <= pd.to_datetime('11/2019', format='%m/%Y')].shape[0]
        #print(ctb100pre)

        #CAR100 =6  #eliminar esta linha qdo possivel
        dif100 = CAR100 - ctb100pre
        #print(dif100)    

        #Verifica regra de ptos qto data de ingresso do contribuine
        if dif100 > 24 and ctb100pre > 0:  # Verificando se a condição é verdadeira
            Reg100=1 #indicando COM DIREITO PEDAGIO 100
        else:
            Reg100=0 #indicando SEM DIREITO PEDAGIO 100

        #Definir a data de nascimento
        nasc_str = NASCI
        nasc = pd.to_datetime(nasc_str, format='%d/%m/%Y')# usando ddta do cnis

        # Calcular o mês correspondente à idade final de sseurança para Pedagio100
        #print(idade_final)
        mes_idade_final = nasc + pd.DateOffset(years=idade_final)
        mes_idade_final = mes_idade_final.replace(day=1)        

        ctb_CaR100=0
        if dif100 > 24 and ctb100pre > 0 and (len(pdg100) < (CAR100+dif100)):
            #Criar linha adicional com o próximo mês em relacao data atual
            if pdg100['comp'].max() < datetime.now():
                ctb_CaR100=1
                #next_month = pd.Timestamp.now() + pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                pdg100 = pd.concat([pdg100, new_row], ignore_index=True)
                #print('linha adicional mes atual por carencia')

            while len(pdg100) < (CAR100+dif100):
                #next_month = extpr['comp'].max() + timedelta(days=30)
                next_month = pdg100['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                pdg100 = pd.concat([pdg100, new_row], ignore_index=True)
                ctb_CaR100 = ctb_CaR100+1

        # Adicionar linhas até que o número de linhas alcance a idade final
        ctb_id100=0 # conta contrib por idade (facultativa)
        if pdg100['comp'].max() < mes_idade_final and mes_idade_final > datetime.now() and (dif100 >24 and ctb100pre > 0 ):
            # Criar linha adicional com o próximo mês em relacao data atual
            if pdg100['comp'].max() < datetime.now() and ctb_CaRid == 0: # ctb_CaRid == 0,data atual ja atualizada
                ctb_id100=1
                #next_month = pd.Timestamp.now() + pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                pdg100 = pd.concat([pdg100, new_row], ignore_index=True)
                #print('linha adicional mes atual por idade')

            # Verificar a condição para adicionar linhas adicionais até alcancar idade final
            while pdg100['comp'].max() <= mes_idade_final and mes_idade_final > datetime.now():
                next_month = pdg100['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                pdg100 = pd.concat([pdg100, new_row], ignore_index=True)
                ctb_id100=ctb_id100+1

        #CALCULO BENEFICIO  PEDAGIO 100 PROJETANDO IDADE/SALARIO C/S OTIMIZACAO

        #valor simulado de salario bruto futuro (neste caso salario bruto medio de salarios ate o momento)
        SalMedio= round(pdg100.loc[(pdg100['AdicDt'] == 0) & (pdg100['Correcao'] > 0), 'SalCorr'].sum()/ len(pdg100.loc[(pdg100['AdicDt'] == 0) & (pdg100['Correcao'] > 0)]),2)
        #print(SalMedio)
        # Substituir os valores zero na coluna 'remu' pelo valor simulado de 'SalMedio'
        pdg100.loc[pdg100['AdicDt'] == 1, 'remu'] = SLBRT

        pdg100.drop(columns=['Correcao'], inplace=True)
        pdg100.drop(columns=['Minimo'], inplace=True)
        pdg100.drop(columns=['Teto'], inplace=True)
        # Converter colunas 'comp' e 'Mes' para o tipo de dado datetime
        pdg100['comp'] = pd.to_datetime(pdg100['comp'])
        series['Mes'] = pd.to_datetime(series['Mes'])
        # Formatando para conter apenas a data, sem as informações de hora
        pdg100['comp'] = pdg100['comp'].dt.date
        series['Mes'] = series['Mes'].dt.date

        # Mesclar os DataFrames usando a coluna 'comp'
        pdg100 = pd.merge(pdg100, series[['Mes', 'Correcao', 'Minimo', 'Teto']], left_on='comp', right_on='Mes', how='left')
        # Remover a coluna extra 'Mes' que foi adicionada durante a mesclagem
        pdg100.drop(columns=['Mes'], inplace=True)

        # Iterar sobre as linhas do DataFrame para corrigir remuneracao
        for index, row in pdg100.iterrows():
            # Aplicar as condições para calcular 'SalCorr' para cada linha
            if row['Correcao'] > 0:
                if row['remu'] >= row['Minimo'] and row['remu'] <= row['Teto']:
                    pdg100.at[index, 'SalCorr'] = round(row['remu'] * row['Correcao'], 2) 
                elif row['remu'] > row['Teto']:
                    pdg100.at[index, 'SalCorr'] = round(row['Teto'] * row['Correcao'], 2)
                elif row['remu'] > 0 and row['remu'] < row['Minimo']:
                    pdg100.at[index, 'SalCorr'] = round(row['Minimo'] * row['Correcao'], 2)#reverter para row['Minimo'] p 'remu'

        #salcorr=Filtr0 das linhas onde 'SalCorr' é maior que zero (todas contribuicoes apos jun94)
        salcorr = pdg100[pdg100['SalCorr'] > 0]

        # Ordenar o DataFrame 'salcorr' por 'SalCorr' do maior para o menor
        salcorr = salcorr.sort_values(by='SalCorr', ascending=True)
        salcorr = salcorr.reset_index(drop=True)

        # Criar uma nova coluna 'CorrAcum' em 'salcorr'
        salcorr['CorrAcum'] = 0  # Inicializar a nova coluna com valores zero

        # Definir o valor da primeira linha como o valor máximo de 'SalCorr'
        salcorr.at[salcorr.index[0], 'CorrAcum'] = salcorr['SalCorr'].min()

        # Calcular os valores acumulados para as linhas subsequentes
        for i in range(1, len(salcorr)):
            salcorr.at[salcorr.index[i], 'CorrAcum'] = salcorr.at[salcorr.index[i-1], 'CorrAcum'] + salcorr.at[salcorr.index[i], 'SalCorr']

        # Criar uma nova coluna 'Qtd' em 'salcorr'
        salcorr['Qtd'] = range(1, len(salcorr) + 1)

        #CALCULO BENEFICIO COM/SEM OTIMIZACAO REGRA IDADE C CONTRIBUIC0ES EFETUADAS
        # Inicialize a coluna 'Media' com valores zero
        salcorr['Media'] = 0
        salcorr['Adic'] = 0
        salcorr['BenOtim'] = 0

        # Iterar sobre as linhas do DataFrame
        #SX=1 # 1 masculino via formulario
        DatIng = extpr['comp'].min()
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        for index in salcorr.index:
            if SX == 1:
                carencia60 = 35
            else:
                carencia60 = 30
            #Controla quantidade maxima parcelas retirada para calculo media
            if (len(pdg100) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
            #if (salcorr.loc[index, 'Qtd'] < len(salcorr)) and (len(IDADE) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
                if len(salcorr) - salcorr.loc[index, 'Qtd'] >= 108:
                    divisor = len(salcorr) - salcorr.loc[index, 'Qtd']
                else:
                    divisor = 108

                salcorr.loc[index, 'Media'] = round((salcorr['CorrAcum'].max() - salcorr.loc[index, 'CorrAcum']) / divisor,2)
            else:
                salcorr.loc[index, 'Media'] = 0
            salcorr.loc[index, 'BenOtim'] = round(salcorr.loc[index, 'Media']*1,2)# + adicional,2)

        #Beneficio Com Otimizacao
        BenCOtim = round(salcorr['BenOtim'].max(),2)
        #print(BenCOtim)
        rmvd = (salcorr['BenOtim'] > 0).sum()
        #print("Número de elementos removidos", rmvd)

        #Beneficio Sem Otiminizacao
        if len(salcorr) >= 108:
            divsemotim = len(salcorr)
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim),2) #*(0.6+(int(len(pdg100)/12)-carencia2)*0.02),2)
        else:
            divsemotim = 108
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim),2) #*(0.6+(int(len(pdg100)/12)-carencia2)*0.02),2)
        #print(BenSOtim)

        #Definicao de BENEFICIO
        if max(BenCOtim, BenSOtim) > series['Teto'].max():
            BNFC = series['Teto'].max()
        else:
            if max(BenCOtim, BenSOtim) < series['Minimo'].max():
                BNFC = series['Minimo'].max()
            else:
                BNFC = max(BenCOtim, BenSOtim)

        #LOCALIZA A DATA DE APOSENTADORIA PEDAGIO_100

        if pdg100['AdicDt'].sum() == 0 and Reg100==1:
            if pdg100.loc[CARid - 1, 'comp'] >= mes_idade_final:

                dt_ap_100 = pdg100.loc[CARid - 1, 'comp'].strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("data por pedagio100:", dt_ap_100)
            else:

                dt_ap_100 = mes_idade_final.strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("Data por pedagio100:", dt_ap_100)
        else:
            dt_ap_100 = pdg100['comp'].max().strftime('%b/%Y').capitalize()
            locale.setlocale(locale.LC_TIME, '')
            #print("data carencia e idade 100 é:", dt_ap_100)

        # INDICA Benefício Estimado DE APOSENTADORIA PEDAGIO 100
        if Reg100==1:
            vlr_100 = BNFC
        else:
            vlr_100 = 0
        # Criar a variável string 'bnf_100' com formatação para exibir todas as casas decimais
        bnf_100= 'R$ {:.2f}'.format(vlr_100)

        # INDICA NRO ESTIMADO DE CONTRIBUICOES FUTURAS P APOSENTADORIA CARENCIA100

        if pdg100['AdicDt'].sum() > 0:
            ctr_100 = pdg100['AdicDt'].sum()
        else:
            ctr_100 = 0

        # INDICA VALOR DA CONTRIBUICAO ATE APOSENTADORIA POR CARENCIA100
        slr_ctr = SLBRT

        if pdg100['AdicDt'].sum() > 0:
            parcela = 'R$ {:.2f}'.format(slr_ctr)
        else:
            parcela = '0'

        # Criando o DataFrame 'ATNTV' com rótulos dos campos organizados em uma palavra por linha
        if Reg100==1:
            new_row = pd.DataFrame({
            'Regra': ['Pedagio100'],
            'Data Aposentadoria': [dt_ap_100],
            'Benefício Estimado': [bnf_100],
            'Número Futuro Contribuições': [ctr_100],
            'Salário Futuro Bruto': [parcela]})

            ATNTV = pd.concat([ATNTV, new_row], ignore_index=True)

        #REGRA PEDAGIO 50: ADICIONA linhas em df=extpr para completar linhas para a idade e carencia min para H/M
        from datetime import datetime, timedelta

        pdg50 = extpr.copy()

        #Ajusta carencia e tabela pts em funcao do sexo, tbm verifica regra de ptos qto data de ingresso
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        DatIng = pdg50['comp'].min() #data de ingresso provisoria (ajustar por data na linha Seq1 do cnis...)

        #Ajusta carencia e tabela pts em funcao do sexo
        #SX = 1  # Substitua pelo sexo real (1 para masculino, 0 para feminino)
        if SX == 1:# and DatIng < DatRef:
            CAR50 = 420
        if SX == 0:# and DatIng < DatRef:
            CAR50 = 360

        #Verifica nro de contribuicoes ate nov19
        ctb50pre = extpr.loc[pdg50['comp'] <= pd.to_datetime('11/2019', format='%m/%Y')].shape[0]
        #print('ctb50pre',ctb50pre)

        #CAR50 = 5 #eliminar esta linha qdo possivel
        dif50 = CAR50 - ctb50pre
        #print('dif50',dif50)    

        #Verifica regra de carencia qto as condicoes de contribuicao
        if dif50 >0 and dif50 <=24 and ctb50pre > 0:  # Verificando se a condição é verdadeira
            Reg50=1 #indicando COM DIREITO PEDAGIO 50
        else:
            Reg50=0 #indicando SEM DIREITO PEDAGIO 50

        if dif50 > 0 and dif50 <= 24 and ctb50pre > 0 and len(pdg50) < (CAR50 + dif50*0.5):
            if pdg50['comp'].max() < datetime.now():
                next_month = datetime.now().replace(day=1) 
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                pdg50 = pd.concat([pdg50, new_row], ignore_index=True)

            while len(pdg50) < (CAR50 + dif50*0.5): 
                next_month = pdg50['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                pdg50 = pd.concat([pdg50, new_row], ignore_index=True)

        #LOCALIZA A DATA DE APOSENTADORIA PEDAGIO_50

        if pdg50['AdicDt'].sum() == 0 and Reg50==1:
            if pdg50.loc[CARid - 1, 'comp'] >= mes_idade_final:

                dt_ap_50 = pdg50.loc[CARid - 1, 'comp'].strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("data por pedagio50:", dt_ap_50)
            else:

                dt_ap_50 = mes_idade_final.strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                print("Data por pedagio50:", dt_ap_50)
        else:
            dt_ap_50 = pdg50['comp'].max().strftime('%b/%Y').capitalize()
            locale.setlocale(locale.LC_TIME, '')

        # INDICA Benefício Estimado DE APOSENTADORIA CARENCIA100
        #vlr_50 = 4500.00

        # Criar a variável string 'bnf_100' com formatação para exibir todas as casas decimais
        if  Reg50==1:
            bnf_50 = 'Ver app Meu_INSS'
        else:
            bnf_50 = 'sem acesso'

        # INDICA NRO ESTIMADO DE CONTRIBUICOES FUTURAS P APOSENTADORIA CARENCIA100

        if pdg50['AdicDt'].sum() > 0:
            ctr_50 = pdg50['AdicDt'].sum()
        else:
            ctr_50 = 0
        #print("nro 'ctr_50':", ctr_50)

        # INDICA VALOR DA CONTRIBUICAO ATE APOSENTADORIA POR CARENCIA100
        slr_ctr = SLBRT

        if pdg50['AdicDt'].sum() > 0:
            parcela = 'R$ {:.2f}'.format(slr_ctr)
        else:
            parcela = '0'

        # Criando o DataFrame 'ATNTV' com rótulos dos campos organizados em uma palavra por linha
        if Reg50==1:
            new_row = pd.DataFrame({
            'Regra': ['Pedagio50'],
            'Data Aposentadoria': [dt_ap_50],
            'Benefício Estimado': [bnf_50],
            'Número Futuro Contribuições': [ctr_50],
            'Salário Futuro Bruto': [parcela]})

            ATNTV = pd.concat([ATNTV, new_row], ignore_index=True)

        #REGRA PEDAGIO 100p50: ADICIONA linhas em df=extpr para completar linhas para a idade e carencia min para H/M
        from datetime import datetime, timedelta

        pdg1p5 = extpr.copy()

        #Ajusta carencia e tabela pts em funcao do sexo, tbm verifica regra de ptos qto data de ingresso
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        DatIng = pdg1p5['comp'].min() #data de ingresso provisoria (ajustar por data na linha Seq1 do cnis...)

        #Ajusta carencia e tabela pts em funcao do sexo
        #SX = 1  # Substitua pelo sexo real (1 para masculino, 0 para feminino)
        if SX == 1:# and DatIng < DatRef:
            CAR100 = 420
            idade_final = 60 # idade final em anos
        if SX == 0:# and DatIng < DatRef:
            CAR100 = 360
            idade_final = 57 # idade final em anos

        #Verifica nro de contribuicoes ate nov19
        ctb100pre = pdg1p5.loc[pdg1p5['comp'] <= pd.to_datetime('11/2019', format='%m/%Y')].shape[0]

        #CAR100 =6  #eliminar esta linha qdo possivel
        dif100 = CAR100 - ctb100pre

        #Verifica regra de carencia qto as condicoes de contribuicao
        #if dif50 >0 and dif50 <= 3 and ctb50pre > 0
        if dif100 >0 and dif100<=24 and ctb100pre > 0:  # Verificando se a condição é verdadeira
            Reg100to50=1 #indicando COM DIREITO PEDAGIO 100
        else:
            Reg100to50=0 #indicando SEM DIREITO PEDAGIO 100

        #Definir a data de nascimento
        nasc_str = NASCI
        nasc = pd.to_datetime(nasc_str, format='%d/%m/%Y')# usando ddta do cnis


        # Calcular o mês correspondente à idade final de segurança para Pedagio100
        #print(idade_final)
        mes_idade_final = nasc + pd.DateOffset(years=idade_final)
        mes_idade_final = mes_idade_final.replace(day=1)        

        ctb_CaR100p50=0
        if dif100 >0 and dif100<=24 and ctb100pre > 0 and (len(pdg1p5) < (CAR100+dif100)):
        # Criar linha adicional com o próximo mês em relacao data atual
            if pdg1p5['comp'].max() < datetime.now():
                ctb_CaR100p50=1
                #next_month = pd.Timestamp.now() + pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                pdg1p5 = pd.concat([pdg1p5, new_row], ignore_index=True)
                print('linha adicional mes atual por carencia')

            while len(pdg1p5) < (CAR100+dif100):
                #next_month = extpr['comp'].max() + timedelta(days=30)
                next_month = pdg1p5['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                pdg1p5 = pd.concat([pdg1p5, new_row], ignore_index=True)
                ctb_CaR100p50 = ctb_CaR100p50+1

        # Adicionar linhas até que o número de linhas alcance a idade final
        ctb_id100p50=0 # conta contrib por idade (facultativa)
        if pdg1p5['comp'].max() < mes_idade_final and mes_idade_final > datetime.now() and (dif100 >0 and dif100<=24 and ctb100pre > 0):
            # Criar linha adicional com o próximo mês em relacao data atual
            if pdg1p5['comp'].max() < datetime.now() and ctb_CaRid == 0: # ctb_CaRid == 0,data atual ja atualizada
                ctb_id100p50=1
                #next_month = pd.Timestamp.now() + pd.offsets.MonthBegin(1)
                next_month = datetime.now().replace(day=1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                # Concatenar o DataFrame original com o novo DataFrame
                pdg1p5 = pd.concat([pdg1p5, new_row], ignore_index=True)
                #print('linha adicional mes atual por idade')

            # Verificar a condição para adicionar linhas adicionais até alcancar idade final
            while pdg1p5['comp'].max() <= mes_idade_final and mes_idade_final > datetime.now():
                next_month = pdg1p5['comp'].max() + pd.offsets.MonthBegin(1)
                new_row = pd.DataFrame({'comp': [next_month], 'remu': [0.0],'AdicDt': [1]})
                pdg1p5 = pd.concat([pdg1p5, new_row], ignore_index=True)
                ctb_id100p50=ctb_id100p50+1

        #CALCULO BENEFICIO  PEDAGIO 100p50 PROJETANDO IDADE/SALARIO C/S OTIMIZACAO

        #valor simulado de salario bruto futuro (neste caso salario bruto medio de salarios ate o momento)
        SalMedio= round(pdg1p5.loc[(pdg1p5['AdicDt'] == 0) & (pdg1p5['Correcao'] > 0), 'SalCorr'].sum()/ len(pdg1p5.loc[(pdg1p5['AdicDt'] == 0) & (pdg1p5['Correcao'] > 0)]),2)
        #print(SalMedio)
        # Substituir os valores zero na coluna 'remu' pelo valor simulado de 'SalMedio'
        pdg1p5.loc[pdg1p5['AdicDt'] == 1, 'remu'] = SLBRT

        pdg1p5.drop(columns=['Correcao'], inplace=True)
        pdg1p5.drop(columns=['Minimo'], inplace=True)
        pdg1p5.drop(columns=['Teto'], inplace=True)
        # Converter colunas 'comp' e 'Mes' para o tipo de dado datetime
        pdg1p5['comp'] = pd.to_datetime(pdg1p5['comp'])
        series['Mes'] = pd.to_datetime(series['Mes'])
        # Formatando para conter apenas a data, sem as informações de hora
        pdg1p5['comp'] = pdg1p5['comp'].dt.date
        series['Mes'] = series['Mes'].dt.date

        # Mesclar os DataFrames usando a coluna 'comp'
        pdg1p5 = pd.merge(pdg1p5, series[['Mes', 'Correcao', 'Minimo', 'Teto']], left_on='comp', right_on='Mes', how='left')
        # Remover a coluna extra 'Mes' que foi adicionada durante a mesclagem
        pdg1p5.drop(columns=['Mes'], inplace=True)

        # Iterar sobre as linhas do DataFrame para corrigir remuneracao
        for index, row in pdg1p5.iterrows():
            # Aplicar as condições para calcular 'SalCorr' para cada linha
            if row['Correcao'] > 0:
                if row['remu'] >= row['Minimo'] and row['remu'] <= row['Teto']:
                    pdg1p5.at[index, 'SalCorr'] = round(row['remu'] * row['Correcao'], 2) 
                elif row['remu'] > row['Teto']:
                    pdg1p5.at[index, 'SalCorr'] = round(row['Teto'] * row['Correcao'], 2)
                elif row['remu'] > 0 and row['remu'] < row['Minimo']:
                    pdg1p5.at[index, 'SalCorr'] = round(row['Minimo'] * row['Correcao'], 2)#reverter para row['Minimo'] p 'remu'

        #salcorr=Filtr0 das linhas onde 'SalCorr' é maior que zero (todas contribuicoes apos jun94)
        salcorr = pdg1p5[pdg1p5['SalCorr'] > 0]

        # Ordenar o DataFrame 'salcorr' por 'SalCorr' do maior para o menor
        salcorr = salcorr.sort_values(by='SalCorr', ascending=True)
        salcorr = salcorr.reset_index(drop=True)

        # Criar uma nova coluna 'CorrAcum' em 'salcorr'
        salcorr['CorrAcum'] = 0  # Inicializar a nova coluna com valores zero

        # Definir o valor da primeira linha como o valor máximo de 'SalCorr'
        salcorr.at[salcorr.index[0], 'CorrAcum'] = salcorr['SalCorr'].min()

        # Calcular os valores acumulados para as linhas subsequentes
        for i in range(1, len(salcorr)):
            salcorr.at[salcorr.index[i], 'CorrAcum'] = salcorr.at[salcorr.index[i-1], 'CorrAcum'] + salcorr.at[salcorr.index[i], 'SalCorr']

        # Criar uma nova coluna 'Qtd' em 'salcorr'
        salcorr['Qtd'] = range(1, len(salcorr) + 1)

        #CALCULO BENEFICIO COM/SEM OTIMIZACAO REGRA IDADE C CONTRIBUIC0ES EFETUADAS
        # Inicialize a coluna 'Media' com valores zero
        salcorr['Media'] = 0
        salcorr['Adic'] = 0
        salcorr['BenOtim'] = 0

        # Iterar sobre as linhas do DataFrame
        #SX=1 # 1 masculino via formulario
        DatIng = extpr['comp'].min()
        DatRef = pd.to_datetime('13/11/2019', format='%d/%m/%Y') #reforma
        for index in salcorr.index:
            if SX == 1:
                carencia60 = 35
            else:
                carencia60 = 30
            #Controla quantidade maxima parcelas retirada para calculo media
            if (len(pdg1p5) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
            #if (salcorr.loc[index, 'Qtd'] < len(salcorr)) and (len(IDADE) - salcorr.loc[index, 'Qtd'] >= carencia60 * 12):
                if len(salcorr) - salcorr.loc[index, 'Qtd'] >= 108:
                    divisor = len(salcorr) - salcorr.loc[index, 'Qtd']
                else:
                    divisor = 108

                salcorr.loc[index, 'Media'] = round((salcorr['CorrAcum'].max() - salcorr.loc[index, 'CorrAcum']) / divisor,2)
            else:
                salcorr.loc[index, 'Media'] = 0

            salcorr.loc[index, 'BenOtim'] = round(salcorr.loc[index, 'Media']*1,2)# + adicional,2)

        #Beneficio Com Otimizacao
        BenCOtim = round(salcorr['BenOtim'].max(),2)
        #print(BenCOtim)
        rmvd = (salcorr['BenOtim'] > 0).sum()
        #print("Número de elementos removidos", rmvd)

        #Beneficio Sem Otiminizacao
        if len(salcorr) >= 108:
            divsemotim = len(salcorr)
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim),2) #*(0.6+(int(len(pdg100)/12)-carencia2)*0.02),2)
        else:
            divsemotim = 108
            BenSOtim = round((salcorr['CorrAcum'].max()/divsemotim),2) #*(0.6+(int(len(pdg100)/12)-carencia2)*0.02),2)
        #print(BenSOtim)
        BNFC = max(BenCOtim, BenSOtim)

        #Definicao de BENEFICIO
        if max(BenCOtim, BenSOtim) > series['Teto'].max():
            BNFC = series['Teto'].max()
        else:
            if max(BenCOtim, BenSOtim) < series['Minimo'].max():
                BNFC = series['Minimo'].max()
            else:
                BNFC = max(BenCOtim, BenSOtim)

        #LOCALIZA A DATA DE APOSENTADORIA PEDAGIO_100p50

        if pdg1p5['AdicDt'].sum() == 0 and Reg100to50==1:
            if pdg1p5.loc[CARid - 1, 'comp'] >= mes_idade_final:

                dt_ap_1p5 = pdg1p5.loc[CARid - 1, 'comp'].strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("data por pedagio100p50:", dt_ap_1p5)
            else:

                dt_ap_1p5 = mes_idade_final.strftime('%b/%Y').capitalize()
                locale.setlocale(locale.LC_TIME, '')
                #print("Data por pedagio1p5:", dt_ap_1p5)
        else:
            dt_ap_1p5 = pdg1p5['comp'].max().strftime('%b/%Y').capitalize()
            locale.setlocale(locale.LC_TIME, '')
            #print("data carencia e idade 100p50 é:", dt_ap_1p5)

        # INDICA Benefício Estimado DE APOSENTADORIA CARENCIA100p50
        if Reg100to50==1:
            vlr_1p5 = BNFC
            # Criar a variável string 'bnf_100' com formatação para exibir todas as casas decimais
            bnf_1p5= 'R$ {:.2f}'.format(vlr_1p5)
        else:
            vlr_1p5 = 0

        # INDICA NRO ESTIMADO DE CONTRIBUICOES FUTURAS P APOSENTADORIA CARENCIA100p50

        if pdg1p5['AdicDt'].sum() > 0:
            ctr_1p5 = pdg1p5['AdicDt'].sum()
        else:
            ctr_1p5 = 0
        #print("nro 'ctr_1p5':", ctr_1p5)

        # INDICA VALOR DA CONTRIBUICAO ATE APOSENTADORIA POR CARENCIA100p50
        slr_ctr = SLBRT

        if pdg1p5['AdicDt'].sum() > 0:
            parcela = 'R$ {:.2f}'.format(slr_ctr)
        else:
            parcela = '0'

        # Criando o DataFrame 'ATNTV' com rótulos dos campos organizados em uma palavra por linha
        if Reg100to50==1:
            new_row = pd.DataFrame({
            'Regra': ['Pedagio100'],
            'Data Aposentadoria': [dt_ap_1p5],
            'Benefício Estimado': [bnf_1p5],
            'Número Futuro Contribuições': [ctr_1p5],
            'Salário Futuro Bruto': [parcela]})

            ATNTV = pd.concat([ATNTV, new_row], ignore_index=True)

        #CRIA dataframe que encontra vinculos empregaticios e data ingresso inss
        

        # Cria um DataFrame vazio para armazenar os dados
        VCLS = pd.DataFrame(columns=['VÍNCULO'])

        # Use pdfplumber para extrair texto e informações de layout
        with pdfplumber.open(pdf_path) as pdf:
            D_V = []  # recebe pares datas&valores filtrados
            DatInic= None
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')  # transforma cada linha em uma string
                # Itera sobre as linhas
                for i, line in enumerate(lines):
                    if "Civil" in line or "Benefício" in line:
                        break  # Interrompe o loop ao encontrar a palavra "Civil"

                    if "Seq." in line:
                        # Verifica se há uma próxima linha na lista
                        if i + 1 < len(lines) and "Benefício" not in lines[i + 1]:
                            # Aplica a substituição do padrão em line para eliminar MM/AAAA
                            cleaned_1 = re.sub(r'(?<![\w/])(\d{2}/\d{4})(?![\w/])', '', lines[i + 1])
                            # Aplica a substituição do padrão em line para eliminar NIT
                            cleaned_2 = re.sub(r'(?<=\s)([\d.]*-)(\d+)(?=\s)', '', cleaned_1)
                            # Aplica a substituição do padrão em line para eliminar CNPJs
                            cleaned_3 = re.sub(r'(\s[\d.]+/\d{4}-\d{2})', '', cleaned_2)
                            #print(cleaned_3[0])
                            #captura da inicio de entrada no inss
                            if cleaned_3[0] == '1'and len(cleaned_3[0])==1 and DatInic is None:
                                DatInic=re.search(r'\d{2}/\d{2}/\d{4}', cleaned_3).group()

                            # Adiciona a próxima linha ao DataFrame VCLS
                            new_row = pd.DataFrame({'VÍNCULO': [cleaned_3]})

                            VCLS = pd.concat([VCLS, new_row], ignore_index=True)

        VCLS_styled = VCLS.style.set_properties(**{'text-align': 'left'})
        # Exibir o DataFrame estilizado
        VCLS_styled

        #CRIACAO do PDF com vinculos empregaticios

        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus.flowables import Flowable

        # Caminho do arquivo PDF
        vinculos_pdf = BytesIO()

        # DataFrame 'VCLS' já existe em memória (certifique-se de que está preenchido)
        # VCLS = ...

        # Adicionando um atributo 'name' ao DataFrame 'VCLS'
        VCLS.name = 'VCLS'

        # Classe para adicionar uma linha ao documento
        class LineBreak(Flowable):
            def __init__(self, width, height=0,color=colors.black):
                super().__init__()
                self.width = width
                self.height = height
                self.color = color

            def draw(self):
                self.canv.setStrokeColor(self.color)
                self.canv.line(0, self.height, self.width, self.height)

        # Função para criar o PDF a partir do DataFrame
        def create_pdf(dataframe, filename):
            # Configurar o tamanho da página
            doc = SimpleDocTemplate(filename, pagesize=letter)

            # Adicionar o título ao documento usando o estilo de parágrafo
            styles = getSampleStyleSheet()
            title = f"Anexo A - Vínculos Empregatícios Identificados"
            title_paragraph = Paragraph(title, styles['Title'])

            # Adicionar a linha abaixo do título
            line = LineBreak(455, height=1,color=colors.orangered)

            # Adicionar o primeiro texto abaixo do título
            additional_text = """
            Na relação abaixo constam os vínculos encontrados em seu extrato (CNIS). Caso não encontre algum vínculo empregatício,
            recomenda-se que agende uma visita a um posto do INSS para resolver o problema caso avalie conveniente. Alguns possíveis exemplos dessa
            situação são: não inclusão do período do serviço militar, residência médica, ausência de registro do empregador dentre outros.
            """
            additional_paragraph = Paragraph(additional_text, styles['BodyText'])

            # Adicionar o segundo texto abaixo do primeiro
            additional_text_2 = """
            Verifique o numero de vínculos, a data início e a data fim dos vínculos. Verique se as informações
            coincidem com seus documentos de registro (carteira de trabalho, carnes, etc ) pois omições
            podem ter impacto na análise do benefício estimado e benefício de aposentadoira do INSS.
            """
            additional_paragraph_2 = Paragraph(additional_text_2, styles['BodyText'])

            # Adicionar o terceiro texto abaixo do segundo
            additional_text_3 = """
            Cada linha apresenta as seguintes informações nesta ordem: nome do vínculo, tipo de filiação, data início/fim.
            """
            additional_paragraph_3 = Paragraph(additional_text_3, styles['BodyText'])

            # Converter o DataFrame para um formato tabular
            table_data = [list(dataframe.columns)] + dataframe.applymap(str).values.tolist()

            # Criar a tabela com largura ajustada automaticamente e centralizada na horizontal
            table = Table(table_data, colWidths=[None] * len(dataframe.columns), hAlign='CENTER')

            # Configurar o estilo da tabela com cores alternadas
            style = TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])

            # Adicionar o estilo às linhas alternadas
            for i in range(1, len(table_data), 2):
                style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)  # Linhas ímpares em cinza

            table.setStyle(style)

            # Adicionar o quarto texto abaixo da tabela
            additional_text_4 = """
            Para mais informações, procure a agência do INSS mais próxima para regularizar sua situação.
            """
            #Para mais informações, procure a agência do INSS mais próxima para regularizar sua situação ou agende uma consulta
            #com nossos parceiros para detalhamento de sua situação.
            additional_paragraph_4 = Paragraph(additional_text_4, styles['BodyText'])

            # Adicionar os elementos ao documento
            content = [line,title_paragraph, line, additional_paragraph, additional_paragraph_2, additional_paragraph_3,Spacer(1, 0.1 * inch),line, Spacer(1, 0.2 * inch), table, additional_paragraph_4]

            # Construir o documento
            doc.build(content)

        # Chamar a função para criar o PDF usando o DataFrame existente 'VCLS'
        create_pdf(VCLS, vinculos_pdf)

        #CRIACAO do pdf com dados do filiado
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus.flowables import Flowable

        # Caminho do arquivo PDF
        filiado_pdf = BytesIO()

        # Adicionando um atributo 'name' ao DataFrame 'ATNTV'
        ATNTV.name = 'ATNTV'

        # Classe para adicionar uma linha ao documento
        class LineBreak(Flowable):
            def __init__(self, width, height=0,color=colors.black):
                super().__init__()
                self.width = width
                self.height = height
                self.color = color

            def draw(self):
                self.canv.setStrokeColor(self.color)
                self.canv.line(0, self.height, self.width, self.height)

        # Função para criar o PDF a partir do DataFrame
        def create_pdf(dataframe, filename):
            # Configurar o tamanho da página
            doc = SimpleDocTemplate(filename, pagesize=letter)

            # Adicionar o título ao documento usando o estilo de parágrafo
            styles = getSampleStyleSheet()
            title = f"Análise do Extrato da Previdencia (CNIS)"
            title_paragraph = Paragraph(title, styles['Title'])

            title2 = f"ALTERNATIVAS APOSENTADORIA"
            title_2 = Paragraph(title2, styles['Title'])

            title3 = f"Descrição de Regras de Aposentadoria"
            title_3= Paragraph(title3, styles['Title'])

            # Adicionar a linha abaixo do título
            line = LineBreak(455, height=1,color=colors.orangered)

            # Modificar o texto additional_text para incluir a variável NOME em negrito
            #additional_text = f"<b>NOME:</b> {NOME}"
            #additional_text = f"<font color='red'><b>NOME:</b> {NOME}</font>"

            #nome_text = f"<b>NOME:</b> <font color='red'>{NOME}</font>"
            nome_text = f"<para align=center><font color='red'>{NOME}</font></para>"
            nome = Paragraph(nome_text, styles['BodyText'])

            cadastro_text = f"<b>DADOS CADASTRAIS</b>"
            cadastro = Paragraph(cadastro_text, styles['BodyText'])

            nit_text = f"<b>NIT:</b> {NIT}"
            nit = Paragraph(nit_text, styles['BodyText'])

            cpf_text = f"<b>CPF:</b> {CPF}"
            cpf = Paragraph(cpf_text, styles['BodyText'])

            nasc_text = f"<b>Nascimento:</b> {NASCI}"
            nascimento = Paragraph(nasc_text, styles['BodyText'])

            mae_text = f"<b>Mãe:</b> {MAE}"
            mae = Paragraph(mae_text, styles['BodyText'])

            ingresso_text = f"<b>Data Ingresso INSS:</b> {DatInic}"
            ingresso = Paragraph(ingresso_text, styles['BodyText'])

            extrato_text = f"<b>Data Extrato CNIS:</b> {DTEXT}"
            extrato = Paragraph(extrato_text, styles['BodyText'])

            data_atual2 = datetime.now().strftime("%d/%m/%Y")
            analise_text = f"<b>Data Análise CNIS:</b> {data_atual2}"
            analise = Paragraph(analise_text, styles['BodyText'])

            idade_text = f"<b>Idade Atual:</b> {IDATUAL}"
            idade = Paragraph(idade_text, styles['BodyText'])

            contribuicao_text = f"<b>Tempo Contribuição:</b> {CTBf}"
            contribuicao = Paragraph(contribuicao_text, styles['BodyText'])  

            nrosal_text = f"""<b>Contribuições abaixo do Salário Mínimo :</b> {Texsalmin}"""
            nrosal = Paragraph(nrosal_text, styles['BodyText'])  

            text_3 = f"""
            Alternativas de aposentadoria para <b>{NOME}</b>, considerando as informações
            disponíveis no extrato previdenciário (CNIS).
            """
            additional_3 = Paragraph(text_3, styles['BodyText'])

            notaimportante=f"""
            <b>NOTA IMPORTANTE:</b> {TexBnfIdd}
            """
            # Criar um estilo personalizado baseado em 'BodyText'
            custom_body_text = ParagraphStyle \
            ('CustomBodyText',parent=styles['BodyText'],backColor=colors.lightgrey, \
            borderWidth=1,borderPadding=5,borderColor=colors.black,borderStyle='dashed')
            nt_i = Paragraph(notaimportante, custom_body_text)

            observacao_text = f"<b>Notas Explicativas da Tabela:</b>"
            observacao = Paragraph(observacao_text, styles['BodyText'])

            additional_text_4 = f"""
            (1) <b>Regra:</b> coluna indica a que regras de aposentadoria tem acesso em função
            das características de filiação ao INSS (data de filiação, idade, contribuições). 
            As regras são da EC103/2019 para trabalhador urbano do RGPS focando nas cinco principais e
            que abrangem o maior numero de filiados (idade, 50% pedagio, 100% pedagio, pontos,
            idade progressiva). No bloco <b>"Descrição de Regras"</b> são detalhadas as características
            das regras que aparecem na tabela acima.
            """
            additional_paragraph_4 = Paragraph(additional_text_4, styles['BodyText'])

            text_5 = f"""
            (2) <b>Data Aposentadoria:</b> coluna da data estimada para aposentadoria por esta regra
            se continuar a contribuir mensalmente com o valor indicado nas respectivas colunas da tabela.
            """
            additional_5 = Paragraph(text_5, styles['BodyText'])

            text_6 = f"""
            (3) <b>Benefício Estimado:</b> coluna do benefício simulado para aposentadoria por esta regra
            se continuar a contribuir mensalmente com o salário bruto na respectiva linha da tabela.
            """
            additional_6 = Paragraph(text_6, styles['BodyText'])

            text_7 = f"""
            (4) <b>Numero Futuro Contribuições:</b> coluna do numero de contribuições futuras simuladas
            para aposentadoria por esta regra se continuar a contribuir mensalmente com o valor indicado
            nas respectivas colunas da tabela.
            Se numero de contribuições futuras indicado nesta linha da tabela for <b>ZERO</b>
            a aposentadoria por esta regra esta condicionada exclusivamente a estimativa da Data Aposentadoria.
            """
            additional_7 = Paragraph(text_7, styles['BodyText'])

            text_8 = f"""
            (5) <b>Salário Futuro Bruto:</b> esta coluna define o salario bruto mensal utilizado no processo
            de simulação do benefício estimado. A definição acontece pela relação do salário bruto
            indicado (atual/esperado) pelo contribuinte com Salario Mínimo e Teto do INSS.
            O salário bruto norteia o nivel de contribuições para o INSS.
            Caso o salário bruto indicado (atual/esperado) seja menor que o Salário Mínimo o processo de
            simulação do benefício estimado assume como valor o Salário Mínimo por critério de suficiência.
            """
            additional_8 = Paragraph(text_8, styles['BodyText'])

            # Adicionar o segundo texto abaixo do primeiro
            additional_text_2 = """
            É <b>recomendavel executar de tempos em tempos esta análise</b> com seu Extrato de Previdencia (CNIS) 
            atualizado para que os valores indicados reflitam sua realidade na tomada de decisao
            de aposentadoria. 
            Providências podem ser necessárias para adequacão de informações que constam no seu extrato (CNIS)
            pois estas podem influir nos valores e alternativas de aposentadoria apresentadas nesta analise.
            Verifique os <b>anexos "Vínculos Empregatícios" e "Indicadores"</b> para avaliar ações
            corretivas. 
            """
            additional_paragraph_2 = Paragraph(additional_text_2, styles['BodyText'])

            texto_id = f"""
            <b>Idade:</b> para os homens a idade mínima continua em 65 anos. Para as mulheres começa em 60
        anos. Mas, a partir de 2020, a idade mínima de aposentadoria da mulher é acrescida de seis meses a
        cada ano, até chegar a 62 anos em 2023. O tempo mínimo de contribuição exigido é de pelo menos 15
        anos para ambos os sexos exceto para homens que se filiem à Previdência apos EC103/19 (13/11/19)
        que devem ter 20 anos. O benefício será calculada a partir da média de todos os salários de contribuição
        (a partir de julho 1994), com a aplicação da regra de 60% do valor do benefício integral por
        15/20 anos de contribuição, crescendo 2% a cada ano adicional de contribuição.
            """
            additional_rgid = Paragraph(texto_id, styles['BodyText']) 

            # Converter o DataFrame para um formato tabular
            table_data = [dataframe.columns] + dataframe.values.tolist()

            # Criar a tabela com largura ajustada automaticamente e centralizada na horizontal
            table = Table(table_data, hAlign='CENTER')

            # Configurar o estilo da tabela com cores alternadas
            style = TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.black),])

            # Adicionar o estilo às linhas alternadas
            for i in range(1, len(table_data), 2):
                style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)  # Linhas ímpares em cinza

            table.setStyle(style)

            # Adicionar os elementos ao documento
            content = [line,title_paragraph, line, nome,Spacer(1, 0.1 * inch),line,\
                    cadastro,nit,cpf,nascimento,mae,ingresso,extrato,analise,idade,contribuicao,nrosal,\
                    Spacer(1, 0.1 * inch),\
                    line,title_2,line,additional_3,Spacer(1, 0.1 * inch),table,Spacer(1, 0.1 * inch),nt_i,Spacer(1, 0.1 * inch),observacao, additional_paragraph_4,additional_5,\
                    additional_6,additional_7,additional_8, additional_paragraph_2,Spacer(1, 0.1 * inch),\
                    line,title_3,line,additional_rgid]
            if Regptos == 1:
                texto_pts = f"""
                <b>Pontos:</b> o trabalhador deve alcançar uma pontuação que resulta da soma de sua idade mais o tempo
                de contribuição. O número inicial será de 86 para as mulheres e 96 para os homens em 2019, respeitando
                o tempo mínimo de contribuição que vale hoje (35anos para homens e 30 anos para mulheres). 
                A regra prevê um aumento de 1 ponto a cada ano, chegando a 100 para mulheres (em 2033)
                e 105 para os homens (em 2028). O benefício será calculada a partir da média de todos os
                salários de contribuição (a partir de julho 1994), com a aplicação da regra de 60% do valor
                do benefício integral por 15/20 anos de contribuição, crescendo 2% a cada ano adicional
                de contribuição.
                """
                additional_rgpts = Paragraph(texto_pts, styles['BodyText'])
                content.append(additional_rgpts)

            if Regprg==1:
                texto_prg = f"""
                <b>Progressiva:</b> nessa regra, a idade mínima começa em 56 anos para mulheres e 61 para
                os homens em 2019, subindo meio ponto a cada ano até que a idade de 65 (homens) e 62 (mulheres) seja
                atingida. Em 12 anos (2031) acaba a transiçãopara as mulheres e em 8 anos (2027) para
                os homens. Nesse modelo, é exigido um tempo mínimo decontribuição: 30 anos para mulheres
                e 35 para homens. O benefício será calculada a partir da média de todos os salários de
                contribuição (a partir de julho 1994), com a aplicação da regra de 60% do valor do benefício
                integral por 15/20 anos de contribuição, crescendo 2% a cada ano adicional de contribuição.
                """
                additional_rgprg = Paragraph(texto_prg, styles['BodyText'])
                content.append(additional_rgprg)

            if Reg100==1:
                texto_100 = f"""
                <b>Pedagio100 :</b> nesta regra, trabalhadores que estavam a mais dois anos da aposentadoria
                em 13/11/19 (EC103/19) devem cumprir os seguintes requisitos:idade mínima de 57 anos para
                mulheres e de 60 anos para homens, além um "pedágio 100%" equivalente ao tempo que faltava para
                cumprir o tempo mínimo de contribuição (30 anos se mulher e 35 anos se homem) na data
                em que a EC103/19 entrou em vigor. Nessa regra, o benefício será de 100% da média
                de todos os salários.
                """
                additional_100 = Paragraph(texto_100, styles['BodyText'])
                content.append(additional_100)

            if Reg50==1:
                texto_50 = f"""
                <b>Pedagio50 :</b> nesta regra, trabalhadores que estavam a menos dois anos da aposentadoria
                em 13/11/19 (EC103/19) devem cumprir os seguintes requisitos: estarem a menos
                de dois anos para aposentadoria na data da EC103/19 mulheres com mais de 28 anos contribuição
                e homens com mais de 33 anos de contribuição, além um "pedágio 50%" equivalente a metade do tempo
                que faltava para cumprir o tempo mínimo de contribuição (30 anos se mulher e 35 anos se homem) na data 
                em que a PEC entrou em vigor independente da idade.Trabalhadores que se enquadrem regra
                também pode utilizar a regra de "pedágio 100%" se for mais vantagosa. Nessa regra, a remuneração
                será a média de todos os salários de contribuição multiplicada pelo fator previdenciário.
                """
                additional_50 = Paragraph(texto_50, styles['BodyText'])
                content.append(additional_50)

            if Reg100to50==1:
                texto_100 = f"""
                <b>Pedagio100 :</b> nesta regra, trabalhadores que estavam a mais dois anos da aposentadoria
                em 13/11/19 (EC103/19) devem cumprir os seguintes requisitos:idade mínima de 57 anos para
                mulheres e de 60 anos para homens, além um "pedágio 100%" equivalente ao tempo que faltava para
                cumprir o tempo mínimo de contribuição (30 anos se mulher e 35 anos se homem) na data
                em que a EC103/19 entrou em vigor. Nessa regra, o benefício será de 100% da média
                de todos os salários.
                """
                additional_100 = Paragraph(texto_100, styles['BodyText'])
                content.append(additional_100)



            # Adicionar a tabela ao conteúdo após a construção do documento
            #content.append(PageBreak())
            #content.append(table)

            # Construir o documento
            doc.build(content)

        # Chamar a função para criar o PDF usando o DataFrame existente 'VCLS'
        create_pdf(ATNTV, filiado_pdf)

        #ENCONTRA lEGENDA DE INDICADORES no df df_SGS

        import pdfplumber
        import re

        padraoS = r'([A-Z]{3,}[A-Z0-9\-]*)\s'
        df_SGS = pd.DataFrame(columns=['Elemento'])  # Inicializa o DataFrame para armazenar elementos encontrados

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                for i, line in enumerate(lines):
                    if "Legenda" in line:
                        # Inicia busca por elementos que estejam no padrãoS
                        for j in range(i + 1, len(lines)):
                            if "autenticidade" in lines[j] or "constantes" in lines[j]:
                                # Interrompe a guarda de elementos ao encontrar 'autenticidade' ou 'constantes'
                                break

                            #match = re.search(padraoS, lines[j])
                            matches = re.finditer(padraoS, lines[j])
                            #print(matches)
                            for match in matches:
                                elemento = match.group(1)
                                #print(elemento)
                                if elemento != 'INSS':
                                    # Se o elemento for diferente de 'INSS', guarda no DataFrame SGS
                                    df_SGS = pd.concat([df_SGS, pd.DataFrame({'Elemento': [elemento]})], ignore_index=True)

        # Imprime o DataFrame resultante com alinhamento à esquerda
        pd.set_option('display.max_colwidth', None)
        df_SGS_styled = df_SGS.style.set_properties(**{'text-align': 'left'})

        #importa todas as tabelas d pdf SEM quebras \n E +d 1 tabela por pagina E salva dataframe sgls

        import pdfplumber

        my_path = os.path.join('static', 'assets', 'arquivos', 'mysiglas.pdf')

        def process_table(table):
            for i in range(len(table)):
                for j in range(len(table[i])):
                    cell = table[i][j]
                    if '\n' in cell:
                        if j == 2:
                            # Se '\n' estiver na terceira posição, remove o padrão
                            table[i][j] = cell.replace('\n', '')
                        else:
                            # Se '\n' estiver em qualquer outra posição, substitui por espaço
                            table[i][j] = cell.replace('\n', ' ')
            return table

        # Criar um DataFrame vazio
        mysgls = pd.DataFrame(columns=['Tipo', 'Grupo', 'Indicador', 'Descricao', 'Esclarecimentos'])

        with pdfplumber.open(my_path) as pdf:
            for page_number in range(len(pdf.pages)):
                # Obtém a página
                page = pdf.pages[page_number]

                # Extrai todas as tabelas da página
                tables = page.extract_tables()

                if tables:
                    #print(f"Tabelas da Página {page_number + 1}:")

                    # Itera sobre cada tabela e imprime as primeiras 3 linhas (ou todas se houver menos de 3)
                    for table_number, table in enumerate(tables):
                        cleaned_table = process_table(table)
                        for row in cleaned_table:
                            # Adiciona uma nova linha ao DataFrame mysgls
                            mysgls = pd.concat([mysgls, pd.DataFrame([{
                                'Tipo': row[0],
                                'Grupo': row[1],
                                'Indicador': row[2],
                                'Descricao': row[3],
                                'Esclarecimentos': row[4]
                            }])], ignore_index=True)

        # Aplicar estilo para alinhar à esquerda
        mysgls_styled = mysgls.style.set_properties(**{'text-align': 'left'})
        # Exibir o DataFrame estilizado
        mysgls_styled

        #CRIACAO do df mylgdi usando coluna Elemente do df df_SGS e coluna Indicador do df mysgls


        # Suponha que você já tenha seus dataframes df_SGS e mysgls carregados

        # Crie o dataframe mylgdi vazio com as colunas desejadas
        mylgdi = pd.DataFrame(columns=['Indicador', 'Tipo', 'Grupo', 'Descricao', 'Esclarecimentos'])

        # Itere sobre os itens da coluna 'Elemento' em df_SGS
        for elemento in df_SGS['Elemento']:
            # Use str.contains para verificar se o padrão está presente na coluna 'Indicador' de mysgls
            resultado_busca = mysgls[mysgls['Indicador'].str.contains(elemento, case=False, na=False)]

            # Se encontrar alguma correspondência, adicione ao dataframe mylgdi
            if not resultado_busca.empty:
                mylgdi = pd.concat([mylgdi, resultado_busca[['Indicador', 'Tipo', 'Grupo', 'Descricao', 'Esclarecimentos']]])

        # Resetando os índices do dataframe resultante
        mylgdi.reset_index(drop=True, inplace=True)

        # Aplicar estilo para alinhar à esquerda
        mylgdi_styled = mylgdi.style.set_properties(**{'text-align': 'left'})
        # Exibir o DataFrame estilizado
        mylgdi_styled

        #CRIACAO do pdf indicadores, resultado da busca e insercao de informacao s indicadores

        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus.flowables import Flowable

        # Caminho do arquivo PDF
        indicadores_pdf = BytesIO()
        #Adicionando um atributo 'name' ao DataFrame 'mylgdi'
        mylgdi.name = 'mylgdi'

        # Classe para adicionar uma linha ao documento
        class LineBreak(Flowable):
            def __init__(self, width, height=0,color=colors.black):
                super().__init__()
                self.width = width
                self.height = height
                self.color = color

            def draw(self):
                self.canv.setStrokeColor(self.color)
                self.canv.line(0, self.height, self.width, self.height)

        # Função para criar o PDF a partir do DataFrame
        def create_pdf(dataframe, filename, dataframe_name):
            # Configurar o tamanho da página
            doc = SimpleDocTemplate(filename, pagesize=letter)

            # Converter o DataFrame para um formato tabular
            table_data = dataframe.applymap(str).values.tolist()

            # Criar a tabela
            table = Table(table_data, colWidths=[1.5 * inch] * len(dataframe.columns))

            # Configurar o estilo da tabela
            style = TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.black)])
            table.setStyle(style)

            # Adicionar o título ao documento usando o estilo de parágrafo
            styles = getSampleStyleSheet()
            title = f"Anexo B - Indicadores"
            title_paragraph = Paragraph(title, styles['Title'])

            # Adicionar a linha abaixo do título
            line = LineBreak(455, height=1,color=colors.orangered)

            # Acrescentar parágrafos adicionais
            info_paragraph1 = Paragraph("Informações detalhadas são apresentadas abaixo dos indicadores encontrados no seu extrato (CNIS).", styles['BodyText'])
            info_paragraph2 = Paragraph("No extrato previdenciário (CNIS) são utilizados indicadores para \
            informar sobre períodos de contribuição e/ou contribuições que podem precisar de alguma \
            ação, providência ou atenção do filiado.", styles['BodyText'])

            # Adicionar os parágrafos ao documento
            content = [line,title_paragraph, line, info_paragraph2, info_paragraph1,Spacer(1, 0.1 * inch),line,Spacer(1, 0.2 * inch)]

            # Adicionar cada linha da tabela ao conteúdo do documento
            for i, row in enumerate(table_data):
                row_paragraphs = []
                for j, cell in enumerate(row):
                    cell_text = str(cell)

                    # Adicionar Spacer para separar as células na mesma linha
                    if j > 0:
                        row_paragraphs.append(Spacer(1, 1))

                    # Adicionar número da linha e texto em negrito no início da primeira célula
                    if j == 0:
                        cell_text = f'<b>{i + 1})</b> {cell_text}'

                    # Adicionar texto em negrito no início de células específicas
                    elif j == 1:
                        cell_text = f'<b>Tipo:</b> {cell_text}'
                    elif j == 2:
                        cell_text = f'<b>Grupo:</b> {cell_text}'
                    elif j == 3:
                        cell_text = f'<b>Descricao:</b> {cell_text}'
                    elif j == 4:
                        cell_text = f'<b>Esclarecimentos:</b> {cell_text}'

                    # Adicionar cada linha da célula como um parágrafo
                    cell_paragraph = Paragraph(cell_text, styles['BodyText'])
                    row_paragraphs.append(cell_paragraph)

                # Adicionar todas as células da linha ao conteúdo
                content.extend(row_paragraphs)

            # Construir o documento
            doc.build(content)

        # Chamar a função para criar o PDF usando o DataFrame existente 'mylgdi'
        create_pdf(mylgdi, indicadores_pdf, mylgdi.name)

        #XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        import PyPDF2
        from datetime import datetime
        import os
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import gray, black,white, orangered  # Cor para a linha
        import io
        
        def add_page_numbers_and_header(pdf_buffer):
            # Criar um buffer para armazenar as alterações
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Ler o PDF existente do buffer
            existing_pdf = PyPDF2.PdfReader(pdf_buffer)
            number_of_pages = len(existing_pdf.pages)
            page_width, page_height = letter
            header_height = 50  # Altura do cabeçalho
            line_position_x = 50  # Posição x da linha vertical
            footer_height = 20   # Altura do texto no rodapé
            image_path = './static/assets/GRP branding.LOGOMARCA.png'

            font_name = "Helvetica-Bold"
            header_text = "GrP - Análise Previdência"
            header_font_size = 24
            vertical_text = "Relatorio Analitico Previdenciario - GrP"
            vertical_font_size = 14  # Tamanho da fonte para o texto vertical

            for page_number in range(number_of_pages):
                if page_number == 0:
                    can.setFillColor(orangered)
                    can.rect(0, 735, page_width, header_height, stroke=0, fill=1)
                    can.setFont(font_name, header_font_size)
                    can.setFillColor(white)
                    header_text_width = can.stringWidth(header_text, font_name, header_font_size)
                    can.drawString((page_width - header_text_width) / 2, 750, header_text)
                else:
                    # Linha vertical e texto
                    can.setLineWidth(5)  # Espessura da linha
                    can.setStrokeColor(orangered)  # Cor da linha
                    can.line(line_position_x, letter[1] - footer_height, line_position_x, footer_height + 10)
                    can.saveState()
                    can.translate(line_position_x - 10, letter[1] / 2)  # Deslocamento para centralizar o texto
                    can.rotate(90)
                    can.setFont(font_name, vertical_font_size)
                    can.setFillColor(black)
                    can.drawCentredString(0, 0, vertical_text)  # Centraliza o texto no ponto de rotação
                    can.restoreState()

                    # Desenha a imagem como marca d'água no canto superior direito
                    image_width = 30  # Largura da imagem, ajuste conforme necessário
                    image_height = 50  # Altura da imagem, ajuste conforme necessário
                    image_x = page_width - image_width - 10  # Posiciona a imagem a 10 pixels da borda direita
                    image_y = page_height - image_height - 10  # Posiciona a imagem a 10 pixels da borda superior
                    can.drawImage(image_path, image_x, image_y, width=image_width, height=image_height, mask='auto')

                # Números de página no rodapé
                can.setFont("Helvetica", 10)
                can.setFillColor(black)
                page_text = f"Página {page_number + 1} de {number_of_pages}"
                page_text_width = can.stringWidth(page_text, "Helvetica", 10)
                can.drawString(page_width - page_text_width - 40, 20, page_text)
                can.drawString((page_width - can.stringWidth("GrP", "Helvetica", 12)) / 2, 20, "GrP")
                can.drawString(40, 20, "guiarendaprevidencia.com.br")

                can.showPage()

            can.save()

            # Retornar o buffer para o início
            packet.seek(0)

            # Lendo o novo PDF com o cabeçalho e números de página
            new_pdf = PyPDF2.PdfReader(packet)

            # Criando o escritor de saída
            output = PyPDF2.PdfWriter()
            for page_number in range(number_of_pages):
                page = existing_pdf.pages[page_number]
                page.merge_page(new_pdf.pages[page_number])
                output.add_page(page)

            # Criar um novo buffer para o PDF final
            final_buffer = io.BytesIO()
            output.write(final_buffer)
            final_buffer.seek(0)  # Voltar ao início do buffer para leitura posterior

            return final_buffer


        def merge_pdfs(filepaths):
            pdf_writer = PyPDF2.PdfWriter()
            for filepath in filepaths:
                if isinstance(filepath, BytesIO):
                    filepath.seek(0)
                    pdf_reader = PyPDF2.PdfReader(filepath)
                else:
                    pdf_reader = PyPDF2.PdfReader(filepath)

                # Adiciona todas as páginas ao writer
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)

            # Armazena o PDF no buffer em vez de no disco
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            output_buffer.seek(0)  # Certifique-se de que estamos no início para leitura posterior

            # Adicionar numeração e cabeçalho
            final_pdf_with_header = add_page_numbers_and_header(output_buffer)

            return final_pdf_with_header

        def criar_nome_pdf(nome):
            nome_arquivo = '_'.join(nome.split()[:2])
            data_hora_atual = datetime.now().strftime("%Y-%d-%m %H-%M-%S")
            nome_pdf = f"{nome_arquivo}_{data_hora_atual}.pdf"
            return nome_pdf


        pdf_files = [filiado_pdf, vinculos_pdf, indicadores_pdf]
        pdf = merge_pdfs(pdf_files)

        atntv_html = ATNTV.to_dict(orient="records")
    
        return pdf, atntv_html
    
    except Exception as err:
        print(err)
        return render_template('calculadora.html', error_relatorio="Tivemos um erro inesperado, por favor, entre em contato com o suporte")


def verifica_cnis(cnis_path):
    import pdfplumber
    import re

    pdf_path = cnis_path

    # Use pdfplumber para extrair texto e informações de layout
    with pdfplumber.open(pdf_path) as pdf:
        D_V = []#recebe pares datas&valores filtrados
        for i in range(1):  # ajusta numero de paginas extraidas
            page = pdf.pages[i]
            text = page.extract_text()
            lines = text.split('\n')#transforma cada linha em uma string
            #print(elements)
            #print(page)
            pare = 0
            contapalavras = 0
            for line in lines:
                if "Civil" in line:#para a busca/for ao encontrar a palavra Civil em alguma linha 
                    break
                if pare == 1:
                    break
                elements = re.findall(r'\S+', line)#transforma linha/string em uma lista com os elementos da string
                #print(elements)

                for i in range(len(elements)):
                    # Verifica se o elemento atual é 'CNIS::'
                    if elements[i] == 'CNIS':
                        contapalavras = contapalavras+1
                    # Verifica se o elemento atual é 'Extrato:'
                    if elements[i] == 'Extrato':
                        contapalavras = contapalavras+1
                     # Verifica se o elemento atual é 'NIT:'    
                    if elements[i] == 'NIT:':
                        contapalavras = contapalavras+1
                    if contapalavras == 3:
                        pare = 1
    return contapalavras

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
            empresa = Empresa.query.filter_by(id=user.empresa_id).first()
            
            if empresa:
                dias_restantes = verificar_acesso_empresa(empresa)

                if dias_restantes >= 0:
                    # Empresa ainda tem dias de acesso
                    token = jwt.encode({
                        'user_id': user.id,
                    }, app.config['SECRET_KEY'], algorithm='HS256')
                    response = jsonify({'token': token, 'message': 'Login bem-sucedido!'})
                    response.set_cookie('auth-token', token, httponly=True)
                    return response, 200  # Retorna um JSON com status 200
                else:
                    # Acesso expirado
                    return jsonify({'message': 'Acesso expirado, prazo de utilização contratado finalizado.'}), 403
            else:
                token = jwt.encode({
                        'user_id': user.id,
                }, app.config['SECRET_KEY'], algorithm='HS256')
                response = jsonify({'token': token, 'message': 'Login bem-sucedido!'})
                response.set_cookie('auth-token', token, httponly=True)
                return response, 200 

        return jsonify({'message': 'Credenciais inválidas.'}), 401

    return render_template('auth/login.html')


@app.route('/calculadora')
@token_required
def dashboard():
    return render_template('calculadora.html')

@app.route('/desejada')
@token_required
def desejada():
    return render_template('desejada.html')

@app.route('/possivel')
@token_required
def possivel():
    return render_template('possivel.html')

@app.route('/perfil')
@token_required
def perfil():
    return render_template('perfil.html')

@app.errorhandler(404)
def page_not_found(e):
    # Exibe uma página 404 personalizada ou redireciona para uma página desejada
    return render_template('404.html'), 404

@app.route('/cadastro')
def cadastro_empresa():
    return render_template('auth/empresaCadastro.html')

@app.route('/')
@token_required
def sobre():
    return render_template('sobre.html')

@app.route('/ia')
@token_required
def ia():
    return render_template('ia.html')

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

@app.route('/grafico_renda_desejada', methods=['POST'])
@token_required
def criar_grafico_rendaDesejada():
    if request.method == 'POST':
        try:
            # Capturar os dados do formulário
            idade_inicial = request.form['id_ini']
            idade_aposentadoria = request.form['id_apos']
            expec_vida = request.form['id_exp']
            reserva = request.form['id_reser']
            inss = request.form['id_inss']
            renda_desejada = request.form['id_dese']
            taxa_real_ano = request.form['id_tx']
            button = request.form['submit-button']

            # Funções de validação
            def validar_inteiro(valor):
                try:
                    return int(valor)
                except ValueError:
                    return None

            def validar_taxa_real(taxa_real):
                if not taxa_real:
                    return "Digite um número MAIOR que zero com no máximo uma casa decimal"
                try:
                    taxa = float(taxa_real)
                    if taxa <= 0 or taxa >= 21:
                        return "Digite um número MAIOR que zero com no máximo uma casa decimal"
                    if '.' in taxa_real:
                        decimal_part = taxa_real.split('.')[1]
                        if len(decimal_part) > 1:
                            return "Digite um número MAIOR que zero com no máximo uma casa decimal"
                except (ValueError, IndexError):
                    return "Digite um número MAIOR que zero com no máximo uma casa decimal"
                return None

            # Validações
            idade_inicial = validar_inteiro(idade_inicial)
            if idade_inicial is None or idade_inicial < 15 or idade_inicial > 100:
                return render_template("desejada.html", error_idade="Digite um número inteiro entre 15 e 100 para a idade inicial", form_data=request.form)

            idade_aposentadoria = validar_inteiro(idade_aposentadoria)
            if idade_aposentadoria is None or idade_aposentadoria < 15 or idade_aposentadoria > 120 or idade_aposentadoria <= idade_inicial:
                return render_template("desejada.html", error_aposentadoria="Digite um número inteiro maior que a idade atual para aposentadoria", form_data=request.form)

            expec_vida = validar_inteiro(expec_vida)
            if expec_vida is None or expec_vida < 15 or expec_vida > 150 or expec_vida <= idade_aposentadoria:
                return render_template("desejada.html", error_vida="Digite um número inteiro maior que a idade de aposentadoria para a expectativa de vida", form_data=request.form)

            reserva = validar_inteiro(reserva)
            if reserva is None or reserva < 0:
                return render_template('desejada.html', error_reserva="Digite um número inteiro maior ou igual a zero para a reserva financeira", form_data=request.form)

            taxa_real_ano_error = validar_taxa_real(taxa_real_ano)
            if taxa_real_ano_error:
                return render_template('desejada.html', error_taxa=taxa_real_ano_error, form_data=request.form)

            inss = validar_inteiro(inss)
            if inss is None or inss < 0:
                return render_template('desejada.html', error_inss="Digite um número inteiro maior ou igual a zero para o benefício esperado do INSS", form_data=request.form)

            renda_desejada = validar_inteiro(renda_desejada)
            if renda_desejada is None or renda_desejada <= 0:
                return render_template('desejada.html', error_desejada="Digite um número inteiro maior que zero para a renda mensal desejada", form_data=request.form)
            # Conversões e cálculos após validações
            ret_invest_anual = float(taxa_real_ano) / 100
            ret_invest_mensal = (1 + ret_invest_anual) ** (1/12) - 1  # Taxa mensal

            # Construir a coluna 'idade'
            idade = np.arange(idade_inicial, expec_vida + 1)

            # Construir a coluna 'Salario'
            salario = np.where(idade < idade_aposentadoria, 0, renda_desejada)

            complemento = renda_desejada - inss

            # Construir a coluna 'Complemento'
            complemento_col = np.where(idade < idade_aposentadoria, 0, complemento)

            # Função que calcula o valor futuro (FV) equivalente à fórmula do Excel
            def FV(rate, nper, pmt):
                if rate == 0:
                    return pmt * nper
                return pmt * ((1 + rate) ** nper - 1) / rate

            # Função para calcular a coluna 'Poupanca'
            def calcular_poupanca(D5, idade, salario, complemento_col, ret_invest_mensal):
                poupanca = np.zeros_like(idade, dtype=float)
                for i in range(len(idade)):
                    if idade[i] < idade_aposentadoria:
                        poupanca[i] = FV(ret_invest_mensal, 12, D5)
                    else:
                        poupanca[i] = -FV(ret_invest_mensal, 12, complemento_col[i])
                return poupanca

            # Função para calcular a coluna 'Acumula'
            def calcular_acumula(poupanca, reserva, ret_invest_anual):
                acumula = np.zeros_like(poupanca, dtype=float)
                acumula[0] = poupanca[0] + reserva * (1 + ret_invest_anual)
                for i in range(1, len(poupanca)):
                    acumula[i] = acumula[i - 1] * (1 + ret_invest_anual) + poupanca[i]
                return acumula

            # Função objetivo para otimização
            def func_objetivo(D5):
                poupanca = calcular_poupanca(D5, idade, salario, complemento_col, ret_invest_mensal)
                acumula = calcular_acumula(poupanca, reserva, ret_invest_anual)
                return abs(acumula[-1])

            # Intervalo de busca para D5
            d5_min = 0.0
            d5_max = 1000000

            # Encontrar o valor ótimo de D5
            D5_otimo = fminbound(func_objetivo, d5_min, d5_max)

            # Calcular as colunas finais usando o valor ótimo de D5
            poupanca_final = calcular_poupanca(D5_otimo, idade, salario, complemento_col, ret_invest_mensal)
            acumula_final = calcular_acumula(poupanca_final, reserva, ret_invest_anual)

            # Criar o DataFrame e formatar as colunas com duas casas decimais
            RDB = pd.DataFrame({
                'Idade': idade,
                'Salario': salario,
                'Complemento': complemento_col,
                'Poupanca': poupanca_final.round(2),
                'Acumula': acumula_final.round(2)
            })
            
            # Configurações do gráfico
            fig, ax1 = plt.subplots(figsize=(13, 7))  # Ajustar o tamanho da figura

            # Eixo X
            ax1.set_xlim([idade_inicial, expec_vida])
            ax1.set_xticks(np.arange(idade_inicial, expec_vida + 1, 5))
            ax1.set_xlabel('Idade', fontweight='bold',fontsize=15)

            # Eixo Y primário
            #max(renda_desejada, D5_otimo) ajuste para qdo poupanca for maior renda desejada
            ax1.set_ylim([0, max(renda_desejada, D5_otimo) + 1000])
            ax1.set_yticks(np.arange(0, max(renda_desejada, D5_otimo) + 2000, 1000))
            ax1.set_ylabel('Renda (R$)', fontweight='bold',fontsize=15)
            ax1.set_yticklabels([f'R${x},00' for x in np.arange(0, max(renda_desejada, D5_otimo) + 2000, 1000)])

            # Plotando a curva de Poupança (pontilhada vermelha)
            ax1.plot(RDB['Idade'][RDB['Idade'] < idade_aposentadoria], 
                    [D5_otimo] * len(RDB['Idade'][RDB['Idade'] < idade_aposentadoria]), 
                    'r.:', linewidth=2, markersize=8, label='Poupança')

            # Plotando a curva de Renda (tracejada verde)
            ax1.plot(RDB['Idade'][(RDB['Idade'] >= idade_aposentadoria - 1) & (RDB['Idade'] <= expec_vida)], 
                    [renda_desejada] * len(RDB['Idade'][(RDB['Idade'] >= idade_aposentadoria - 1) & (RDB['Idade'] <= expec_vida)]), 
                    'g--', linewidth=5, label='Renda')

            # Eixo Y secundário
            ax2 = ax1.twinx()
            ax2.plot(RDB['Idade'], RDB['Acumula'] / 1000, 'b-', linewidth=5, label='Reserva Acumulada')
            ax2.set_ylabel('Reserva Acumulada Milhares (R$)', fontweight='bold',fontsize=15, labelpad=5)  # Ajuste do labelpad

            # Adicionar linha vertical em grey saindo de 'idade_aposentadoria - 1' até RDB.Acumula.max()
            max_acumula = RDB['Acumula'].max() / 1000  # Convertendo para milhares
            ax2.axvline(x=idade_aposentadoria - 1, color='grey', linestyle='--')
            ax2.plot([idade_aposentadoria - 1, idade_aposentadoria - 1], [0, max_acumula], color='grey', linestyle='--')

            # Formatar os rótulos do eixo Y secundário
            ticks = np.linspace(0, max_acumula, num=6)
            ax2.set_yticks(ticks)
            ax2.set_yticklabels([f'R${int(x)}000,00' for x in ticks])

            # Título
            plt.title('Condições para Renda Desejada', fontweight='bold',fontsize=20)

            # Legendas
            handles1, labels1 = ax1.get_legend_handles_labels()
            handles2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, fontsize=15)

            # Adicionar caixa de texto com informações adicionais ao lado direito do gráfico
            info_text = (
                f"{'RESUMO':^30}\n\n"  # Inserir 'RESUMO' em negrito e centralizado
                f"Aposentadoria aos {idade_aposentadoria} anos\n\n"
                f"Reserva Atual\n"
                f"R$ {reserva:,.0f}\n\n"
                f"Reserva aos {idade_aposentadoria} anos\n"
                f"R$ {RDB['Acumula'].max():,.0f}\n\n"
                f"Poupança até {idade_aposentadoria} anos (P)\n"
                f"R$ {D5_otimo:,.0f}/mês\n\n"
                f"Renda INSS (1)\n"
                f"R$ {inss:,.0f}\n\n"
                f"Renda Investimento (2)\n"
                f"R$ {RDB['Complemento'].max():,.0f}\n\n"
                f"Renda DESEJADA (1)+(2)\n"
                f"R$ {renda_desejada:,.0f}/mês\n"
            )
            plt.gcf().text(1.17, 0.5, info_text, fontsize=15, bbox=dict(facecolor='white', alpha=0.5), transform=ax1.transAxes, verticalalignment='center')

            # Adicionar anotação para a linha verde
            ax1.annotate(
                '(1)+(2)',
                xy=(idade_aposentadoria, renda_desejada),
                xytext=(idade_aposentadoria + 10, renda_desejada + 200),
                fontsize=20,
                ha='center',
                fontweight='bold'
            )

            # Adicionar anotação para a curva vermelha
            ax1.annotate(
                'P',
                xy=(idade_inicial + (idade_aposentadoria - idade_inicial) / 2, D5_otimo),
                xytext=(idade_inicial + (idade_aposentadoria - idade_inicial) / 2, D5_otimo + 100),
                #xytext=(idade_aposentadoria - 15, D5_otimo + 100),  # Ajuste aqui para mudar a posição do texto
                fontsize=20,
                ha='center',
                fontweight='bold',
                color='red'
            )

            # Adicionar anotação para a curva azul
            ax2.annotate(
                '(2)\n',
                xy=(idade_inicial + (idade_aposentadoria - idade_inicial) / 2, max_acumula),
                xytext=(idade_aposentadoria + (expec_vida - idade_aposentadoria) / 2, max_acumula / 2),  # Ajuste aqui para mudar a posição do texto
                fontsize=20,
                ha='center',
                fontweight='bold',
                color='black'
            )

            # Adicionar nota de rodapé
            fig.text(0.0, -0.05, 'Este gráfico é apenas uma simulação e não deve ser usado como único instrumento para decisões financeiras.\n'
                                'Consulte um especialista antes de tomar qualquer decisão financeira.', 
                    fontsize=15)

            # Ajustando layout
            plt.tight_layout(rect=[0, 0, 0.95, 1])

            if button == "2":
                graph = io.BytesIO()
                plt.savefig(graph, format='pdf', bbox_inches='tight')
                graph.seek(0)
                return send_file(graph, as_attachment=True, download_name='GráficoDesejada.pdf')
            
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            img.seek(0)
            graph_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

            # Enviar o gráfico codificado para o frontend
            return render_template('desejada.html', graph_base64=graph_base64, form_data = request.form)
        
        except Exception as err:
            print(err)
            return render_template('desejada.html', error_server="Tivemos um problema nos nossos servidores, por favor, entre em contato imediatamente com o suporte", form_data= request.form)


#funcao cria grafico renda possivel
@app.route('/grafico_renda_possivel', methods=['POST', 'GET'])
@token_required
def criar_grafico_rendaPossivel():
    try:

        if request.method == 'POST':
            idade_inicial = request.form['id_ini']
            idade_aposentadoria = request.form['id_apos']
            expec_vida = request.form['id_exp']
            reserva = request.form['id_reser']
            inss = request.form['id_inss']
            poupanca_possivel = request.form['id_poss']
            ret_invest_anual = request.form['id_tx']

            button = request.form['submit-button']

            if not idade_inicial:
                return render_template('possivel.html', erro_idade_inicial="Digite um número inteiro entre 15 e 100 para a idade atual", form_data=request.form)
            
            idade_inicial = int(idade_inicial)

            if not idade_aposentadoria:
                return render_template('possivel.html', erro_idade_aposentadoria="Digite um número inteiro maior que a idade atual para aposentadoria", form_data=request.form)

            idade_aposentadoria = int(idade_aposentadoria)

            if not expec_vida:
                return render_template('possivel.html', erro_expectativa="Digite um número inteiro maior que a idade de aposentadoria para a expectativa de vida", form_data=request.form)
            
            expec_vida = int(expec_vida)

            if not reserva:
                return render_template('possivel.html', erro_reserva="Digite um número inteiro maior ou igual a zero para a reserva financeira", form_data=request.form)
            
            reserva = float(reserva)

            if not inss:
                return render_template('possivel.html', erro_beneficio="Digite um número inteiro maior ou igual a zero para o benefício esperado do INSS", form_data=request.form)
            
            inss = float(inss)

            if not poupanca_possivel:
                return render_template('possivel.html', erro_poupanca="Digite um número inteiro maior que zero para a poupança mensal possível", form_data=request.form)
            poupanca_possivel = float(poupanca_possivel)

            if not ret_invest_anual:
                return render_template('possivel.html', erro_taxa="Digite um número MAIOR que zero com no máximo uma casa decimal ", form_data=request.form)


            # Validações
            erro_idade_inicial = validar_idade_inicial(idade_inicial)
            erro_idade_aposentadoria = validar_idade_aposentadoria(idade_aposentadoria, idade_inicial, expec_vida)
            erro_expectativa = validar_expectativa(expec_vida, idade_aposentadoria)
            erro_reserva = validar_reserva_financeira(reserva)
            erro_taxa = validar_taxa_real(ret_invest_anual)
            erro_beneficio = validar_beneficio_inss(inss)
            erro_poupanca = validar_poupanca_mensal(poupanca_possivel)

            if erro_idade_inicial or erro_idade_aposentadoria or erro_expectativa or erro_reserva or erro_taxa or erro_beneficio or erro_poupanca:
                return render_template('possivel.html', 
                                    erro_idade_inicial=erro_idade_inicial, 
                                    erro_idade_aposentadoria=erro_idade_aposentadoria, 
                                    erro_expectativa=erro_expectativa, 
                                    erro_reserva=erro_reserva, 
                                    erro_taxa=erro_taxa, 
                                    erro_beneficio=erro_beneficio, 
                                    erro_poupanca=erro_poupanca, form_data=request.form)

            # Convertendo as entradas válidas para o tipo correto
            idade_inicial = int(idade_inicial)
            idade_aposentadoria = int(idade_aposentadoria)
            expec_vida = int(expec_vida)
            reserva = float(reserva)
            inss = float(inss)
            poupanca_possivel = float(poupanca_possivel)
            ret_invest_anual = float(ret_invest_anual) / 100
            ret_invest_mensal = (1 + ret_invest_anual) ** (1/12) - 1 

            # Construir a coluna 'idade'
            idade = np.arange(idade_inicial, expec_vida + 1)

            # Função que calcula o valor futuro (FV) equivalente à fórmula do Excel
            def FV(rate, nper, pmt):
                if rate == 0:
                    return pmt * nper
                return pmt * ((1 + rate) ** nper - 1) / rate

            # Função para calcular a coluna 'Poupanca'
            def calcular_poupanca(D3, idade, ret_invest_mensal):
                poupanca = np.zeros_like(idade, dtype=float)
                for i in range(len(idade)):
                    if idade[i] < idade_aposentadoria:
                        poupanca[i] = FV(ret_invest_mensal, 12, poupanca_possivel)
                    else:
                        poupanca[i] = -FV(ret_invest_mensal, 12, D3)
                return poupanca

            # Função para calcular a coluna 'Acumula'
            def calcular_acumula(poupanca, reserva, ret_invest_anual):
                acumula = np.zeros_like(poupanca, dtype=float)
                acumula[0] = poupanca[0] + reserva * (1 + ret_invest_anual)
                for i in range(1, len(poupanca)):
                    acumula[i] = acumula[i - 1] * (1 + ret_invest_anual) + poupanca[i]
                return acumula

            # Função objetivo para otimização
            def func_objetivo(D3):
                poupanca = calcular_poupanca(D3, idade, ret_invest_mensal)
                acumula = calcular_acumula(poupanca, reserva, ret_invest_anual)
                return abs(acumula[-1])

            # Intervalo de busca para D3
            d3_min = 0.0
            d3_max = 1000000

            # Encontrar o valor ótimo de D3
            D3_otimo = fminbound(func_objetivo, d3_min, d3_max)

            # Calcular as colunas finais usando o valor ótimo de D3
            salario_final = np.where(idade < idade_aposentadoria, 0, inss + D3_otimo)
            poupanca_final = calcular_poupanca(D3_otimo, idade, ret_invest_mensal)
            acumula_final = calcular_acumula(poupanca_final, reserva, ret_invest_anual)

            # Criar o DataFrame e formatar as colunas com duas casas decimais
            RDB = pd.DataFrame({
                'Idade': idade,
                'Salario': salario_final.round(2),
                'Complemento': np.where(idade < idade_aposentadoria, 0, D3_otimo).round(2),
                'Poupanca': poupanca_final.round(2),
                'Acumula': acumula_final.round(2)
            })

            # Configurações do gráfico
            fig, ax1 = plt.subplots(figsize=(13, 7))  # Ajustar o tamanho da figura

            # Eixo X
            ax1.set_xlim([idade_inicial, expec_vida])
            ax1.set_xticks(np.arange(idade_inicial, expec_vida + 1, 5))
            ax1.set_xlabel('Idade', fontweight='bold',fontsize=15)

            # Eixo Y primário
            ax1.set_ylim([0, RDB['Salario'].max() + 2000])
            ax1.set_yticks(np.arange(0, RDB['Salario'].max() + 2000, 1000))
            ax1.set_ylabel('Renda (R$)', fontweight='bold',fontsize=15)
            ax1.set_yticklabels([f'R${int(x)}' for x in np.arange(0, RDB['Salario'].max() + 2000, 1000)])
            #ax1.set_yticklabels([f'R${x},00' for x in np.arange(0, renda_desejada + 2000, 1000)])

            #ticks = np.linspace(0, max_acumula, num=6)
            #x2.set_yticks(ticks)
            #ax2.set_yticklabels([f'R${int(x)}000,00' for x in ticks])

            # Plotando a curva de Poupança (pontilhada vermelha)
            ax1.plot(RDB['Idade'][RDB['Idade'] < idade_aposentadoria], 
                    [poupanca_possivel] * len(RDB['Idade'][RDB['Idade'] < idade_aposentadoria]), 
                    'r.:', linewidth=2, markersize=8, label='Poupança')

            # Plotando a curva de Renda (tracejada verde)
            ax1.plot(RDB['Idade'][(RDB['Idade'] >= idade_aposentadoria - 1) & (RDB['Idade'] <= expec_vida)], 
                    [RDB['Salario'].max()] * len(RDB['Idade'][(RDB['Idade'] >= idade_aposentadoria - 1) & (RDB['Idade'] <= expec_vida)]), 
                    'g--', linewidth=5, label='Renda')

            # Eixo Y secundário
            ax2 = ax1.twinx()
            ax2.plot(RDB['Idade'], RDB['Acumula'] / 1000, 'b-', linewidth=5, label='Reserva Acumulada')
            ax2.set_ylabel('Reserva Acumulada Milhares (R$)', fontweight='bold',fontsize=15, labelpad=5)  # Ajuste do labelpad

            # Adicionar linha vertical em grey saindo de 'idade_aposentadoria - 1' até RDB.Acumula.max()
            max_acumula = RDB['Acumula'].max() / 1000  # Convertendo para milhares
            ax2.axvline(x=idade_aposentadoria - 1, color='grey', linestyle='--')
            ax2.plot([idade_aposentadoria - 1, idade_aposentadoria - 1], [0, max_acumula], color='grey', linestyle='--')

            # Formatar os rótulos do eixo Y secundário
            ticks = np.linspace(0, max_acumula, num=6)
            ax2.set_yticks(ticks)
            ax2.set_yticklabels([f'R${int(x)}000,00' for x in ticks])

            # Título
            plt.title('Condições para Renda Possivel', fontweight='bold',fontsize=20)

            # Legendas
            handles1, labels1 = ax1.get_legend_handles_labels()
            handles2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, fontsize=15)

            # Adicionar caixa de texto com informações adicionais ao lado direito do gráfico
            info_text = (
                f"{'RESUMO':^30}\n\n"  # Inserir 'RESUMO' em negrito e centralizado
                f"Aposentadoria aos {idade_aposentadoria} anos\n\n"
                f"Reserva Atual\n"
                f"R$ {reserva:,.0f}\n\n"
                f"Reserva aos {idade_aposentadoria} anos\n"
                f"R$ {RDB['Acumula'].max():,.0f}\n\n"
                f"Poupança ate {idade_aposentadoria} anos (P)\n"
                f"R$ {poupanca_possivel:,.0f}/mes\n\n"
                f"Renda INSS (1)\n"
                f"R$ {inss:,.0f}\n\n"
                f"Renda Investimento (2)\n"
                f"R$ {RDB['Complemento'].max():,.0f}\n\n"
                f"Renda POSSIVEL (1)+(2)\n"
                f"R$ {RDB['Salario'].max():,.0f}/mes\n"
            )
            plt.gcf().text(1.17, 0.5, info_text, fontsize=15, bbox=dict(facecolor='white', alpha=0.5), transform=ax1.transAxes, verticalalignment='center')
            #plt.gcf().text(1.18, 0.5

            # Adicionar anotação para a linha verde
            ax1.annotate(
                '(1)+(2)',
                xy=(idade_aposentadoria, RDB['Salario'].max()),
                xytext=(idade_aposentadoria + 10, RDB['Salario'].max() +200),
                fontsize=20,
                ha='center',
                fontweight='bold'
            )
            #arrowprops=dict(facecolor='red', shrink=0.05)

            # Adicionar anotação para a curva vermelha
            ax1.annotate(
                'P',
                xy=(idade_inicial + (idade_aposentadoria - idade_inicial) / 2, poupanca_possivel),
                xytext=(idade_inicial + (idade_aposentadoria - idade_inicial) / 2, poupanca_possivel + 100),  # Ajuste aqui para mudar a posição do texto
                fontsize=20,
                ha='center',
                fontweight='bold',
                color='red'
            )

            # Adicionar anotação para a curva azul
            ax2.annotate(
                '(2)\n',
                xy=(idade_inicial + (idade_aposentadoria - idade_inicial) / 2, max_acumula),
                xytext=(idade_aposentadoria + (expec_vida-idade_aposentadoria)/2, max_acumula/ 2),  # Ajuste aqui para mudar a posição do texto
                fontsize=20,
                ha='center',
                fontweight='bold',
                color='black'
            )

            # Adicionar nota de rodapé
            fig.text(0.0,-0.05, 'Este gráfico é apenas uma simulação e não deve ser usado como único instrumento para decisões financeiras.\n'
                                'Consulte um especialista antes de tomar qualquer decisão financeira.', 
                    fontsize=15)

            # Ajustando layout
            plt.tight_layout(rect=[0, 0, 0.95, 1])

            if button == "2":
                graph = io.BytesIO()
                plt.savefig(graph, format='pdf', bbox_inches='tight')
                graph.seek(0)
                return send_file(graph, as_attachment=True, download_name='GráficoPossível.pdf')
            
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            img.seek(0)
            graph_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
            

            # Enviar o gráfico codificado para o frontend
            return render_template('possivel.html', graph_base64=graph_base64, form_data=request.form)
        
        return render_template('possivel.html')
    except Exception as err:
        print(err)
        return render_template('desejada.html', error_server="Tivemos um problema nos nossos servidores, por favor, entre em contato imediatamente com o suporte")


@app.route('/gerar_relatorio', methods=['POST'])
@token_required
def gerar_relatorio():
    try:
        cnis_file = request.files['cnis_file']
        # Construa o caminho absoluto para o arquivo CNIS.pdf
        cnis_buffer = BytesIO()
        cnis_file.save(cnis_buffer)
        cnis_buffer.seek(0)
        n_clicks3 = 0

        sx = request.form['sexo']
        salario_bruto = request.form['salario_bruto']
        button = request.form['submit-button']

        if not sx or sx.strip() == "":
            return render_template('calculadora.html', error_sexo='Por favor, escolha um dos sexos para dar continuidade', sx='3', slbr=salario_bruto)

        # Verificações para o campo salario_bruto
        if not salario_bruto or salario_bruto.strip() == "":  # Verifica se o campo está vazio
            error_salario = 'Digite um número inteiro maior ou igual a 0.'
            return render_template('calculadora.html', error_salario=error_salario, sx=sx, slbr=salario_bruto)

        try:
            # Tenta converter o salário bruto para float, permitindo valores decimais
            slbr = int(salario_bruto)
            if slbr < 0:
                raise ValueError('O valor deve ser maior ou igual a 0.')
        except ValueError:
            error_salario = 'Digite um número inteiro maior ou igual a 0.'
            return render_template('calculadora.html', error_salario=error_salario,
                                   sx=sx, slbr=salario_bruto)

        if slbr < 0:  # Verifica se o número é negativo
            error_salario = 'Digite um número inteiro maior ou igual a 1.'
            return render_template('calculadora.html', error_salario=error_salario, sx=sx, slbr=slbr)

        if n_clicks3 >= 0:
            # Verifica se o arquivo CNIS.pdf existe no caminho absoluto
            if cnis_buffer.getbuffer().nbytes == 0:
                error = 'Para Calcular Benefício ou Gerar PDF, selecione o seu arquivo de CNIS no formato PDF clicando no botão ‘Choose File’'
                return render_template('calculadora.html', error=error, sx=sx, slbr=slbr)

            if verifica_cnis(cnis_buffer) != 3:
                error = 'O CNIS carregado não está correto. Verifique o arquivo PDF e carregue novamente...!'
                return render_template('calculadora.html', error=error, sx=sx, slbr=slbr)

            if sx is None:
                error = 'Preencher sexo e clique novamente em "Calcular Benefício INSS" e aguarde...!'
                return render_template('calculadora.html', error=error, sx=sx, slbr=slbr)

            pdf, atntv_html = criar_relat_pdf(sx, slbr, cnis_buffer)

            if button == '2':
                # Se for para baixar o PDF, retorna o arquivo
                return send_file(pdf, as_attachment=True, download_name='RelatInss.pdf')
                        
            # Passa a tabela HTML para o template `calculadora.html`
            return render_template('calculadora.html', atntv=atntv_html, pdf=pdf, sx=sx, slbr=slbr)

    except Exception as e:
        app.logger.error(f"Error occurred: {str(e)}")
        error = 'Ocorreu um erro ao tentar gerar seu PDF, por favor, verifique seu CNIS.'
        return render_template('calculadora.html', error=error, sx=sx, slbr=slbr)


def send_email(name, email, password):
    msg = Message('Seus Dados de Acesso', recipients=[email])
    msg.html = f'''
    <html>
    <body>
        <p>Olá <strong>{name}</strong>,</p>
        
        <p>Obrigado por sua compra! Aqui estão seus dados de acesso:</p>
        <p><strong>Email:</strong> {email}<br>
        <strong>Senha:</strong> {password}</p>

        <p>Por favor, faça login no sistema e altere sua senha no primeiro acesso.</p>

        <!-- Links para a plataforma -->
        <p>Acesse a plataforma:</p>
        <p><a href="https://app.guiarendaprevidencia.com.br/login">Login: https://app.guiarendaprevidencia.com.br/login</a></p>
        <p><a href="https://app.guiarendaprevidencia.com.br/forgotPassword">Refazer a Senha: https://app.guiarendaprevidencia.com.br/forgotPassword</a></p>

        <p>Atenciosamente,<br>
        <strong>Sua Equipe</strong></p>
    </body>
    </html>
    '''
    mail.send(msg)

# Função de registro para o webhook
def register_via_webhook(name, email, password):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    user = User.query.filter_by(email=email).first()

    if user:
        return {"status": "erro", "message": "Usuário já registrado"}

    new_user = User(name=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    send_email(name, email, password)

    return {"status": "sucesso", "message": "Usuário registrado e email enviado"}

# Rota do webhook que registra e envia o email
@app.route('/compra-realizada', methods=['POST'])
def webhook():
    data = request.json
    
    # Extraindo nome e email do cliente
    customer_name = data.get('Customer', {}).get('full_name')
    customer_email = data.get('Customer', {}).get('email')

    # Gerando uma senha aleatória
    password = 'pwdXhy'

    # Registrando o usuário e enviando o email
    response = register_via_webhook(customer_name, customer_email, password)
    
    return jsonify(response), 200

@app.route('/cadastro_empresa', methods=['POST'])
def cadastroEmpresa():
    carregar_dados_excel()

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    codigo = request.form['codigo']

    empresa = Empresa.query.filter_by(login=codigo).first()

    dias_restantes = verificar_acesso_empresa(empresa)

    print(dias_restantes)

    if dias_restantes < 0:
        error = f"Acesso expirado, prazo de utilização contratado finalizado."
        return render_template('auth/empresaCadastro.html', error=error)

    user = User.query.filter_by(email=email).first()

    if (user):
        error = f"O usuário {email} já está cadastrado"
        return render_template('auth/empresaCadastro.html', error=error)

    if not empresa:
        error = 'Empresa não encontrada!'
        return render_template('auth/empresaCadastro.html', error=error)

    if empresa.qtd_func_rest <= 0:
        error_empresa = 'O limite de acessos foi atingido!'
        return render_template('auth/empresaCadastro.html', error_empresa=error_empresa)

    hashed_password = generate_password_hash(password)

    novo_usuario = User(name=name, email=email, password=hashed_password, empresa_id = empresa.id)
    db.session.add(novo_usuario)

    empresa.qtd_func_rest -= 1
    db.session.commit()

    registrar_usuario_excel(name, email, codigo)

    return redirect(url_for('login'))

from sqlalchemy.exc import IntegrityError

@app.route('/panel/login', methods=['GET', 'POST'])
def panelLogin():
    token = request.cookies.get('auth-token')

    if token:
        return render_template('calculadora.html')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = UserAdm.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            token = jwt.encode({
                    'user_id': user.id,
            }, app.config['SECRET_KEY'], algorithm='HS256')
            response = jsonify({'token': token, 'message': 'Login bem-sucedido!'})
            response.set_cookie('auth-token', token, httponly=True)
            return response, 200 

        return jsonify({'message': 'Credenciais inválidas.'}), 401

    return render_template('panel/LoginPanel.html')

@app.route('/panel/register', methods=['POST'])
def registerPanel():
    data = request.json

    email = data.get('email')
    password = data.get('password')

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    user = UserAdm.query.filter_by(email=email).first()

    if (user):
        return {"status": "erro", "message": "Usuário já registrado"}
    
    new_user = UserAdm(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return {"status": "success", "message": "Usuário registrado com sucesso"}

@panel_token_required
@app.route('/panel/dashboard')
def get_users():
    # Consulta para obter usuários que possuem empresa associada
    users_with_empresa = db.session.query(User, Empresa)\
        .join(Empresa, User.empresa_id == Empresa.id)\
        .all()
    
    # Renderiza a página HTML passando a lista de usuários e suas empresas
    return render_template('panel/HomePanel.html', users_with_empresa=users_with_empresa)

@panel_token_required
@app.route('/panel/export_excel')
def export_excel():
    
    users_with_empresa = db.session.query(User, Empresa).join(Empresa).all()

    data = []
    for user, empresa in users_with_empresa:
        data.append({
            'ID': user.id,
            'Nome de Usuário': user.name,
            'Email': user.email,
            'Empresa': empresa.login,
            'Nota': empresa.nota
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Usuários')

    output.seek(0)

    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='empregados.xlsx')

@app.route('/panel/users/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Buscar o usuário pelo ID
    user = User.query.get_or_404(user_id)

    try:
        # Excluir o usuário do banco de dados
        db.session.delete(user)
        db.session.commit()

        # Exibir uma mensagem de sucesso
        flash(f'Usuário {user.name} foi excluído com sucesso!', 'success')
    except Exception as e:
        # Em caso de erro, fazer rollback e exibir uma mensagem de erro
        db.session.rollback()
        flash(f'Ocorreu um erro ao tentar excluir o usuário: {str(e)}', 'error')

    # Redirecionar de volta à página de usuários (ou outra página desejada)
    return redirect(url_for('get_users'))

def carregar_dados_excel():
    """Lê a planilha e carrega os dados no banco"""
    file_path = "./static/assets/arquivos/empresas.xlsx"

    if not os.path.exists(file_path):
        return

    df = pd.read_excel(file_path)

    for _, row in df.iterrows():
        # Verificar se o login já existe
        empresa_existente = Empresa.query.filter_by(login=row['LOGIN']).first()
        
        if empresa_existente:
            print(f"Empresa com login {row['LOGIN']} já existe, pulando inserção.")
            continue  # Pula para o próximo registro

        empresa = Empresa(
            login=row['LOGIN'],
            qtd_func=row['QTDD FUNC'],
            prazo=row['PRAZO'],
            dt_inicio=row['DT INÍCIO'],
            nota=row['NOTA'],
            qtd_func_rest=row['QTDD FUNC']
        )

        db.session.add(empresa)

    try:
        db.session.commit()
        print("Dados inseridos com sucesso")
    except IntegrityError:
        db.session.rollback()
        print("Erro de integridade: possível duplicação de dados")

def registrar_usuario_excel(nome, email, codigo):
    """Adiciona um novo usuário à planilha empregados.xlsx."""
    if not os.path.exists(EMPREGADOS_FILE):
        df = pd.DataFrame(columns=["Nome", "Email", "Empresa"])
    else:
        df = pd.read_excel(EMPREGADOS_FILE)
    
    novo_registro = pd.DataFrame({"Nome": [nome], "Email": [email], "Empresa": [codigo]})
    df = pd.concat([df, novo_registro], ignore_index=True)
    df.to_excel(EMPREGADOS_FILE, index=False)

def validar_idade_inicial(idade_inicial):
    try:
        idade_inicial = int(idade_inicial)
        if idade_inicial < 15 or idade_inicial > 100:
            return "Digite um número inteiro entre 15 e 100 para a idade inicial"
    except ValueError:
        return "Digite um número inteiro válido para a idade inicial"
    return None

def validar_idade_aposentadoria(idade_aposentadoria, idade_inicial, expec_vida):
    try:
        idade_aposentadoria = int(idade_aposentadoria)
        if idade_aposentadoria < 15 or idade_aposentadoria > 120 or idade_aposentadoria <= idade_inicial:
            return "Digite um número inteiro maior que a idade atual para aposentadoria"
    except ValueError:
        return "Digite um número inteiro válido para a idade de aposentadoria"
    return None

def validar_expectativa(expec_vida, idade_aposentadoria):
    try:
        expec_vida = int(expec_vida)
        if expec_vida < 15 or expec_vida > 150 or expec_vida <= idade_aposentadoria:
            return "Digite um número inteiro maior que a idade de aposentadoria para a expectativa de vida"
    except ValueError:
        return "Digite um número inteiro válido para a expectativa de vida"
    return None

def validar_reserva_financeira(reserva):
    try:
        reserva = float(reserva)
        if reserva < 0:
            return "Digite um número maior ou igual a zero para a reserva financeira"
    except ValueError:
        return "Digite um número válido para a reserva financeira"
    return None

def validar_taxa_real(taxa_real):
    try:
        taxa_real = float(taxa_real)
        if taxa_real <= 0 or taxa_real >= 21:
            return "Digite um número MAIOR que zero com no máximo uma casa decimal"
        
        # Verifica se há mais de uma casa decimal, mas aceita números inteiros
        if '.' in str(taxa_real) and len(str(taxa_real).split('.')[1]) > 1:
            return "Digite um número MAIOR que zero com no máximo uma casa decimal"
    except ValueError:
        return "Digite um número MAIOR que zero com no máximo uma casa decimal"
    
    return None


def verificar_acesso_empresa(empresa):

    data_inicio = datetime.strptime(empresa.dt_inicio, "%Y-%m-%d %H:%M:%S")

    print(data_inicio)

    data_expiracao = data_inicio + timedelta(days=empresa.prazo)

    print(data_expiracao)

    dias_restantes = (data_expiracao - datetime.now()).days

    print(dias_restantes)

    return dias_restantes


def validar_beneficio_inss(inss):
    try:
        inss = float(inss)
        if inss < 0:
            return "Digite um número maior ou igual a zero para o benefício esperado do INSS"
    except ValueError:
        return "Digite um número válido para o benefício esperado do INSS"
    return None

def validar_poupanca_mensal(poupanca):
    try:
        poupanca = float(poupanca)
        if poupanca < 0:
            return "Digite um número maior ou igual a zero para a poupança mensal"
    except ValueError:
        return "Digite um número válido para a poupança mensal"
    return None



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        #carregar_dados_excel()
    app.run(debug=True)
