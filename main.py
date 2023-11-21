from flask import Flask, request, render_template
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from io import BytesIO
import base64
from datetime import timedelta


app = Flask(__name__)
@app.route("/")
def homepage():
    return render_template("index.html")
@app.route("/processar", methods=["POST"])
def processar_formulario():


    # Conduza o cálculo da previsão, semelhante ao exemplo anterior
    data_frame = request.form['acao']
    dados = pd.read_csv(data_frame + '.csv')

    # Converter a coluna de data para o formato datetime
    dados['Date'] = pd.to_datetime(dados['Date'])

    # Definir a data como índice do DataFrame
    dados.set_index('Date', inplace=True)

    # Dividir os dados em variáveis de entrada (X) e variável de saída (y)
    X = dados[['Open', 'High', 'Low']]  # Seleciona as colunas de entrada
    y = dados['Close']  # Saída

    # Inicializar o modelo de Regressão Linear
    modelo = LinearRegression()

    # Treinar o modelo com todos os dados disponíveis
    modelo.fit(X, y)

    # Prever os próximos 6 meses a partir da última data no conjunto de dados
    data_final = dados.index[-1]  # Última data no conjunto de dados
    data_predicao = pd.date_range(start=data_final, periods=6, freq='M')  # Gera datas para os próximos 6 meses

    # Cria um DataFrame vazio para armazenar as previsões diárias
    previsoes_diarias = pd.DataFrame(columns=dados.columns)
    # Faz previsões diárias para cada dia de cada mês dentro dos próximos 6 meses
    for data in data_predicao:
        # Gera um intervalo de datas para o mês atual
        data_inicio = data.replace(day=1)  # Primeiro dia do mês
        data_fim = data + pd.offsets.MonthEnd()  # Último dia do mês
        datas_mes = pd.date_range(start=data_inicio, end=data_fim, freq='D')  # Gera datas para todos os dias do mês

        # Cria um DataFrame com as features de cada dia do mês atual para fazer as previsões
        features_mes = [[data.toordinal(), data.toordinal(), data.toordinal()] for data in datas_mes]
        previsao_atual = modelo.predict(features_mes)  # Faz as previsões para todos os dias

        # Cria um DataFrame temporário para armazenar as previsões atuais do mês
        df_previsao_atual = pd.DataFrame([[None] * len(dados.columns)] * len(datas_mes),
                                         columns=dados.columns)
        df_previsao_atual['Close'] = previsao_atual  # Ajusta os valores de Close com as previsões

        # Adiciona as previsões atuais ao DataFrame de previsões diárias
        previsoes_diarias = pd.concat([previsoes_diarias, df_previsao_atual], ignore_index=True)

    # Define o índice das previsões diárias como todas as datas dos próximos 6 meses
    previsoes_diarias.index = pd.date_range(start=data_final + timedelta(days=1), periods=len(previsoes_diarias),
                                            freq='D')

    # Calcular a média dos valores diários para cada mês
    previsoes_diarias['Month'] = previsoes_diarias.index.to_period('M')  # Criar uma coluna de mês

    # Obter os meses únicos presentes nos dados
    meses_unicos = previsoes_diarias['Month'].unique()[:6]  # Pegar apenas os próximos 6 meses
    if 'AAPL' in data_frame:
        nome_empresa = 'Apple'
    elif 'AMZN' in data_frame:
        nome_empresa = 'Amazon'
    elif 'NFLX' in data_frame:
        nome_empresa = 'Netflix'

    # Calcular a média dos valores diários para cada mês
    previsoes_diarias['Month'] = previsoes_diarias.index.to_period('M')  # Criar uma coluna de mês
    media_mensal = previsoes_diarias.groupby('Month').mean()  # Calcular a média mensal

        # Lista para armazenar os gráficos como bytes
    graficos_bytes = []

    # Adicione cada gráfico à lista 'graficos_bytes'
    for mes in meses_unicos:
        dados_mes = previsoes_diarias[previsoes_diarias['Month'] == mes]

        plt.figure(figsize=(8, 4))
        plt.plot(dados_mes.index, dados_mes['Close'], marker='o', linestyle='-', label=f'Valores de {mes}',
                 color='blue')

        plt.title(f'Evolução dos Valores das Ações da {nome_empresa} - {mes}')
        plt.xlabel('Data')
        plt.ylabel('Valor de Fechamento')
        plt.legend()

        # Salva a figura em formato de bytes
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)
        img_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')

        # Adiciona o gráfico em bytes à lista
        graficos_bytes.append(img_b64)
        plt.close()

    # Plotar a linha contínua entre os meses (média mensal)
    plt.figure(figsize=(10, 6))
    plt.plot(media_mensal.index.to_timestamp(), media_mensal['Close'], marker='o', linestyle='-',
             label='Tendência Mensal',
             color='red')

    plt.title(f'Tendência de Valores das Ações da {nome_empresa} ')
    plt.xlabel('Data')
    plt.ylabel('Valor de Fechamento')
    plt.legend()
    # plt.show()
    # Salva a figura em formato de bytes
    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    img_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')

    # Adiciona o gráfico em bytes à lista
    graficos_bytes.append(img_b64)
    plt.close()

    return render_template('resultado.html', graficos_bytes=graficos_bytes)

if __name__ == '__main__':
    app.run(debug=True)


