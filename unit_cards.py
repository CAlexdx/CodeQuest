"""
CodeQuest - conteúdo de TEORIA das unidades (cards estilo Duolingo).

Antes de responder as perguntas de uma unidade, o aluno passa por 3 cards curtos.
O conteúdo foi escrito a partir das próprias perguntas de cada unidade, para que
quem ler os cards consiga responder sem "chutar".

Chave: (id_da_trilha, ordem_da_unidade)  ->  mesma ordem do seed_data.py.
Como editar: basta mexer neste arquivo e fazer deploy (não precisa rodar init_db.py).

Campos de cada unidade:
  base   texto curto mostrado no topo ("de onde veio" o conteúdo)
  lab    atalho "Praticar no LAB": sql | python | js | css | bughunt | None
  cards  lista de cards; cada card tem titulo, texto e, opcionalmente,
         topicos (lista), codigo (bloco de código) e dica (destaque amarelo)
"""

# Disciplinas do 1º bimestre usadas como base das perguntas (uma por trilha)
DISCIPLINAS = {
    1: "Modelagem e Desenvolvimento de Banco de Dados",
    2: "Inteligência Artificial",
    3: "Programação Back-End",
    4: "Programação Front-End",
    5: "Programação Mobile",
    6: "Versionamento de Código e Sistemas de Mensageria",
}


def card(titulo, texto, topicos=None, codigo=None, dica=None):
    return {"titulo": titulo, "texto": texto, "topicos": topicos or [], "codigo": codigo or "", "dica": dica or ""}


UNIT_CARDS = {
    # ======================= 1. BANCO DE DADOS =======================
    (1, 1): {
        "lab": "sql",
        "cards": [
            card("O que é o MySQL?",
                 "O MySQL Server é um sistema de gerenciamento de banco de dados (SGBD) relacional e de código aberto. "
                 "Ele guarda os dados em tabelas e é controlado por uma linguagem chamada SQL.",
                 ["SGBD: programa que cria, organiza e protege os dados",
                  "Relacional: os dados ficam em tabelas ligadas entre si",
                  "Código aberto: pode ser usado gratuitamente"]),
            card("Ferramentas e linguagem",
                 "O MySQL Workbench é a ferramenta visual: nele você cria diagramas ER e gerencia seus bancos. "
                 "Para conversar com o banco usamos a linguagem SQL (Structured Query Language).",
                 ["Workbench: diagramas ER e administração do banco",
                  "SQL: a linguagem usada pelo MySQL para fazer consultas"]),
            card("Seu primeiro comando",
                 "O comando SELECT busca dados de uma tabela. O asterisco (*) significa \"todas as colunas\".",
                 codigo="SELECT * FROM users;",
                 dica="Numa lacuna como ___ * FROM users; a palavra que falta é select."),
        ],
    },
    (1, 2): {
        "lab": None,
        "cards": [
            card("Relacionamento 1:N",
                 "No relacionamento um-para-muitos (1:N), um registro da tabela \"Um\" se liga a vários registros da tabela "
                 "\"Muitos\". Já cada registro de \"Muitos\" pertence a apenas um registro da tabela \"Um\".",
                 ["Exemplo clássico: um cliente faz vários pedidos",
                  "Cada pedido tem um único cliente"]),
            card("Chave estrangeira (FK)",
                 "A chave estrangeira é a coluna que referencia a chave primária de outra tabela. "
                 "É ela que implementa a conexão 1:N dentro do banco.",
                 codigo="CREATE TABLE pedidos (\n  id INT PRIMARY KEY,\n  cliente_id INT,\n  FOREIGN KEY (cliente_id) REFERENCES clientes(id)\n);"),
            card("Muitos para muitos (N:N)",
                 "No relacionamento N:N não dá para ligar as tabelas diretamente: criamos uma tabela intermediária que guarda "
                 "as chaves das duas.",
                 ["Exemplo: alunos e disciplinas (um aluno cursa várias disciplinas e vice-versa)",
                  "Na notação Crow's Foot, o símbolo de \"muitos\" é o pé de galinha (três linhas abertas)"]),
        ],
    },
    (1, 3): {
        "lab": None,
        "cards": [
            card("Por que normalizar?",
                 "Normalização é o processo de organizar as tabelas para reduzir a redundância (dados repetidos) e evitar "
                 "anomalias, que são inconsistências ao inserir, atualizar ou apagar dados.",
                 ["Vantagem: minimiza redundâncias e melhora a integridade dos dados"]),
            card("As formas normais",
                 "As formas normais são regras progressivas: 1NF, depois 2NF, depois 3NF. "
                 "Para estar na 3NF, a tabela precisa estar antes na 2NF.",
                 ["1NF: valores atômicos (um valor por célula)",
                  "2NF: sem dependências parciais da chave primária",
                  "3NF: elimina as dependências transitivas"],
                 dica="Pergunta de lacuna? A forma anterior à 3NF se escreve 2NF."),
            card("E o processo inverso?",
                 "A normalização divide tabelas. O caminho contrário se chama desnormalização: juntar tabelas de propósito, "
                 "aceitando alguma redundância para reduzir junções (JOINs) e ganhar velocidade de leitura."),
        ],
    },
    (1, 4): {
        "lab": "sql",
        "cards": [
            card("Os subconjuntos do SQL",
                 "O SQL é dividido em grupos de comandos de acordo com o que eles fazem.",
                 ["DDL (CREATE, DROP): criam e removem a estrutura (tabelas)",
                  "DML (INSERT, UPDATE, DELETE, SELECT): manipulam os dados",
                  "DCL (GRANT, REVOKE): controlam permissões de acesso"]),
            card("Comandos DML no dia a dia",
                 "SELECT recupera dados de uma tabela. INSERT adiciona dados novos, UPDATE modifica dados existentes e DELETE apaga registros.",
                 codigo="INSERT INTO users (username, xp) VALUES ('ana', 0);\nUPDATE users SET xp = 50 WHERE username = 'ana';\nSELECT * FROM users;\nDELETE FROM users WHERE username = 'ana';"),
            card("Criar tabelas e um pouco de história",
                 "CREATE TABLE cria uma nova tabela (é um comando DDL). Em 1970, Edgar F. Codd publicou o artigo que propôs o "
                 "modelo relacional, a base que deu origem ao SQL.",
                 codigo="CREATE TABLE alunos (\n  id INT PRIMARY KEY,\n  nome VARCHAR(50)\n);"),
        ],
    },
    (1, 5): {
        "lab": "sql",
        "cards": [
            card("ACID: a confiança das transações",
                 "Uma transação é um conjunto de operações tratado como uma só. As quatro propriedades ACID garantem que ela seja confiável:",
                 ["Atomicidade: tudo ou nada. Se algo falha, o banco reverte as operações",
                  "Consistência: depois da transação, o banco continua respeitando as suas regras",
                  "Isolamento: transações simultâneas não se atrapalham",
                  "Durabilidade: o que foi confirmado não se perde"]),
            card("Confirmar ou desfazer",
                 "O comando COMMIT confirma permanentemente as alterações de uma transação. O ROLLBACK desfaz tudo o que ainda não foi confirmado.",
                 codigo="BEGIN;\nUPDATE contas SET saldo = saldo - 100 WHERE id = 1;\nUPDATE contas SET saldo = saldo + 100 WHERE id = 2;\nCOMMIT;"),
            card("Índices: rápidos para ler, caros para escrever",
                 "Um índice acelera as consultas na coluna indexada, como o índice de um livro. O custo é que cada INSERT, UPDATE ou "
                 "DELETE também precisa atualizar os índices.",
                 ["Objetivo do índice: acelerar consultas",
                  "Efeito colateral de muitos índices: degradação nas operações de escrita"],
                 codigo="CREATE INDEX idx_users_xp ON users (xp);"),
        ],
    },

    # ======================= 2. INTELIGÊNCIA ARTIFICIAL =======================
    (2, 1): {
        "base": "Semana 1 – Introdução à Inteligência Artificial",
        "lab": None,
        "cards": [
            card("O que é Inteligência Artificial?",
                 "IA é a área da computação que cria sistemas capazes de realizar tarefas cognitivas humanas, como reconhecer padrões, "
                 "entender linguagem e tomar decisões.",
                 ["IA Fraca (ou Estreita): faz bem uma tarefa específica. Todas as IAs atuais são fracas, inclusive o ChatGPT",
                  "IA Forte (ou Geral): ainda hipotética, igualaria o humano em qualquer tarefa"]),
            card("Tipos de IA pelo uso de memória",
                 "As IAs também podem ser classificadas pelo quanto guardam do que já aconteceu.",
                 ["Reativa: responde só ao momento, sem histórico",
                  "Memória limitada: usa dados do passado recente. O ChatGPT é desse tipo",
                  "Teoria da mente e autoconsciente: ainda são teóricas"]),
            card("Discriminativa x generativa",
                 "A IA discriminativa classifica (é spam ou não?). A IA generativa cria dados novos (textos, imagens, músicas).",
                 ["Teste de Turing: avalia se uma máquina exibe comportamento inteligente",
                  "LLM (Large Language Model): modelo de linguagem de grande porte, como o GPT"],
                 dica="A sigla de Large Language Models é LLM."),
        ],
    },
    (2, 2): {
        "base": "Semana 2 – Tipos de IA, Aplicações e Impacto",
        "lab": None,
        "cards": [
            card("IA no seu dia a dia",
                 "O Spotify recomenda músicas de artistas que você nunca ouviu porque analisa e compara padrões de gosto musical entre os usuários. "
                 "Carros autônomos usam dados de viagens anteriores, por isso são IA de memória limitada."),
            card("IA reativa",
                 "Um sistema que apenas filtra e-mails, sem guardar histórico de nada, é uma IA reativa: ela reage só ao que está na sua frente.",
                 dica="Sem histórico = reativa. Com histórico recente = memória limitada."),
            card("Vieses e o papel humano",
                 "Sistemas modernos podem herdar vieses. A principal causa são os dados de treinamento, que refletem preconceitos históricos.",
                 ["Em decisões de alto impacto social, a IA deve servir como ferramenta de apoio, com humanos decidindo"]),
        ],
    },
    (2, 3): {
        "lab": None,
        "cards": [
            card("Ciclos e invernos da IA",
                 "A história da IA tem ciclos de otimismo e \"invernos\". O principal motivo dos invernos foram as expectativas irreais "
                 "contra as limitações técnicas da época, que levaram a cortes de investimento."),
            card("Marcos importantes",
                 "Alguns momentos que você precisa conhecer:",
                 ["1950: Alan Turing propõe o famoso teste de Turing",
                  "1997: o computador Deep Blue vence o campeão mundial de xadrez",
                  "Boom recente: big data, GPUs e deep learning"]),
            card("Deep Learning",
                 "Deep learning (aprendizado profundo) usa redes neurais com muitas camadas e foi o que iniciou o boom moderno da IA.",
                 dica="Para montar o termo, a ordem é: deep learning."),
        ],
    },
    (2, 4): {
        "base": "Semanas 3 a 5 – IA Generativa, Modelos e GANs",
        "lab": None,
        "cards": [
            card("GANs: duas redes em disputa",
                 "GAN significa Redes Adversárias Generativas. Duas redes competem: uma gera imagens e a outra tenta descobrir se são falsas. "
                 "O resultado tem qualidade fotorrealista.",
                 ["Exemplo: o site ThisPersonDoesNotExist usa StyleGAN, cuja arquitetura base é a GAN"]),
            card("VAE e Transformer",
                 "Cada modelo generativo tem seu ponto forte.",
                 ["VAE (autoencoder variacional): controle fino das variações. Ideal para gerar logos com variações controladas",
                  "Transformer: arquitetura focada em atenção, base de modelos de linguagem como o GPT"]),
            card("Redes neurais artificiais",
                 "As Redes Neurais Artificiais tentam imitar o funcionamento dos neurônios humanos: camadas de pequenos nós que ajustam seus pesos durante o treinamento.",
                 dica="Lacuna: imitar o funcionamento dos neurônios humanos."),
        ],
    },
    (2, 5): {
        "base": "Impacto e uso responsável da IA",
        "lab": None,
        "cards": [
            card("Deepfakes e privacidade",
                 "Deepfake é uma mídia manipulada com IA para substituir rostos ou vozes. Isso levanta debates sobre desinformação e privacidade de dados."),
            card("Regras e transparência",
                 "Governos criam regras para a IA e especialistas pedem transparência.",
                 ["AI Act: lei da União Europeia que regula o uso de IA por nível de risco",
                  "Explainability (explicabilidade): capacidade de entender como a IA chegou a uma decisão"]),
            card("Preconceito nos dados",
                 "Sistemas de reconhecimento facial falham mais em minorias porque foram treinados com dados majoritariamente de pessoas brancas. "
                 "Por isso, decisões judiciais feitas por IA correm o risco de reproduzir preconceitos históricos."),
        ],
    },

    # ======================= 3. BACK-END =======================
    (3, 1): {
        "lab": None,
        "cards": [
            card("O que é Back-End?",
                 "O Back-End é a parte do sistema que roda no servidor. Ele cuida das regras de negócio, da segurança e da comunicação com o banco de dados."),
            card("Servidor web e portas",
                 "A principal função do servidor web é receber e responder requisições HTTP.",
                 ["Porta padrão do HTTP: 80",
                  "Porta padrão do HTTPS (seguro): 443"]),
            card("Flask",
                 "Flask é um microframework escrito em Python. Com poucas linhas já temos um servidor respondendo.",
                 codigo="from flask import Flask\napp = Flask(__name__)\n\n@app.route(\"/\")\ndef home():\n    return \"Olá, CodeQuest!\""),
        ],
    },
    (3, 2): {
        "lab": None,
        "cards": [
            card("Os verbos HTTP",
                 "O HTTP trafega verbos para realizar as operações de CRUD nas APIs.",
                 ["GET: busca dados sem alterá-los",
                  "POST: cria um novo recurso no servidor",
                  "PUT: atualiza um recurso",
                  "DELETE: remove um recurso"]),
            card("API REST e JSON",
                 "Uma API REST é uma interface que usa HTTP para a comunicação entre sistemas. O formato mais usado para trocar dados é o JSON, "
                 "estruturado em chaves e valores.",
                 codigo="{\n  \"username\": \"ana\",\n  \"xp\": 120\n}"),
            card("Códigos de status",
                 "A resposta HTTP sempre traz um código que diz o que aconteceu.",
                 ["200: deu certo",
                  "404: recurso não encontrado",
                  "500: erro dentro do servidor"]),
        ],
    },
    (3, 3): {
        "lab": None,
        "cards": [
            card("SQL e NoSQL",
                 "Os sistemas conversam com bancos SQL (tabelas) ou NoSQL. O MongoDB é um banco NoSQL que guarda documentos parecidos com JSON. "
                 "O SQLite guarda o banco inteiro em um único arquivo."),
            card("ORM",
                 "Um ORM é uma ferramenta que mapeia objetos do código para tabelas do banco, traduzindo uma coisa na outra."),
            card("SQL Injection",
                 "É a injeção de código malicioso em campos de entrada para quebrar o banco. A proteção é a parametrização: nunca monte o SQL concatenando texto do usuário.",
                 codigo="# ERRADO: concatena o que o usuário digitou\ncursor.execute(\"SELECT * FROM users WHERE nome = '\" + nome + \"'\")\n\n# CERTO: parametrizado\ncursor.execute(\"SELECT * FROM users WHERE nome = ?\", (nome,))"),
        ],
    },
    (3, 4): {
        "lab": "js",
        "cards": [
            card("O que é Node.js?",
                 "Node.js é um ambiente de execução de JavaScript no servidor, construído sobre o motor V8. Ele é assíncrono, orientado a eventos e não-bloqueante."),
            card("npm e Express",
                 "O npm é o gerenciador de pacotes padrão do Node.js. O Express é o framework minimalista de rotas mais famoso do ecossistema.",
                 ["npm: instala bibliotecas (npm install express)",
                  "Express: cria rotas e servidores com poucas linhas"]),
            card("Importando módulos",
                 "No JavaScript moderno, importamos pacotes com import ... from.",
                 codigo="import express from 'express';\n\nconst app = express();\napp.get('/', (req, res) => res.send('Olá!'));\napp.listen(3000);",
                 dica="Lacuna: import express ___ 'express'; a palavra que falta é from."),
        ],
    },
    (3, 5): {
        "lab": "bughunt",
        "cards": [
            card("Flask x Django",
                 "Python brilha no Back-End com dois frameworks famosos.",
                 ["Flask: microframework maleável, você escolhe as peças",
                  "Django: framework robusto \"batteries-included\", já traz ORM e painel Admin"]),
            card("Identação e pip",
                 "Em Python, a identação (os espaços no começo da linha) delimita os blocos de código. O pip é o gerenciador que baixa bibliotecas.",
                 codigo="pip install flask",
                 dica="Ordem do comando: pip install flask."),
            card("Rotas com decorador",
                 "No Flask, o decorador @app.route vincula uma rota (endereço) a uma função.",
                 codigo="@app.route(\"/ranking\")\ndef ranking():\n    return \"Aqui vai o ranking\""),
        ],
    },

    # ======================= 4. FRONT-END =======================
    (4, 1): {
        "lab": "css",
        "cards": [
            card("HTML: a estrutura",
                 "O HTML marca a estrutura da página com tags. A tag p cria um parágrafo e a tag a cria um link, que usa o atributo href para dizer o destino.",
                 codigo="<p>Meu parágrafo</p>\n<a href=\"https://exemplo.com\">Clique aqui</a>"),
            card("CSS: a aparência",
                 "O CSS aplica regras de estilo em cascata.",
                 ["background-color: cor do fundo",
                  "margin: espaçamento externo (o padding é o interno)",
                  "color: cor do texto"]),
            card("Seletores",
                 "Para estilizar um elemento específico, usamos seletores.",
                 ["#nome: seleciona pelo id (o caractere é o #)",
                  ".nome: seleciona pela classe (o caractere é o ponto)"],
                 codigo="#titulo {\n  background-color: #2563eb;\n  margin: 16px;\n}"),
        ],
    },
    (4, 2): {
        "lab": "css",
        "cards": [
            card("UI x UX",
                 "UI (User Interface) cuida do aspecto estético da tela. UX (User Experience) estuda os fluxos e a usabilidade."),
            card("Responsivo e acessível",
                 "Uma interface responsiva muda sua estrutura de acordo com o tamanho da tela (celular, tablet, computador). "
                 "O atributo alt das imagens é fundamental para a acessibilidade, porque leitores de tela leem esse texto.",
                 codigo="<img src=\"logo.png\" alt=\"Logo do CodeQuest\">"),
            card("Flexbox e Grid",
                 "O CSS tem dois modelos de layout principais.",
                 ["Flexbox: organiza itens de forma unidimensional (em linha ou em coluna)",
                  "Grid: layouts de duas dimensões, em linhas e colunas"],
                 codigo=".linha { display: flex; gap: 8px; }\n.tabela { display: grid; grid-template-columns: 1fr 1fr; }"),
        ],
    },
    (4, 3): {
        "lab": "js",
        "cards": [
            card("JavaScript e o DOM",
                 "O JavaScript traz dinamismo à página manipulando o DOM (Document Object Model), a estrutura da página em forma de objetos. "
                 "O método console.log() mostra mensagens no painel do desenvolvedor.",
                 codigo="console.log(\"Olá, DOM!\");",
                 dica="Lacuna: Document ___ Object Model. A palavra que falta é object."),
            card("let, const e var",
                 "As formas de declarar variáveis:",
                 ["let: escopo de bloco e aceita reatribuição",
                  "const: trava o valor e impede reatribuição",
                  "var: forma antiga, evite"],
                 codigo="let pontos = 10;\npontos = 20;      // ok\nconst nome = \"Ana\";\n// nome = \"Bia\"; // erro!"),
            card("fetch",
                 "A API nativa fetch faz requisições HTTP assíncronas de forma moderna.",
                 codigo="fetch('/api/dados')\n  .then(r => r.json())\n  .then(dados => console.log(dados));"),
        ],
    },
    (4, 4): {
        "lab": None,
        "cards": [
            card("React e componentes",
                 "O React é mantido pela Meta. Ele quebra a página em componentes reativos, pedaços reaproveitáveis da interface."),
            card("Props e estado",
                 "Props são dados imutáveis passados de um componente pai para um filho. O Hook useState cria estados dinâmicos locais.",
                 codigo="function Contador() {\n  const [n, setN] = useState(0);\n  return <button onClick={() => setN(n + 1)}>{n}</button>;\n}"),
            card("Virtual DOM e JSX",
                 "O React usa uma cópia otimizada em memória do DOM real, chamada Virtual DOM, para atualizar só o que mudou. "
                 "A mistura de HTML dentro do código JavaScript se chama JSX."),
        ],
    },
    (4, 5): {
        "lab": None,
        "cards": [
            card("Vue.js",
                 "O Vue é um framework progressivo. No Vue 3, a função createApp cria a aplicação.",
                 codigo="import { createApp } from 'vue';\ncreateApp({ /* ... */ }).mount('#app');"),
            card("Diretivas",
                 "Diretivas são atributos especiais que começam com v-.",
                 ["v-if / v-else: renderização condicional",
                  "v-model: data binding bidirecional em inputs"],
                 codigo="<input v-model=\"nome\">\n<p v-if=\"nome\">Olá, {{ nome }}!</p>\n<p v-else>Digite seu nome</p>"),
            card("Build tools",
                 "Ferramentas de build empacotam o projeto. O Vite é a ferramenta moderna que substitui o Webpack em novos apps, com muito mais velocidade."),
        ],
    },

    # ======================= 5. MOBILE =======================
    (5, 1): {
        "lab": None,
        "cards": [
            card("Dois caminhos",
                 "O desenvolvimento mobile se divide em nativo e multiplataforma. Aplicativos compilados direto para a linguagem do processador são chamados de nativos."),
            card("Nativo: Android e iOS",
                 "Cada sistema tem sua linguagem oficial.",
                 ["Android: Kotlin (substituiu o Java como linguagem oficial recomendada pelo Google)",
                  "iOS (Apple): Swift"]),
            card("Multiplataforma",
                 "Um único código para as duas plataformas.",
                 ["Flutter: usa a linguagem Dart",
                  "React Native: usa JavaScript"]),
        ],
    },
    (5, 2): {
        "lab": None,
        "cards": [
            card("Sem HTML no mobile",
                 "No desenvolvimento móvel não existem tags HTML. Usamos componentes nativos ou equivalentes. No React Native, o View equivale à tag div e o Text exibe textos.",
                 codigo="<View>\n  <Text>Olá, mundo!</Text>\n</View>"),
            card("Flexbox no celular",
                 "O layout é ajustado por Flexbox.",
                 ["flexDirection padrão no React Native: column (coluna)",
                  "justifyContent alinha os itens no eixo principal"]),
            card("Telas compridas",
                 "O componente ScrollView adiciona barras de rolagem em telas compridas.",
                 codigo="<ScrollView>\n  {/* conteúdo comprido */}\n</ScrollView>"),
        ],
    },
    (5, 3): {
        "lab": None,
        "cards": [
            card("Tipos de navegação",
                 "Os aplicativos guiam o usuário entre telas de três jeitos principais.",
                 ["Stack: empilha telas e o usuário volta deslizando",
                  "Tabs: abas fixas (Bottom Tab Navigation, embaixo)",
                  "Drawer: menu que desliza a partir da lateral"]),
            card("Biblioteca padrão",
                 "O padrão de fato para navegação no React Native é a biblioteca React Navigation."),
            card("Botões com efeito",
                 "Botões que mudam de opacidade ao toque usam o componente TouchableOpacity.",
                 codigo="<TouchableOpacity onPress={abrir}>\n  <Text>Abrir</Text>\n</TouchableOpacity>"),
        ],
    },
    (5, 4): {
        "lab": "js",
        "cards": [
            card("Salvando dados no aparelho",
                 "O AsyncStorage guarda pequenos dados chave-valor locais de forma assíncrona. Para bancos locais embarcados e leves (NoSQL), um exemplo é o Realm."),
            card("JSON na prática",
                 "O AsyncStorage grava texto. Para guardar um objeto, convertemos com JSON.stringify; para voltar a objeto, usamos JSON.parse.",
                 codigo="const texto = JSON.stringify({ nome: 'Ana' });\nconst objeto = JSON.parse(texto);"),
            card("Busca em segundo plano",
                 "Para buscar dados de APIs externas sem travar a tela, usamos funções async.",
                 codigo="async function carregar() {\n  const r = await fetch('https://exemplo.com/api');\n  return r.json();\n}"),
        ],
    },
    (5, 5): {
        "lab": None,
        "cards": [
            card("Pacotes de instalação",
                 "Para distribuir o app, geramos pacotes assinados.",
                 ["Android: o formato AAB (Android App Bundle) substituiu o .apk para novos envios na Google Play",
                  "iOS: o arquivo final de instalação é o .ipa"]),
            card("As lojas",
                 "Cada plataforma tem sua loja oficial.",
                 ["Apple: App Store",
                  "Android: Google Play, gerenciada pelo Google Play Console"]),
            card("Testes antes de lançar",
                 "Antes do lançamento fazemos testes internos com um grupo pequeno, o beta test, para achar problemas antes do público geral."),
        ],
    },

    # ======================= 6. VERSIONAMENTO =======================
    (6, 1): {
        "lab": None,
        "cards": [
            card("O que é o Git?",
                 "O Git é um sistema de controle de versão distribuído: cada pessoa tem uma cópia completa do histórico. Foi criado por Linus Torvalds em 2005."),
            card("Começando um repositório",
                 "O comando git init cria e inicializa um repositório Git local vazio. Os arquivos aguardam o commit na Staging Area.",
                 codigo="git init"),
            card("Olhando o que mudou",
                 "O comando git status lista os arquivos modificados que ainda não foram salvos no histórico.",
                 codigo="git status"),
        ],
    },
    (6, 2): {
        "lab": None,
        "cards": [
            card("Adicionar à staging",
                 "O git add . indexa todas as alterações da pasta atual para o próximo commit.",
                 codigo="git add ."),
            card("Fazer o commit",
                 "O commit consolida as alterações no histórico, com uma mensagem curta passada pelo parâmetro -m.",
                 codigo="git commit -m 'mensagem'"),
            card("Histórico e hash",
                 "O git log mostra o histórico cronológico de commits. Cada commit recebe um identificador único e longo, o hash.",
                 codigo="git log"),
        ],
    },
    (6, 3): {
        "lab": None,
        "cards": [
            card("Branches",
                 "Uma branch isola uma frente de trabalho. A branch principal padrão dos novos repositórios se chama main.",
                 ["git branch: lista as branches locais",
                  "git checkout -b nome: cria e já muda para a nova branch"]),
            card("Juntando o trabalho",
                 "Ao terminar uma tarefa, trazemos o código de volta para a branch principal com git merge.",
                 codigo="git checkout main\ngit merge minha-branch"),
            card("Merge x Rebase",
                 "A estratégia alternativa ao merge, que reescreve o histórico de commits de forma linear, se chama rebase."),
        ],
    },
    (6, 4): {
        "lab": None,
        "cards": [
            card("Repositório remoto",
                 "Plataformas como o GitHub guardam repositórios remotos para sincronizar o trabalho da equipe. O apelido padrão do remoto principal é origin.",
                 codigo="git remote -v"),
            card("Enviar e receber",
                 "Cada comando tem uma direção.",
                 ["git push: empurra seus commits para o servidor remoto",
                  "git pull: baixa e mescla as atualizações do remoto",
                  "git clone: baixa uma cópia inteira do repositório pela primeira vez"]),
            card("Pull Request",
                 "Uma solicitação formal para fundir seu código no repositório de outra pessoa chama-se Pull Request (PR)."),
        ],
    },
    (6, 5): {
        "lab": None,
        "cards": [
            card("Conflitos",
                 "Um conflito acontece quando alterações concorrentes mexem nas mesmas linhas do mesmo arquivo, feitas por pessoas diferentes. Quem resolve é o dev, manualmente."),
            card("Boas práticas",
                 "Mensagens de commit profissionais são curtas e claras. O arquivo .gitignore, na raiz, diz ao Git quais pastas ignorar, como node_modules/ ou venv/.",
                 codigo="node_modules/\nvenv/\n.env"),
            card("Limpando e guardando",
                 "Dois comandos úteis para o dia a dia:",
                 ["git clean: limpa arquivos temporários não rastreados",
                  "git stash: guarda modificações incompletas provisoriamente, sem comitar"]),
        ],
    },
}


def get_unit_content(trail_id, unit_order):
    """Devolve o conteúdo de teoria da unidade (ou um padrão vazio, que cai no intro_text do banco)."""
    return UNIT_CARDS.get((trail_id, unit_order), {"cards": [], "lab": None})
