
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

# Pega a API Key da variável de ambiente
api_key = os.getenv("API_KEY")

from google import genai

# Cria o cliente passando a API Key
client = genai.Client(api_key=api_key)

MODEL_ID = "gemini-2.0-flash"

# Agora pode usar o client para chamar o modelo



from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types  # Para criar conteúdos (Content e Part)
from datetime import date
import textwrap # Para formatar melhor a saída de texto 
import requests # Para fazer requisições HTTP
import warnings

warnings.filterwarnings("ignore")



# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
def call_agent(agent: Agent, message_text: str) -> str:
    # Cria um serviço de sessão em memória
    session_service = InMemorySessionService()
    # Cria uma nova sessão (você pode personalizar os IDs conforme necessário)
    session = session_service.create_session(app_name=agent.name, user_id="user1", session_id="session1")
    # Cria um Runner para o agente
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    # Cria o conteúdo da mensagem de entrada
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    # Itera assincronamente pelos eventos retornados durante a execução do agente
    for event in runner.run(user_id="user1", session_id="session1", new_message=content):
        if event.is_final_response():
          for part in event.content.parts:
            if part.text is not None:
              final_response += part.text
              final_response += "\n"
    return final_response

    # Função auxiliar para exibir texto formatado em Markdown no Colab
def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

  ##########################################
# --- Agente 1: Identificador de Produtos --- #
##########################################
def agente_classificador(produto,estado, cidade, bairro):

    classificador = Agent(
        name="agente_classificador",
        model="gemini-2.0-flash",
        instruction="""
        Você é um agente classificador especializado em reciclagem. Sua função é identificar o tipo de produto ou material mencionado pelo usuário e informar se ele é **Reciclável**, **Parcialmente Reciclável** ou **Não Reciclável**.

        ### Classificação:
        - **Reciclável**: O material pode ser reciclado com facilidade pela maioria das cooperativas e centros de reciclagem.
        - **Parcialmente Reciclável**: O item contém partes recicláveis, mas exige separação, processos especiais ou não é reciclado em todas as localidades.
        - **Não Reciclável**: O material não é aceito em programas convencionais de reciclagem ou contém misturas que inviabilizam sua reutilização.

        ### Categorias e Especificações:
        Utilize uma base de conhecimento estruturada em categorias como:
        - **Plástico**: Diferencie tipos como PET (ex: garrafas de refrigerante), PEAD (ex: embalagens de produtos de limpeza), PP, PS, PVC, etc.
        - **Papel**: Especifique se é papelão, papel branco, papel misto, papel plastificado, etc.
        - **Vidro**
        - **Metal**
        - **Orgânico**
        - **Eletrônico**
        - **Perigoso** (ex: pilhas, lâmpadas, remédios)
        - **Compostos** (ex: caixas longa vida, embalagens com camadas mistas de plástico e alumínio)

        ### Materiais Genéricos:
        Caso o item citado seja genérico (ex: "embalagem de salgadinho", "pacote de ovo"), utilize a ferramenta de busca ou base de conhecimento interna para identificar os materiais mais comuns atualmente usados nesse tipo de item e ofereça uma classificação **educada e segura** com base nessa estimativa.

        ### Formato da Resposta:
        1. **Comece sempre com a classificação**: "Reciclável", "Parcialmente Reciclável" ou "Não Reciclável".
        2. **Siga com uma explicação concisa**: uma única frase explicando o motivo, destacando o material predominante e a reciclabilidade do item.

        ### Observações:
        - Nunca invente materiais. Se não encontrar uma correspondência clara, diga:  
          **"Não foi possível identificar o material com precisão. Por favor, descreva melhor o item para uma avaliação adequada."**
        """
,
        description="Agente que busca classificacao de produtos no Google",
        tools=[google_search]
    )

    entrada_do_agente_classificador = f"Produto: {produto} \n Estado: {estado} \n Cidade: {cidade} \n Bairro: {bairro}"

    classificacao = call_agent(classificador, entrada_do_agente_classificador)
    return classificacao

    ##########################################
# --- Agente 2: Identificador de Pontos de Coleta --- #
##########################################
def agente_identificador(produto, estado, cidade, bairro):

    identificador = Agent(
        name="agente_identificador",
        model="gemini-2.0-flash",
        instruction="""
        Você é um agente especializado em fornecer informações sobre pontos de coleta de materiais recicláveis.

        Sua função é localizar, com base no **produto**, **tipo de material** (se identificado pelo Agente 1), **estado**, **cidade** e **bairro** informados pelo usuário, locais próximos que aceitam esse tipo de material para reciclagem.

        ### Estratégia de Busca:
        - Utilize ferramentas de busca online para identificar **cooperativas de reciclagem**, **ecopontos**, **empresas de coleta seletiva** e **pontos de entrega voluntária (PEVs)**.
        - Inclua o **tipo de material** (ex: papelão, PET, vidro, etc.) na busca para obter resultados mais direcionados. Exemplo: "onde reciclar papelão em Uberlândia Alto Umuarama".
        - Priorize resultados que estejam **mais próximos do bairro informado** pelo usuário, sempre que possível.

        ### Resposta Deve Conter:
        1. **Lista numerada dos pontos de coleta encontrados**, com:
          - Nome do local (se disponível).
          - Endereço completo.
        2. **Informações adicionais relevantes**, como:
          - Tipos de materiais aceitos.
          - Horários de funcionamento.
          - Telefone de contato ou site (se disponível).
        3. **Caso não encontre pontos específicos** para o tipo de material ou produto na localidade indicada:
          - Informe que não foi possível localizar pontos exatos.
          - Sugira que o usuário:
            - Acesse o site da prefeitura da cidade.
            - Procure associações de catadores locais.
            - Entre em contato com a central de coleta seletiva da região.

        ### Formato da Resposta:
        - Clareza é essencial: use uma **lista numerada** para os locais.
        - Organize os detalhes de cada ponto com **marcadores**.
        - Evite parágrafos longos: foque em informações diretas e legíveis.
        """
 , 

        description="Agente que identifica pontos de coleta no Google a partir do estado, cidade e bairro do usuário",
        tools=[google_search]
    )

    entrada_do_agente_identificador = f"Produto: {produto} \n Estado: {estado} \n Cidade: {cidade} \n Bairro: {bairro}"

    identificacao = call_agent(identificador, entrada_do_agente_identificador)
    return identificacao

    ##########################################
# --- Agente 3: Buscador de Impactos Positivos --- #
##########################################
def agente_buscador(produto):

    buscador = Agent(
        name="agente_buscador",
        model="gemini-2.0-flash",
        instruction="""
          Você é um agente educacional especializado em reciclagem. Sua função é fornecer informações relevantes e educativas sobre o processo de reciclagem do **material predominante** do produto mencionado pelo usuário.

          ### Integração com o Agente 1:
          Sempre que possível, use o tipo de material identificado previamente pelo Agente 1 (ex: PET, PEAD, papelão, vidro) para tornar a resposta mais precisa e direcionada. Caso o material não tenha sido identificado, baseie-se nos materiais mais comuns do item citado (ex: papelão ou plástico no caso de embalagens de ovos).

          ### Sua resposta deve abordar:

          1. **Processo de reciclagem** do material predominante:
            - Descreva de forma simples como o material é coletado, processado e transformado em novos produtos.
            - Use exemplos concretos e adaptados ao tipo de material (ex: "Papelão é triturado e transformado em novas caixas").

          2. **Importância ambiental** da reciclagem desse material:
            - Explique os benefícios diretos da reciclagem, como economia de recursos naturais, redução de poluição e preservação de aterros.

          3. **Dicas específicas de preparação** para reciclagem:
            - Adapte as dicas ao tipo de material:
              - **Papelão**: Desmonte e amasse as caixas, evite molhar.
              - **Plástico**: Enxágue para remover resíduos, remova tampas se possível.
              - **Vidro**: Enxágue e evite quebrar.
              - **Metal**: Lave para evitar contaminação.
            - No caso de **embalagens de ovos**, destaque a separação por tipo: se for de papelão, pode ser reciclada com papel; se for de plástico ou isopor, pode depender da política local.

          4. **Curiosidades ou fatos interessantes**:
            - Compartilhe uma curiosidade sobre o ciclo de vida do material ou dados de impacto positivo da reciclagem (ex: "Reciclar 1 tonelada de papelão economiza cerca de 20 árvores").

          ### Estilo da Resposta:
          - Clareza e simplicidade.
          - Frases curtas e acessíveis.
          - Pode utilizar subtítulos ou marcadores para facilitar a leitura.

          Se não for possível identificar claramente o material, informe isso ao usuário e sugira que ele descreva melhor o item.
          """ ,
        description="Agente que buscará os impactos positivos de reciclagem o produto que o usuário informou",
        tools=[google_search]
    )

    entrada_do_agente_buscador = f"Produto: {produto}"

    buscar = call_agent(buscador, entrada_do_agente_buscador)
    return buscar

    ##########################################
# --- Agente 4: Recompensar o usuário com motivação para reciclagem  --- #
##########################################
def agente_elogiador(buscar, produto , classificacao, identificacao):

    elogiador = Agent(
        name="agente_elogiador",
        model="gemini-2.0-flash",
        instruction="""
          Você é um agente motivacional especializado em reciclagem. Sua função é agradecer, incentivar e informar o usuário de forma acolhedora e positiva por sua atitude sustentável. Sempre que possível, personalize a resposta com base no tipo de material e na localização retornados pelo Agente 1.

            Sua resposta deve conter:

            1. **Agradecimento caloroso e direto**
            - Parabenize o usuário pela reciclagem do produto/material informado (ex: “embalagem de ovo” ou “plástico PET”).
            - Use uma linguagem amigável e humana. Emojis são bem-vindos se usados com leveza.

            2. **Benefícios da reciclagem do material identificado**
            - Destaque como a reciclagem ajuda o planeta e a comunidade.
            - Ex: “O papelão é 100 reciclável e sua reciclagem reduz a derrubada de árvores e o uso de energia.”

            3. **Pontos de coleta/programas locais (se disponíveis)**
            Liste de forma objetiva:
            - Nome do ponto de coleta
            - Endereço
            - Materiais aceitos
            - Benefícios extras (ex: descontos, sorteios, créditos, etc.)

            4. **Caso não existam pontos específicos**
            - Diga isso com empatia.
            - Valorize ainda mais a atitude do usuário, mostrando que sua ação continua importante e impactante para o meio ambiente.

            5. **Mensagem final curta e motivadora**
            - Ex: “Continue assim! Cada atitude como a sua ajuda a construir um futuro mais verde.”

            **Estilo e tom:**
            - Positivo, acolhedor e inspirador.
            - Frases curtas, linguagem clara e direta.
            - Use listas para facilitar a leitura.
            - Emojis podem ser usados moderadamente para tornar a mensagem leve e envolvente (ex: 🌱, ♻️, 💚).

            **Personalização obrigatória sempre que possível:**
            - Tipo do material (ex: papel, plástico, isopor, metal, vidro etc.).
            - Nome do produto (ex: garrafa PET, caixa de ovos).
            - Cidade e bairro do usuário.

            Exemplo de retorno ideal baseado no prompt:

                🎉 Parabéns por reciclar sua embalagem de ovo! Cada atitude como essa faz uma enorme diferença para o planeta 🌍

                ♻️ A reciclagem do papelão ajuda a preservar árvores, economiza água e reduz o volume de resíduos em aterros sanitários.

                📍 Ponto de coleta próximo:
                - Ecoponto Umuarama  
                - Rua Arlindo Teixeira, 1650 – Uberlândia/MG  
                - Aceita: papel, plástico, eletrodomésticos, lâmpadas e mais  
                - Benefícios: educação ambiental e descarte consciente ✅

                🌱 Continue assim! Sua atitude inspira e transforma 🌎💚'


                    """
,

        description="Agente que recompensará o usuário com motivação para reciclagem",
        tools=[google_search]
    )

    entrada_do_agente_elogiador = f"Busca: {buscar} \n Produto: {produto} \n Classificacao {classificacao} \n Identificacao {identificacao} "

    elogiar = call_agent(elogiador, entrada_do_agente_elogiador)
    return elogiar

# print("💚 Que bom que você decidiu reciclar!...")
# produto = input("❓ Por favor, digite o PRODUTO que deseja descartar: ")
# estado = input("📍 Agora, informe o ESTADO onde você está: ")
# cidade = input("🏙️ E a CIDADE: ")
# bairro = input("📌 Para finalizar, qual é o BAIRRO? ")

# if erros:
#     for erro in erros:
#         print(erro)
# else:
#     print(f"Maravilha! Vamos verificar se '{produto}' é reciclável e encontrar o ponto de coleta mais próximo para você.")

#     classificacao = agente_classificador(produto, estado, cidade, bairro)
#     identificacao = agente_identificador(produto, estado, cidade, bairro)
#     buscar = agente_buscador(produto)
#     elogiar = agente_elogiador(buscar, produto, classificacao, identificacao)

#     print("\n--- 📝 Resultado da Pesquisa ---\n")
#     print(elogiar)
#     print("--------------------------------------------------------------")

# print("💚 Que bom que você decidiu reciclar!...")
# produto = input("❓ Por favor, digite o PRODUTO que deseja descartar: ")
# estado = input("📍 Agora, informe o ESTADO onde você está: ")
# cidade = input("🏙️ E a CIDADE: ")
# bairro = input("📌 Para finalizar, qual é o BAIRRO? ")

# if erros:
#     for erro in erros:
#         print(erro)
# else:
#     print(f"Maravilha! Vamos verificar se '{produto}' é reciclável e encontrar o ponto de coleta mais próximo para você.")

#     classificacao = agente_classificador(produto, estado, cidade, bairro)
#     identificacao = agente_identificador(produto, estado, cidade, bairro)
#     buscar = agente_buscador(produto)
#     elogiar = agente_elogiador(buscar, produto, classificacao, identificacao)

#     print("\n--- 📝 Resultado da Pesquisa ---\n")
#     print(elogiar)
#     print("--------------------------------------------------------------")

from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
import os

# Supondo que as funções dos agentes já estejam aqui ou importadas:
# agente_classificador(), agente_identificador(), agente_buscador(), agente_elogiador()

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)  # habilita CORS para permitir chamadas do front-end

@app.route('/reciclagem', methods=['POST'])
def reciclagem():
    data = request.get_json()

@app.route('/', methods=['GET'])
def home():
    return "API do chatbot de reciclagem está no ar!"
    

    produto = data.get('produto')
    estado = data.get('estado')
    cidade = data.get('cidade')
    bairro = data.get('bairro')

    classificacao = agente_classificador(produto, estado, cidade, bairro)
    identificacao = agente_identificador(produto, estado, cidade, bairro)
    buscar = agente_buscador(produto)
    elogiar = agente_elogiador(buscar, produto, classificacao, identificacao)

    return jsonify({
        "classificacao": classificacao,
        "pontos": identificacao,
        "impactos": buscar,
        "mensagem": elogiar
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

