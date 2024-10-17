

#CRIAR PAGINA WEB COM DASH QUE GERA RELATORIO INSS E SIMULACAO RENDA

def criar_relat_pdf(SX,SLBRT):
    #RESTO DO CODIGO...
    #A FUNCAO USA OS ARQUVIVOS ABAIXO EM CADA PROCESSAMENTO
    path = r'F:\arquivos\series.xlsx'
    pdf_path = r'F:\arquivos\CNIS.PDF'
    pdf_path = r'F:\arquivos\mysiglas.PDF'
    image_path = r'F:\arquivos\logo_GdR.png'
    pdf_path =r'F:\arquivos\\EXEMPLO.pdf'
    
    #A FUNCAO PRODUZ OS ARQUVIVO ABAIXO EM CADA PROCESSAMENTO
    pdf_path = r'F:\PYTHON T1\CNIS\vinculos.PDF'
    pdf_path = r'F:\PYTHON T1\CNIS\filiado.PDF'
    pdf_path = r'F:\PYTHON T1\CNIS\indicadores.PDF'
    pdf_path = r'F:\PYTHON T1\CNIS\RelatInss.PDF'
    
    #A FUNCAO USA ESTA FUNCÕES/BIBLIOTECAS NO PROCESSAMENTO
    import re
    from datetime import datetime
    import pdfplumber
    import re
    import pandas as pd
    import pandas as pd
    from datetime import datetime, timedelta
    import locale
    from datetime import datetime
    import pandas as pd
    from datetime import datetime, timedelta
    import pandas as pd
    from datetime import datetime, timedelta
    import pandas as pd
    from datetime import datetime, timedelta
    import pandas as pd
    from datetime import datetime, timedelta
    import pandas as pd
    from datetime import datetime, timedelta
    import pandas as pd
    import re
    import pdfplumber
    import pandas as pd
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus.flowables import Flowable
    import pandas as pd
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus.flowables import Flowable
    import pdfplumber
    import re
    import pandas as pd
    import pandas as pd
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus.flowables import Flowable
    import PyPDF2
    from datetime import datetime
    import os
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import gray, black,white, orangered  # Cor para a linha
    import io #A FUNCAO RETORNA retornA ESTE tabela/dataframe com 5colunas e ate 5linhas



def verifica_cnis():
    #RESTO DO CODIGO...
    
    #A FUNCAO USA ESTAS BIBLIOTECAS
    import pdfplumber
    import re
    
    #A FUNCAO USA ESTE ARQUIVO
    pdf_path = r'F:\PYTHON T1\CNIS\CNIS.PDF'
     #A FUNCAO RETORNA UM VALOR NUMERICO INTEIRO


#GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG

#As duas funcoes de criar_grafico  USAM A BIBLIOTECAS ABAIXO

import numpy as np
import pandas as pd
from scipy.optimize import fminbound
import matplotlib.pyplot as plt
from datetime import datetime

# Função para criar o gráfico renda desejada
def criar_grafico(idade_inicial, idade_aposentadoria, expec_vida, reserva,ret_invest_anual,inss,renda_desejada):
    #RESTO DO CODIGO...
    
    #A FUNCAO PRODUZ UM PRODUZ OS ARQUIVOS ABAIXO
    png_file_path = fr'F:\PYTHON T1\CNIS\RNDesejada.png'
    pdf_file_path = fr'F:\PYTHON T1\CNIS\RND.pdf'

    return png_file_path #A FUNCAO RETORNA O CAMINHO DO ARQUIVO PNG

#funcao cria grafico renda possivel
def criar_grafico2(idade_inicial, idade_aposentadoria, expec_vida, reserva,ret_invest_anual,inss,poupanca_possivel):
    #RESTO DO CODIBO...
    
    #A FUNCAO PRODUZ UM PRODUZ OS ARQUIVOS ABAIXO
    png_file_path = fr'F:\PYTHON T1\CNIS\RNDPossivel.png'
    pdf_file_path = fr'F:\PYTHON T1\CNIS\RND.pdf'

    return png_file_path #A FUNCAO RETORNA O CAMINHO DO ARQUIVO PNG


#DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD


#DASH

#grafico com botoes de idade e esc0lha de porta automatica
#acrescentando reserva
#acrescentando taxa investimento
#acresc inss
#rendda desejada
#renda possivel
#salario bruto
#abre pdf inss
#abre pdf grafico rendas
#abre caixa para uploud de pdf
#verifica pdf do cnis
#abre arquivo pdf exemplo

import os
import base64
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
from flask import send_file
from werkzeug.utils import secure_filename

# Supondo que criar_grafico, criar_grafico2 e criar_relat_pdf estejam definidos acima

# Inicializar o aplicativo Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout do aplicativo
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("PLANEJE RENDA FUTURA: INSS, Desejada&Possível"), className="mb-2")
    ]),
    dbc.Row([
        dbc.Col(html.H6(children='Planeje&Calcule sua Renda Futura em 2 Etapas'), className="mb-0")
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='Em duas etapas descubra sua Renda Futura resultado da soma do seu esforço \
        de poupanca E do seu Benefício de Aposentadoria !',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '2px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='Na primeira etapa verifique o valor do Beneficio de Aposentadoria com as contribuições realizadas ao INSS de forma simples e rápida ! Acesse tambem relatório completo sobre sua situação previdenciária !',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '2px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='Na segunda etapa verifique qual Renda Futura é possível E o esforço de poupança a realizar! Verifique também como o Beneficio Aposentadoria auxilia a chegar à Renda Futura E como impacta facilitando no esforço de poupança !',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '10px'}))
    ]),
    html.Div(style={'borderBottom': '5px solid orangered', 'marginBottom': '10px'}),  #linha orangered
    dbc.Row([
        dbc.Col(html.P(children='1 - CALCULE RENDA de APOSENTADORIA pelo INSS'),style={'font-size': '20px','font-weight': 'bold'}, className="mb-0")
    ]),
    html.Div(style={'borderBottom': '5px solid orangered', 'marginBottom': '10px'}),  #linha orangered
    dbc.Row([
        dbc.Col(html.P(
        children='DESCUBRA NESTA ETAPA o valor de seu Benefício de Aposentadoria do INSS em diferentes alternativas !',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='Calculo pela EC103/19 para trabalhador urbano no RGPS em 5 principais regras: Idade, 50%, 100%, Pontos, Progressiva',
        style={'font-size': '14px', 'margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='- Carregue o arquivo CNIS no formato PDF para o calculo clicando abaixo no botão "Clique&Selecione Arquivo CNIS"',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='- Arquivo CNIS é obtido no aplicativo "Meu INSS" ou no site www.meu.inss.gov.br',
        style={'font-size': '14px', 'margin-top': '0px','margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='- Indique o Salario Bruto que será referência para simular o Benefício do INSS',
        style={'font-size': '14px', 'margin-top': '0px','margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(children=['Clique ', 
            html.A('AQUI', href='/download_example_pdf', target='_blank'), 
            ' e veja exemplo completo do "Relatório de Análise do CNIS" que obtem ao "Calcular Benefício"'],
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '10px'}))
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label('Sexo:', style={'font-weight': 'bold', 'margin-right': '10px'}),
                dcc.Dropdown(
                    id='id_sx',
                    options=[
                        {'label': 'FEM', 'value': 0},
                        {'label': 'MASC', 'value': 1}
                    ],
                    placeholder='Selecione o sexo',
                    style={'width': '100px', 'margin-right': '20px'}
                ),
                html.Label('Salário Bruto Atual (R$):', style={'font-weight': 'bold', 'margin-right': '10px'}),
                dcc.Input(id='id_slbr', type='number', min=0,value=0, step=1, style={'width': '100px', 'margin-right': '20px'}),
                html.Button('Calcular Beneficio INSS', id='submit-button3', n_clicks=0, style={'width': '200px'})
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div(id='error-message3', style={'color': 'red', 'margin-top': '10px'}),
            html.Div(id='relatorio-output', style={'margin-top': '10px'})
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            # Novo componente de upload de arquivo
            dcc.Upload(
                id='upload-pdf',
                children=html.Div(['Clique&Selecione Arquivo CNIS']),
                style={
                    'width': '35%',
                    'height': '25px',
                    'lineHeight': '20px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'font-weight': 'bold',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px auto',
                    'backgroundColor': 'lightgray'
                },
                multiple=False
            ),
            html.Div(id='upload-output')
        ], width=12)
    ]),
    html.Div(style={'borderBottom': '5px solid orangered', 'marginBottom': '10px'}), 
    dbc.Row([
        dbc.Col(html.P(children='2 - CALCULE RENDA DESEJADA&POSSÍVEL FUTURA'),style={'font-size': '20px','font-weight': 'bold'}, className="mb-0")
    ]),
    html.Div(style={'borderBottom': '5px solid orangered', 'marginBottom': '10px'}),  
    dbc.Row([
        dbc.Col(html.P(
        children='EXERCITE & SIMULE NESTA ETAPA Rendas Futuras para diferentes cenários, situações, condições alterando os campos abaixo !',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='- Informe a Renda Desejada mensal na aposentadoria e veja a Poupança Necessária HOJE',
        style={'font-size': '14px', 'margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='- Informe sua Poupança possível mensal HOJE e veja a Renda Possível mensal na aposentadoria',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children=['- Informe seu Benefício do INSS',html.B(' (Etapa 1) '),'e veja IMPACTO no esforço da poupança mensal HOJE e obtenção da Renda Futura !'],
        style={'font-size': '14px', 'margin-top': '0px','margin-bottom': '0px'}))
    ]),
    dbc.Row([
        dbc.Col(html.P(
        children='- Informe a taxa real (descontada inflação) ano de juros que remunera sua poupança e reserva financeira',
        style={'font-size': '14px', 'margin-top': '0px', 'margin-bottom': '10px'}))
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Idade Atual:', style={'font-weight': 'bold'}),
            dcc.Input(id='id_ini', type='number', min=15, max=100, value=25, step=1, style={'width': '50px'})
        ], width=3),
        dbc.Col([
            html.Label('Idade Aposentadoria:', style={'font-weight': 'bold'}),
            dcc.Input(id='id_apos', type='number', min=15, max=120, value=65, step=1, style={'width': '50px'})
        ], width=4),
        dbc.Col([
            html.Label('Expectativa de Vida:', style={'font-weight': 'bold'}),
            dcc.Input(id='id_exp', type='number', min=15, max=150, value=85, step=1, style={'width': '50px'})
        ], width=4),
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Reserva Financeira Atual (R$):', style={'font-weight': 'bold'}),
            dcc.Input(id='id_reser', type='number', min=0, value=1000, step=1, style={'width': '85px'})
        ], width=6),
        dbc.Col([
            html.Label('Taxa real ano (%):', style={'font-weight': 'bold'}),
            dcc.Input(id='id_tx', type='number', min=0.1, value=4, step=0.1, style={'width': '50px'})
        ], width=4),
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Benefício Esperado INSS (R$):', style={'font-weight': 'bold'}),
            dcc.Input(id='id_inss', type='number', min=0, value=0, step=1, style={'width': '70px', 'margin-top': '5px'})
        ], width=4.5),
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label('Renda Mensal DESEJADA (R$):', style={'font-weight': 'bold', 'margin-right': '0px'}),
                dcc.Input(id='id_dese', type='number', min=0, value=1000, step=1, style={'width': '65px', 'margin-right': '30px', 'margin-top': '5px'}),
                html.Button('Condição p/ Renda Desejada', id='submit-button', n_clicks=0, style={'width': '250px', 'margin-top': '5px'})
            ], style={'display': 'flex', 'align-items': 'center'}),
        ], width=9),
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label('Poupança Mensal POSSÍVEL (R$):', style={'font-weight': 'bold', 'margin-right': '5px'}),
                dcc.Input(id='id_poss', type='number', min=0, value=100, step=1, style={'width': '65px', 'margin-right': '5px', 'margin-top': '5px'}),
                html.Button('Condição p/ Renda Possível', id='submit-button2', n_clicks=0, style={'width': '250px', 'margin-top': '5px'})
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div(id='error-message2', style={'color': 'red', 'margin-top': '5px'})
        ], width=9),
    ]),
    dbc.Row([
        dbc.Col([
            # Div para imagem e link
            html.Div([
                html.Img(id='grafico-img', style={'width': '100%', 'margin-top': '20px'}),
                # Novo link abaixo da imagem
                #html.A('Abrir Resultado da Simulação', href='/download_graph_pdf', target="_blank", style={'display': 'block', 'margin-top': '10px'})
                html.A('Clique AQUI para abrir Gráfico acima no formado pdf.', id='pdf-link', href='/download_graph_pdf', target="_blank", style={'display': 'none', 'margin-top': '10px'})
            ])
        ])
    ]),
], fluid=True)
# Callback para atualizar a imagem do gráfico e validar os campos
@app.callback(
    [Output('grafico-img', 'src'), Output('pdf-link', 'style'), Output('error-message2', 'children')],
    [Input('submit-button', 'n_clicks'), Input('submit-button2', 'n_clicks')],
    [State('id_ini', 'value'), State('id_apos', 'value'), State('id_exp', 'value'), State('id_reser', 'value'),
     State('id_tx', 'value'), State('id_inss', 'value'), State('id_dese', 'value'), State('id_poss', 'value')]
)

def update_output(n_clicks1, n_clicks2, idade_inicial, idade_aposentadoria, expec_vida, reserva, rentabilidade, inss, renda_desejada, poupanca_possivel):
    ctx = dash.callback_context
    if not ctx.triggered:
        return None, {'display': 'none'}, ''
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if idade_inicial is None:
        return None, {'display': 'none'}, 'Idade Atual mínima permitida é 15 anos E sem casas decimais (exemplos: 19 ou 25 ou 49 etc...)! Digite outro valor...!'
    if idade_aposentadoria is None or idade_aposentadoria <= idade_inicial:
        return None,{'display': 'none'}, 'Digite um valor maior que a Idade Atual para a Idade Aposentadoria E sem casas decimais (exemplos: 69 ou 75 ou 89 etc...).'
    if expec_vida is None or expec_vida <= idade_inicial or expec_vida <= idade_aposentadoria:
        return None,{'display': 'none'}, 'Digite um valor maior que da Idade Atual e da Idade de Aposentadoria para a Expectativa de Vida E sem casas decimais (exemplos: 99 ou 95 ou 79 etc...).'
    if reserva is None or reserva < 0:
        return None,{'display': 'none'}, 'Digite um valor inteiro maior ou igual a zero E sem casas decimais (exemplos: 1000 ou 2500 ou 4987 etc...) para Reserva Financeira.'
    if rentabilidade is None or rentabilidade <= 0:
        return None,{'display': 'none'}, 'Digite um valor maior que zero E com no maximo uma casa decimal (exemplos: 4.9 ou 3.2 etc...)para a Taxa Real.'
    if inss is None or inss < 0:
        return None,{'display': 'none'}, 'Digite um valor maior ou igual a zero E sem casas decimais (exemplos: 1000 ou 2500 ou 4987 etc...) para Benefício INSS.'
    if renda_desejada is None or renda_desejada < 0:
        return None,{'display': 'none'}, 'Digite um valor maior ou igual a zero E sem casas decimais (exemplos: 1000 ou 2500 ou 4987 etc...) para Renda Mensal DESEJADA.'
    if poupanca_possivel is None or poupanca_possivel < 0:
        return None,{'display': 'none'}, 'Digite um valor maior ou igual a zero E sem casas decimais (exemplos: 1000 ou 2500 ou 4987 etc...) para Poupança Mensal POSSÍVEL.'

    rentabilidade_anual = rentabilidade / 100  # Ajuste da rentabilidade para a função

    if button_id == 'submit-button':
        png_file_path = criar_grafico(idade_inicial, idade_aposentadoria, expec_vida, reserva, rentabilidade_anual, inss, renda_desejada)
    elif button_id == 'submit-button2':
        png_file_path = criar_grafico2(idade_inicial, idade_aposentadoria, expec_vida, reserva, rentabilidade_anual, inss, poupanca_possivel)

    # Converter o caminho da imagem para um formato que o Dash possa exibir
    encoded_image = base64.b64encode(open(png_file_path, 'rb').read()).decode('utf-8')
    src_data = 'data:image/png;base64,' + encoded_image

    return src_data, {'display': 'block', 'margin-top': '10px'}, ''

# abre o PDF exemplo usando o Flask
import flask
@app.server.route('/download_example_pdf')
def download_example_pdf():
    return flask.send_file('F:\\PYTHON T1\\CNIS\\EXEMPLO.pdf', as_attachment=False)

# Servir o PDF usando o Flask
@app.server.route('/download_pdf')
def download_pdf():
    pdf_path = r'F:\PYTHON T1\CNIS\RelatInss.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=False)  # Serve o PDF sem forçar download
    else:
        return "Arquivo PDF não encontrado."

# Nova rota para servir o PDF do gráfico  
@app.server.route('/download_graph_pdf')
def download_graph_pdf():
    pdf_path = r'F:\PYTHON T1\CNIS\RND.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=False)  # Serve o PDF sem forçar download
    else:
        return "Arquivo PDF não encontrado."
# Callback para gerar relatório PDF com os dados do usuário e exibir o link para abri-lo
@app.callback(
    [Output('relatorio-output', 'children'), Output('error-message3', 'children')],
    [Input('submit-button3', 'n_clicks')],
    [State('id_sx', 'value'), State('id_slbr', 'value')]
)

def gerar_relatorio(n_clicks3, sx, slbr):
    cnis_path = r'F:\PYTHON T1\CNIS\CNIS.pdf'
    if n_clicks3 > 0:
        # Verifica se o arquivo CNIS.pdf existe no caminho especificado
        if not os.path.exists(cnis_path):
            return '', 'Para o Calculo do Benefício Selecione seu arquivo de CNIS no formato PDF clicando em "Clique&Selecione Arquivo CNIS" abaixo !'
        if verifica_cnis() != 3:
            return '', 'O CNIS carregado não está correto. Verifique o arquivo PDF e carregue novamente...!'
        if sx is None:
            return None, 'Preencher sexo e clique novamente em "Calcular Beneficio INSS" e aguarde...!'
        if slbr is None or slbr < 0:
            return None, 'Preencha Salário Bruto um valor inteiro, maior ou igual a zero E sem casas decimais (exemplos: 1000 ou 2500 ou 4987 etc...)! clique novamente em "Calculo Beneficio INSS" E aguarde...!'
        #loading_message = 'Aguarde, cálculo sendo executado!'
        
        ATNTV = criar_relat_pdf(sx, slbr)
        df = pd.DataFrame(ATNTV)
        
        table = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': 'white', 'fontWeight': 'bold'}
        )
        
        # Adicionando o link diretamente após a tabela para abrir o PDF via servidor
        link = html.A('Clique aqui para visualizar "Relatório Completo de Análise do CNIS" no formato pdf.', href='/download_pdf', target="_blank", style={'display': 'block', 'margin-top': '10px'})
        
        return html.Div([
            dcc.Markdown("### Alternativas de Aposentadoria com Informações do CNIS"),
            table,
            link
        ]), ''
    # Garantir que a função sempre retorne uma tupla
    return '', ''
# Callback para salvar o PDF e gerar a saída desejada
@app.callback(
    Output('upload-output', 'children'),
    [Input('upload-pdf', 'contents')],
    [State('upload-pdf', 'filename')]
)
def save_uploaded_file(contents, filename):
    if contents is not None:
        # Verifica se o arquivo é um PDF
        if not filename.lower().endswith('.pdf'):
            return html.Div('O arquivo CNIS tem que ser do tipo PDF, verifique e carregue novamente...!',
                            style={'color': 'red', 'font-weight': 'bold'})
            #return 'O arquivo selecionado tem que ser do tipo PDF.'

        # Decodifica o conteúdo do arquivo
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Salva o arquivo no caminho especificado
        filepath = os.path.join('F:\\PYTHON T1\\CNIS', 'CNIS.pdf')
        with open(filepath, 'wb') as f:
            f.write(decoded)

        #return f'Arquivo {filename} carregado e salvo em {filepath}'
        return f'Arquivo "{filename}" carregado! Continue "Calcular Benefício INSS"...!'
    
    return None


#ABRE A APLICACAO DASH DIRETAMENTE NO BROWSE
import dash
from dash import html
import webbrowser
from threading import Timer
import socket

# Função para encontrar uma porta disponível
def find_available_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port

# Função para abrir o navegador com a porta correta
def open_browser(port):
    webbrowser.open_new(f"http://127.0.0.1:{port}/")

# Inicia o servidor Dash
if __name__ == '__main__':
    # Encontra uma porta disponível
    port = find_available_port()
    open_browser(port)
    # Executa o servidor Dash com a porta dinâmica
    app.run_server(debug=False, port=port)



