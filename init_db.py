import os
import sqlite3
from werkzeug.security import generate_password_hash

def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    return sqlite3.connect("database.db")

def ph():
    return "%s" if os.environ.get("DATABASE_URL") else "?"

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    p = ph()
    is_pg = (p == "%s")

    print("--- Iniciando CodeQuest Database Setup ---")

    # USERS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_active TEXT DEFAULT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        )
    """)

    # TRILHAS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS trails (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            description TEXT NOT NULL,
            color TEXT NOT NULL,
            order_num INTEGER NOT NULL
        )
    """)

    # UNIDADES
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS units (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            trail_id INTEGER NOT NULL,
            order_num INTEGER NOT NULL,
            title TEXT NOT NULL,
            intro_text TEXT NOT NULL
        )
    """)

    # PERGUNTAS (agora com unit_id)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS questions (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            unit_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            type TEXT NOT NULL DEFAULT 'multiple',
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT
        )
    """)

    # PROGRESSO POR UNIDADE
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS unit_progress (
            user_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (user_id, unit_id)
        )
    """ if not is_pg else f"""
        CREATE TABLE IF NOT EXISTS unit_progress (
            user_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (user_id, unit_id)
        )
    """)

    # RESPOSTAS (por unidade + questão)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answered (
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL
        )
    """)

    # ADMIN PADRÃO
    cursor.execute(f"SELECT id FROM users WHERE username={p}", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            f"INSERT INTO users (username, password, is_admin) VALUES ({p},{p},{p})",
            ("admin", generate_password_hash("admin123"), True)
        )

    # DADOS
    cursor.execute("SELECT COUNT(*) FROM trails")
    if cursor.fetchone()[0] == 0:
        print("Inserindo trilhas, unidades e perguntas...")
        _insert_data(cursor, p)

    conn.commit()
    conn.close()
    print("--- Setup Finalizado ---")


def _insert_data(cursor, p):
    # =====================
    # TRILHAS
    # =====================
    trails = [
        (1, "Banco de Dados",       "🗄️",  "Fundamentos de MySQL, SQL, normalização e transações.",         "#3b82f6", 1),
        (2, "Inteligência Artificial","🤖", "IA fraca e forte, modelos generativos e ética.",                "#8b5cf6", 2),
        (3, "Back-End",              "⚙️",  "HTTP, APIs, Node.js, Python e servidores.",                     "#22c55e", 3),
        (4, "Front-End",             "🎨",  "HTML, CSS, JavaScript, React e Vue.",                           "#f97316", 4),
        (5, "Mobile",                "📱",  "Desenvolvimento de apps iOS e Android.",                        "#06b6d4", 5),
        (6, "Versionamento",         "🔧",  "Git, GitHub, branches e boas práticas.",                        "#f59e0b", 6),
    ]
    for t in trails:
        cursor.execute(
            f"INSERT INTO trails (id, name, icon, description, color, order_num) VALUES ({p},{p},{p},{p},{p},{p})",
            t
        )

    # =====================
    # UNIDADES + PERGUNTAS
    # =====================

    # Estrutura: (trail_id, order_num, title, intro_text, [ (question, answer, diff, type, o1,o2,o3,o4), ... ])
    data = [

        # ======= BANCO DE DADOS =======
        (1, 1, "Introdução ao MySQL",
         "O MySQL é um sistema de gerenciamento de banco de dados relacional (SGBD) de código aberto. Ele usa SQL (Structured Query Language) para criar, ler, atualizar e deletar dados. O MySQL Workbench é a ferramenta visual oficial para administrar bancos MySQL.",
         [
             ("O que é o MySQL Server?", "um sistema de gerenciamento de banco de dados", 1, "multiple",
              "Um sistema de gerenciamento de banco de dados", "Uma ferramenta de design gráfico", "Um sistema operacional", "Um editor de texto"),
             ("Para que serve o MySQL Workbench?", "criar diagramas er e gerenciar bancos de dados", 1, "multiple",
              "Navegar na web", "Criar diagramas ER e gerenciar bancos de dados", "Desenvolver aplicativos móveis", "Editar imagens"),
             ("Qual é a linguagem usada pelo MySQL para consultas?", "sql", 1, "multiple",
              "Python", "HTML", "SQL", "Java"),
             ("MySQL é um banco de dados do tipo...?", "relacional", 1, "multiple",
              "Relacional", "Orientado a objetos", "Hierárquico", "Em grafos"),
             ("Qual empresa atualmente mantém o MySQL?", "oracle", 1, "multiple",
              "Microsoft", "Oracle", "Google", "IBM"),
         ]),

        (1, 2, "Relacionamentos entre Tabelas",
         "Relacionamentos definem como tabelas se conectam. No tipo um-para-muitos (1:N), um registro de uma tabela pode se relacionar com vários da outra — como um cliente que faz vários pedidos. Chaves estrangeiras (FK) implementam esses relacionamentos.",
         [
             ("Como os registros da entidade 'Muitos' se relacionam com a 'Um'?", "um registro em muitos tem um na entidade um", 1, "multiple",
              "Um registro em 'Muitos' não tem relação", "Um registro em 'Muitos' tem vários na 'Um'", "Um registro em 'Muitos' tem um na entidade 'Um'", "Um registro em 'Muitos' só se relaciona com outras tabelas"),
             ("O que melhor exemplifica um relacionamento um-para-muitos?", "um cliente faz varios pedidos", 1, "multiple",
              "Um funcionário com vários empregadores", "Um produto tem vários fornecedores", "Um pedido feito por vários clientes", "Um cliente faz vários pedidos"),
             ("O que é uma chave estrangeira (FK)?", "coluna que referencia a chave primaria de outra tabela", 2, "multiple",
              "Coluna que referencia a chave primária de outra tabela", "Uma chave duplicada", "O índice principal da tabela", "Uma senha de acesso"),
             ("No relacionamento N:N, como ele é implementado no banco?", "tabela intermediaria", 2, "multiple",
              "Duas chaves primárias", "Tabela intermediária", "Chave estrangeira direta", "Não é possível implementar"),
             ("Qual símbolo representa 'muitos' na notação de Crow's Foot?", "pe de galinha", 2, "multiple",
              "Traço único", "Círculo", "Pé de galinha", "Seta dupla"),
         ]),

        (1, 3, "Normalização",
         "Normalização é o processo de organizar tabelas para reduzir redundância e evitar inconsistências. As formas normais (1NF, 2NF, 3NF) são regras progressivas: cada forma exige que a anterior já esteja satisfeita.",
         [
             ("Qual é o principal objetivo da normalização?", "evitar anomalias como redundancia e inconsistencia", 2, "multiple",
              "Reduzir espaço ao máximo", "Melhorar consultas complexas", "Evitar anomalias como redundância e inconsistência", "Eliminar índices"),
             ("O que a 3NF elimina?", "dependencias transitivas", 2, "multiple",
              "Relacionamentos entre tabelas", "Dados atômicos", "Dependências parciais", "Dependências transitivas"),
             ("Para estar na 3NF, a tabela deve primeiro estar em qual forma?", "2nf", 2, "multiple",
              "4NF", "BCNF", "2NF", "1NF"),
             ("Qual é uma vantagem do banco normalizado?", "minimiza redundancias e melhora a integridade", 2, "multiple",
              "Cria tabelas com muitos campos", "Reduz número de junções", "Elimina chaves estrangeiras", "Minimiza redundâncias e melhora a integridade"),
             ("A normalização divide tabelas. O processo inverso chama-se...?", "desnormalizacao", 2, "multiple",
              "Fragmentação", "Desnormalização", "Particionamento", "Indexação"),
         ]),

        (1, 4, "SQL e DML",
         "SQL tem subconjuntos: DDL (CREATE, DROP), DML (INSERT, UPDATE, DELETE, SELECT) e DCL (GRANT, REVOKE). O histórico do SQL começa com o artigo de Edgar Codd em 1970 e a padronização pelo ANSI em 1986.",
         [
             ("Qual dos seguintes é um comando DML?", "delete", 2, "multiple",
              "CREATE", "DELETE", "GRANT", "DROP"),
             ("O artigo de Edgar F. Codd, que originou o SQL, foi publicado em?", "1970", 2, "multiple",
              "1986", "1970", "1981", "2003"),
             ("Qual comando SQL recupera dados de uma tabela?", "select", 1, "multiple",
              "INSERT", "UPDATE", "SELECT", "DELETE"),
             ("Qual comando cria uma nova tabela no banco?", "create table", 2, "multiple",
              "INSERT TABLE", "MAKE TABLE", "CREATE TABLE", "NEW TABLE"),
             ("O comando UPDATE serve para...?", "modificar dados existentes", 2, "multiple",
              "Apagar registros", "Inserir novos dados", "Modificar dados existentes", "Criar colunas"),
         ]),

        (1, 5, "Transações ACID e Índices",
         "ACID garante confiabilidade: Atomicidade (tudo ou nada), Consistência (regras sempre respeitadas), Isolamento (transações independentes) e Durabilidade (dados persistem após commit). Índices aceleram buscas mas aumentam o custo de escrita.",
         [
             ("Qual propriedade ACID garante que o banco sempre respeita suas regras após uma transação?", "consistencia", 3, "multiple",
              "Consistência", "Atomicidade", "Durabilidade", "Isolamento"),
             ("Quando um banco reverte operações após uma falha, qual propriedade ACID está sendo aplicada?", "atomicidade", 3, "multiple",
              "Durabilidade", "Atomicidade", "Isolamento", "Consistência"),
             ("Qual comando confirma permanentemente as alterações de uma transação?", "commit", 2, "multiple",
              "ROLLBACK", "SAVEPOINT", "BEGIN", "COMMIT"),
             ("Qual é o principal objetivo de criar um índice?", "acelerar consultas na coluna indexada", 2, "multiple",
              "Reduzir tamanho da tabela", "Ordenar dados alfabeticamente", "Acelerar consultas na coluna indexada", "Garantir integridade referencial"),
             ("Qual é o principal efeito colateral de muitos índices?", "degradacao em operacoes de escrita", 3, "multiple",
              "Melhora todas as consultas", "Degradação em operações de escrita", "Impossibilidade de criar tabelas", "Reduz espaço em disco"),
         ]),

        # ======= INTELIGÊNCIA ARTIFICIAL =======
        (2, 1, "O que é Inteligência Artificial?",
         "IA é a área da computação que cria sistemas capazes de realizar tarefas que normalmente exigem inteligência humana. IA Fraca (ou Estreita) é especializada em uma tarefa. IA Forte seria capaz de qualquer tarefa cognitiva humana — ainda não existe.",
         [
             ("O ChatGPT consegue conversar, escrever código e contar piadas. Isso o torna uma IA Forte?", "nao ainda e ia fraca especializada em linguagem", 1, "multiple",
              "Sim, passa no Teste de Turing", "Não, ainda é IA Fraca, especializada em linguagem", "Sim, demonstra inteligência geral", "Depende da qualidade das respostas"),
             ("O ChatGPT é classificado como qual tipo de IA?", "ia com memoria limitada", 2, "multiple",
              "IA com memória limitada", "IA com teoria da mente completa", "IA autoconsciente", "Máquina puramente reativa"),
             ("Qual é a diferença entre IA discriminativa e IA generativa?", "a discriminativa classifica a generativa cria dados novos", 2, "multiple",
              "A discriminativa é mais moderna", "A generativa só usa imagens", "A discriminativa classifica; a generativa cria dados novos", "Não há diferença real"),
             ("Uma IA que só joga xadrez é classificada como...?", "ia fraca ou estreita", 1, "multiple",
              "IA Forte", "IA Fraca ou Estreita", "IA Consciente", "IA Generalista"),
             ("Qual teste clássico avalia se uma máquina exibe comportamento inteligente?", "teste de turing", 1, "multiple",
              "Teste de Turing", "Teste ACID", "Teste de Codd", "Teste de Shannon"),
         ]),

        (2, 2, "Tipos de IA e Aplicações",
         "Existem diferentes categorias de IA: reativa (responde a estímulos), com memória limitada (usa dados históricos, como carros autônomos), teoria da mente e autoconsciência (ainda teóricas). Aplicações práticas incluem recomendações, diagnósticos e assistentes virtuais.",
         [
             ("Por que o Spotify recomenda músicas de artistas que você nunca ouviu?", "analisa e compara padroes de gosto musical", 1, "multiple",
              "Porque grava conversas sobre música", "Porque os artistas pagam", "Porque analisa e compara padrões de gosto musical", "Porque é aleatório"),
             ("Carros autônomos que usam dados de viagens anteriores são classificados como IA de...?", "memoria limitada", 2, "multiple",
              "Memória limitada", "Teoria da mente", "IA reativa", "IA forte"),
             ("Qual é a principal causa de vieses em sistemas de IA?", "dados de treinamento que refletem preconceitos historicos", 2, "multiple",
              "Bugs no código", "Falta de capacidade computacional", "Dados de treinamento que refletem preconceitos históricos", "Má intenção dos programadores"),
             ("Em decisões de alto impacto social, qual deve ser o papel ideal da IA?", "servir como ferramenta de apoio com humanos decidindo", 2, "multiple",
              "Substituir completamente decisões humanas", "Decidir autonomamente casos simples", "Servir como ferramenta de apoio com humanos decidindo", "Não ser usada"),
             ("Um sistema de spam que apenas filtra e-mails é um exemplo de IA...?", "reativa ou estreita", 1, "multiple",
              "Forte", "Com teoria da mente", "Reativa ou Estreita", "Autoconsciente"),
         ]),

        (2, 3, "História da IA",
         "A IA passou por períodos de euforia e 'invernos' (falta de financiamento). O boom atual é impulsionado por big data, GPUs potentes e algoritmos de deep learning. Marcos importantes: Turing (1950), redes neurais (1980s), Deep Blue (1997), deep learning (2012), LLMs (2020+).",
         [
             ("Qual foi o principal motivo dos 'Invernos da IA'?", "expectativas irreais contra limitacoes tecnicas", 2, "multiple",
              "Falta de cientistas", "Expectativas irreais contra limitações técnicas", "Proibição governamental", "Competição com outras tecnologias"),
             ("Qual dos seguintes fatores mais impulsionou o boom recente da IA?", "big data gpus e deep learning", 2, "multiple",
              "Leis governamentais", "Big data, GPUs e deep learning", "Redução do custo de energia", "Aumento de programadores"),
             ("Em que ano Alan Turing propôs o famoso teste de comportamento inteligente?", "1950", 2, "multiple",
              "1970", "1986", "1950", "2001"),
             ("O computador Deep Blue ficou famoso por...?", "vencer o campeon mundial de xadrez", 2, "multiple",
              "Ser o primeiro PC pessoal", "Vencer o campeão mundial de xadrez", "Criar a internet", "Desenvolver o primeiro chatbot"),
             ("O que são LLMs (Large Language Models)?", "modelos de ia treinados em grandes volumes de texto", 3, "multiple",
              "Linguagens de programação novas", "Modelos de IA treinados em grandes volumes de texto", "Sistemas operacionais de IA", "Hardwares especializados"),
         ]),

        (2, 4, "IA Generativa e Modelos",
         "IA Generativa cria conteúdo novo: imagens, texto, áudio. Os principais modelos são: GANs (gerador vs. discriminador), VAEs (comprimem e reconstroem dados com controle), Transformers (baseados em atenção, usados em texto). Cada um tem vantagens diferentes.",
         [
             ("Uma empresa quer gerar variações de logos com controle fino de cores e formas. Qual modelo é mais indicado?", "vae pelo controle fino das variacoes", 3, "multiple",
              "VAE – pelo controle fino das variações", "Transformer – pela capacidade textual", "GAN – pela qualidade fotorrealista", "BERT – pela compreensão de contexto"),
             ("Uma empresa de jogos precisa gerar variações de espadas com GPU limitada. Qual combinação seria mais adequada?", "vae apenas controle e eficiencia", 3, "multiple",
              "VAE apenas – controle e eficiência", "Transformer apenas", "GAN apenas – máxima qualidade visual", "GAN + Transformer"),
             ("O site ThisPersonDoesNotExist usa StyleGAN. Qual preocupação ética isso levanta?", "pode ser usada para criar identidades falsas e deepfakes", 3, "multiple",
              "Pode ser usada para criar identidades falsas e deepfakes", "Usa muita energia elétrica", "Os rostos são protegidos por direitos autorais", "Compete com fotógrafos"),
             ("Por que a IA generativa precisa de bilhões de exemplos, enquanto uma criança aprende com poucos?", "a ia nao conhece o mundo fisico aprende do zero", 3, "multiple",
              "Os computadores são lentos", "A IA não conhece o mundo físico; aprende do zero", "Os programadores não sabem ensinar", "A IA é menos inteligente"),
             ("O que é uma GAN (Generative Adversarial Network)?", "dois modelos que competem gerador e discriminador", 3, "multiple",
              "Um banco de dados generativo", "Dois modelos que competem: gerador e discriminador", "Um tipo de linguagem de programação", "Uma rede social de IA"),
         ]),

        (2, 5, "Ética em IA",
         "IA levanta questões éticas sérias: viés algorítmico, privacidade, deepfakes, substituição de empregos e tomada de decisão autônoma. Regulamentações como o AI Act europeu buscam garantir IA confiável, transparente e segura.",
         [
             ("O que é um deepfake?", "midia manipulada com ia para substituir rostos ou vozes", 2, "multiple",
              "Mídia manipulada com IA para substituir rostos ou vozes", "Um tipo de vírus de computador", "Uma técnica de compressão de vídeo", "Um filtro de rede social"),
             ("Qual lei europeia regula o uso de IA por nível de risco?", "ai act", 3, "multiple",
              "GDPR", "AI Act", "LGPD", "Digital Markets Act"),
             ("Por que sistemas de reconhecimento facial têm desempenho pior em pessoas negras?", "treinados com dados majoritariamente de pessoas brancas", 2, "multiple",
              "Problema técnico de iluminação", "Treinados com dados majoritariamente de pessoas brancas", "Algoritmo incorreto", "Câmeras de baixa resolução"),
             ("Em decisões judiciais automatizadas, qual é o maior risco ético?", "reproducao de vieses historicos do sistema juridico", 3, "multiple",
              "Alto custo computacional", "Reprodução de vieses históricos do sistema jurídico", "Lentidão do sistema", "Falta de conectividade"),
             ("O que significa 'explainability' (explicabilidade) em IA?", "capacidade de entender como a ia chegou a uma decisao", 3, "multiple",
              "Capacidade de entender como a IA chegou a uma decisão", "Velocidade de resposta da IA", "Custo de treinamento do modelo", "Número de parâmetros do modelo"),
         ]),

        # ======= BACK-END =======
        (3, 1, "Fundamentos de Back-End",
         "Back-End é a parte do sistema que roda no servidor, invisível ao usuário. Ele processa lógica de negócio, acessa bancos de dados e retorna respostas. Tecnologias comuns: Python (Flask/Django), Node.js (Express), Java (Spring).",
         [
             ("Qual é a principal função do servidor web como Apache?", "receber e responder requisicoes http", 1, "multiple",
              "Interface gráfica", "Receber e responder requisições HTTP", "Plugins visuais", "Design front-end"),
             ("O que é Back-End?", "parte do sistema que roda no servidor", 1, "multiple",
              "A interface visual do site", "Parte do sistema que roda no servidor", "O banco de dados somente", "O design das páginas"),
             ("Qual linguagem é amplamente usada em back-end com o framework Flask?", "python", 1, "multiple",
              "JavaScript", "Python", "HTML", "CSS"),
             ("O que significa 'servidor'?", "computador que processa e responde requisicoes", 1, "multiple",
              "Computador do usuário", "Navegador web", "Computador que processa e responde requisições", "Banco de dados"),
             ("Qual porta padrão o protocolo HTTP usa?", "80", 2, "multiple",
              "443", "22", "80", "3306"),
         ]),

        (3, 2, "HTTP e APIs",
         "HTTP (HyperText Transfer Protocol) define como clientes e servidores se comunicam. Métodos: GET (buscar), POST (criar), PUT (atualizar), DELETE (apagar). APIs REST usam esses métodos para expor funcionalidades via URLs.",
         [
             ("Qual método HTTP é usado para buscar dados sem alterá-los?", "get", 1, "multiple",
              "POST", "DELETE", "GET", "PUT"),
             ("Qual método HTTP cria um novo recurso no servidor?", "post", 1, "multiple",
              "GET", "POST", "PUT", "PATCH"),
             ("O que é uma API REST?", "interface que usa http para comunicacao entre sistemas", 2, "multiple",
              "Um banco de dados", "Interface que usa HTTP para comunicação entre sistemas", "Um servidor web", "Uma linguagem de programação"),
             ("Qual código HTTP indica que um recurso não foi encontrado?", "404", 2, "multiple",
              "200", "500", "301", "404"),
             ("Qual formato de dados é mais usado em APIs modernas?", "json", 2, "multiple",
              "XML", "CSV", "JSON", "HTML"),
         ]),

        (3, 3, "Bancos de Dados no Back-End",
         "O back-end se conecta a bancos de dados para persistir informações. Bancos relacionais (MySQL, PostgreSQL) usam SQL. Bancos NoSQL (MongoDB, Redis) usam outros formatos. ORMs como SQLAlchemy (Python) facilitam essa integração.",
         [
             ("O que é um ORM?", "ferramenta que mapeia objetos para tabelas do banco", 2, "multiple",
              "Um tipo de banco de dados", "Ferramenta que mapeia objetos para tabelas do banco", "Uma linguagem de consulta", "Um servidor de banco"),
             ("Qual banco de dados NoSQL é baseado em documentos JSON?", "mongodb", 2, "multiple",
              "MySQL", "PostgreSQL", "MongoDB", "SQLite"),
             ("O SQLite é ideal para qual cenário?", "desenvolvimento local e projetos pequenos", 1, "multiple",
              "Grandes empresas com milhões de usuários", "Desenvolvimento local e projetos pequenos", "Bancos de dados distribuídos", "Armazenamento em nuvem"),
             ("Qual é a função de uma 'connection string'?", "definir como a aplicacao se conecta ao banco", 2, "multiple",
              "Senha do banco", "Definir como a aplicação se conecta ao banco", "Nome das tabelas", "Tipo de índice usado"),
             ("O que é 'SQL Injection'?", "ataque que insere sql malicioso em inputs do sistema", 3, "multiple",
              "Comando para inserir dados", "Ataque que insere SQL malicioso em inputs do sistema", "Tipo de índice de banco", "Técnica de normalização"),
         ]),

        (3, 4, "Node.js",
         "Node.js permite executar JavaScript no servidor. É baseado em eventos e não-bloqueante (assíncrono), ideal para aplicações em tempo real. O npm é seu gerenciador de pacotes. Express.js é o framework web mais popular para Node.",
         [
             ("O que é Node.js?", "ambiente de execucao de javascript no servidor", 2, "multiple",
              "Um banco de dados", "Um navegador web", "Ambiente de execução de JavaScript no servidor", "Uma linguagem de programação nova"),
             ("Qual é o gerenciador de pacotes padrão do Node.js?", "npm", 1, "multiple",
              "pip", "npm", "composer", "gem"),
             ("Node.js é ideal para aplicações que precisam de...?", "alta concorrencia e tempo real", 2, "multiple",
              "Processamento gráfico intenso", "Alta concorrência e tempo real", "Cálculos científicos pesados", "Edição de vídeo"),
             ("Qual framework web é mais popular com Node.js?", "express", 2, "multiple",
              "Django", "Flask", "Express", "Spring"),
             ("O modelo de execução do Node.js é...?", "assíncrono e não bloqueante", 3, "multiple",
              "Síncrono e bloqueante", "Multi-thread puro", "Assíncrono e não bloqueante", "Baseado em processos"),
         ]),

        (3, 5, "Python no Back-End",
         "Python é uma das linguagens mais usadas em back-end por sua sintaxe simples e ecossistema rico. Flask é minimalista e flexível. Django é completo (ORM, admin, auth incluídos). Ambos são usados em APIs REST e aplicações web.",
         [
             ("Qual framework Python é conhecido por ser minimalista e flexível?", "flask", 2, "multiple",
              "Django", "Flask", "FastAPI", "Spring"),
             ("Qual framework Python já vem com ORM, admin e autenticação embutidos?", "django", 2, "multiple",
              "Flask", "FastAPI", "Django", "Express"),
             ("Como Python lida com indentação?", "e obrigatoria e define blocos de codigo", 1, "multiple",
              "É opcional e decorativa", "É obrigatória e define blocos de código", "Usa chaves como JavaScript", "Usa ponto e vírgula"),
             ("O que é o pip?", "gerenciador de pacotes do python", 1, "multiple",
              "Um framework web", "Gerenciador de pacotes do Python", "Um banco de dados", "Uma IDE"),
             ("Qual decorador Flask define a URL de uma rota?", "@app.route", 2, "multiple",
              "@app.url", "@route.path", "@app.route", "@flask.path"),
         ]),

        # ======= FRONT-END =======
        (4, 1, "HTML e CSS",
         "HTML (HyperText Markup Language) estrutura o conteúdo da web com tags. CSS (Cascading Style Sheets) estiliza esse conteúdo com seletores, propriedades e valores. Juntos, formam a base visual de qualquer site.",
         [
             ("Qual tag HTML cria um parágrafo?", "p", 1, "multiple",
              "div", "p", "span", "h1"),
             ("Qual propriedade CSS define a cor de fundo?", "background-color", 1, "multiple",
              "color", "background-color", "border-color", "font-color"),
             ("O que significa HTML?", "hypertexto markup language", 1, "multiple",
              "Hyper Transfer Markup Language", "HyperText Markup Language", "High Text Making Language", "Hyper Tool Markup Language"),
             ("Qual seletor CSS estiliza todos os elementos de uma classe?", "ponto seguido do nome", 1, "multiple",
              "# seguido do nome", ". seguido do nome", "@ seguido do nome", "* seguido do nome"),
             ("Qual propriedade CSS controla o espaço interno de um elemento?", "padding", 1, "multiple",
              "margin", "padding", "border", "spacing"),
         ]),

        (4, 2, "Interfaces e Usabilidade",
         "UX (User Experience) trata da experiência do usuário. UI (User Interface) é a interface visual. Boas interfaces são intuitivas, acessíveis e responsivas. Princípios como hierarquia visual, contraste e consistência guiam um bom design.",
         [
             ("O que significa UX?", "experiencia do usuario", 1, "multiple",
              "User eXecution", "User eXperience", "Universal eXchange", "Unified eXperience"),
             ("Uma interface responsiva se adapta a...?", "diferentes tamanhos de tela", 1, "multiple",
              "Diferentes idiomas", "Diferentes tamanhos de tela", "Diferentes sistemas operacionais", "Diferentes velocidades de internet"),
             ("Qual propriedade CSS torna um layout responsivo por colunas flexíveis?", "flexbox ou grid", 2, "multiple",
              "float", "position", "flexbox ou grid", "display: block"),
             ("O que é acessibilidade web?", "garantir que sites funcionem para pessoas com deficiencias", 2, "multiple",
              "Sites com animações bonitas", "Garantir que sites funcionem para pessoas com deficiências", "Velocidade de carregamento", "Compatibilidade com todos os navegadores"),
             ("O atributo HTML 'alt' em imagens serve para...?", "descrever a imagem para leitores de tela", 2, "multiple",
              "Definir o tamanho da imagem", "Descrever a imagem para leitores de tela", "Aplicar filtros visuais", "Definir o link da imagem"),
         ]),

        (4, 3, "JavaScript",
         "JavaScript (JS) é a linguagem de programação da web, executada no navegador. Permite interatividade: validação de formulários, animações, requisições assíncronas (fetch/AJAX). É também usada no back-end com Node.js.",
         [
             ("Qual função JavaScript exibe uma mensagem no console?", "console.log", 1, "multiple",
              "print()", "console.log()", "alert.show()", "log.print()"),
             ("O que é o DOM?", "representacao em arvore dos elementos html", 2, "multiple",
              "Um banco de dados do navegador", "Representação em árvore dos elementos HTML", "Uma biblioteca JavaScript", "Um servidor web"),
             ("O que faz o 'fetch' em JavaScript?", "faz requisicoes http assincronas", 2, "multiple",
              "Busca arquivos locais", "Faz requisições HTTP assíncronas", "Estiliza elementos", "Valida formulários"),
             ("Como declarar uma variável de valor imutável em JS moderno?", "const", 1, "multiple",
              "var", "let", "const", "def"),
             ("O que é um evento em JavaScript?", "acao do usuario como clique ou tecla pressionada", 1, "multiple",
              "Um erro no código", "Uma função matemática", "Ação do usuário como clique ou tecla pressionada", "Um tipo de variável"),
         ]),

        (4, 4, "React",
         "React é uma biblioteca JavaScript para criar interfaces baseadas em componentes reutilizáveis. Usa um DOM virtual para atualizações eficientes. Conceitos principais: componentes, props, state e hooks (useState, useEffect).",
         [
             ("React é uma biblioteca criada por...?", "meta facebook", 2, "multiple",
              "Google", "Microsoft", "Meta (Facebook)", "Apple"),
             ("O que são 'props' no React?", "dados passados de um componente pai para filho", 2, "multiple",
              "Estilos CSS do componente", "Dados passados de um componente pai para filho", "Funções internas do componente", "Variáveis globais"),
             ("Qual hook React gerencia estado local de um componente?", "usestate", 2, "multiple",
              "useEffect", "useContext", "useState", "useRef"),
             ("O que é o Virtual DOM?", "copia leve do dom real para otimizar atualizacoes", 3, "multiple",
              "Um banco de dados do React", "Cópia leve do DOM real para otimizar atualizações", "Um servidor virtual", "Uma extensão do navegador"),
             ("JSX é...?", "sintaxe que mistura javascript e html no react", 2, "multiple",
              "Uma linguagem de programação nova", "Sintaxe que mistura JavaScript e HTML no React", "Um banco de dados", "Um framework CSS"),
         ]),

        (4, 5, "Vue.js",
         "Vue.js é um framework JavaScript progressivo para criar interfaces. É mais fácil de aprender que React. Usa template declarativo, reatividade automática e componentes .vue (Single File Components). Conceitos: v-bind, v-model, v-if, v-for.",
         [
             ("Vue.js foi criado por...?", "evan you", 2, "multiple",
              "Google", "Meta", "Evan You", "Microsoft"),
             ("Qual diretiva Vue vincula dados a um input de formulário bidirecionalmente?", "v-model", 2, "multiple",
              "v-bind", "v-on", "v-model", "v-data"),
             ("Qual diretiva Vue renderiza um elemento condicionalmente?", "v-if", 1, "multiple",
              "v-show-if", "v-for", "v-if", "v-when"),
             ("O que é um SFC (Single File Component) no Vue?", "arquivo vue com template script e style juntos", 2, "multiple",
              "Um servidor Vue", "Arquivo Vue com template, script e style juntos", "Uma função global", "Um plugin do Vue"),
             ("Qual é a principal diferença entre Vue e React?", "vue e um framework completo react e so uma biblioteca", 3, "multiple",
              "React é mais rápido que Vue sempre", "Vue é um framework completo; React é só uma biblioteca", "Vue usa JavaScript puro; React usa TypeScript", "Não há diferença prática"),
         ]),

        # ======= MOBILE =======
        (5, 1, "Introdução ao Desenvolvimento Mobile",
         "Aplicativos mobile rodam em smartphones e tablets. Podem ser nativos (Swift/iOS, Kotlin/Android), híbridos (React Native, Flutter) ou PWAs (Progressive Web Apps). Cada abordagem tem trade-offs entre desempenho e custo de desenvolvimento.",
         [
             ("Qual linguagem é usada para desenvolvimento nativo Android?", "kotlin", 1, "multiple",
              "Swift", "Kotlin", "Dart", "JavaScript"),
             ("Qual linguagem é usada para desenvolvimento nativo iOS?", "swift", 1, "multiple",
              "Kotlin", "Java", "Swift", "Dart"),
             ("O que é React Native?", "framework para criar apps mobile com javascript", 2, "multiple",
              "Um banco de dados mobile", "Framework para criar apps mobile com JavaScript", "Um sistema operacional", "Uma loja de aplicativos"),
             ("O que é um PWA?", "aplicativo web que funciona como app mobile", 2, "multiple",
              "Um tipo de banco de dados", "Aplicativo web que funciona como app mobile", "Uma loja de apps", "Um sistema de pagamento"),
             ("Qual framework usa Dart para criar apps nativos iOS e Android?", "flutter", 2, "multiple",
              "React Native", "Ionic", "Flutter", "Xamarin"),
         ]),

        (5, 2, "Estrutura e Ciclo de Vida",
         "Todo app mobile tem um ciclo de vida: criação, execução, pausa, retomada e destruição. Componentes principais incluem telas (activities/views), navegação entre telas e gerenciamento de estado. O design deve ser pensado para telas pequenas e toque.",
         [
             ("O que é o ciclo de vida de um aplicativo?", "estados pelos quais o app passa da criacao ao encerramento", 2, "multiple",
              "O tempo de carregamento do app", "Estados pelos quais o app passa da criação ao encerramento", "A lista de permissões do app", "O tamanho do arquivo APK"),
             ("O que é navegação em apps mobile?", "sistema de transicao entre telas do aplicativo", 1, "multiple",
              "Botão de voltar do celular", "Sistema de transição entre telas do aplicativo", "Mapa GPS integrado", "Menu de configurações"),
             ("Qual das seguintes é uma boa prática de UI para mobile?", "botoes grandes e espacados para toque facil", 1, "multiple",
              "Textos pequenos para caber mais conteúdo", "Botões grandes e espaçados para toque fácil", "Menus com muitos níveis", "Cores escuras sempre"),
             ("O que é um APK?", "arquivo de instalacao de apps android", 2, "multiple",
              "Linguagem de programação", "Arquivo de instalação de apps Android", "Um framework mobile", "Um banco de dados mobile"),
             ("Qual evento ocorre quando o usuário minimiza o app?", "o app entra em pausa", 2, "multiple",
              "O app é desinstalado", "O app reinicia do zero", "O app entra em pausa", "O app perde todos os dados"),
         ]),

        (5, 3, "Interatividade e Navegação",
         "Interatividade em apps envolve gestos (toque, swipe, pinch), animações e feedback visual. A navegação pode ser por abas, gaveta lateral (drawer) ou pilha de telas (stack). Uma boa navegação é intuitiva e nunca deixa o usuário perdido.",
         [
             ("O que é um 'swipe' em mobile?", "gesto de deslizar o dedo na tela", 1, "multiple",
              "Toque duplo na tela", "Gesto de deslizar o dedo na tela", "Pressionar e segurar", "Apertar o botão físico"),
             ("O que é um 'bottom navigation bar'?", "barra de navegacao na parte inferior do app", 1, "multiple",
              "Barra de notificações", "Barra de navegação na parte inferior do app", "Teclado virtual", "Menu de configurações"),
             ("Para que serve o 'splash screen'?", "tela inicial exibida enquanto o app carrega", 1, "multiple",
              "Tela de erro", "Tela inicial exibida enquanto o app carrega", "Tela de pagamento", "Tutorial do app"),
             ("O que é um 'drawer' (gaveta) em apps mobile?", "menu lateral que desliza da borda da tela", 2, "multiple",
              "Animação de loading", "Menu lateral que desliza da borda da tela", "Notificação push", "Formulário de cadastro"),
             ("Feedback tátil (vibração leve) ao tocar botões é um exemplo de...?", "haptic feedback", 2, "multiple",
              "Bug de hardware", "Haptic feedback", "Animação CSS", "Erro de sistema"),
         ]),

        (5, 4, "Publicação e Boas Práticas",
         "Publicar um app exige conta de desenvolvedor (Google Play ou App Store), preparar ícones, screenshots e descrição, e assinar o app digitalmente. Boas práticas incluem: tratamento de erros, permissões mínimas necessárias e respeito à privacidade do usuário.",
         [
             ("Onde são publicados apps Android?", "google play store", 1, "multiple",
              "App Store", "Google Play Store", "Microsoft Store", "Steam"),
             ("Onde são publicados apps iOS?", "apple app store", 1, "multiple",
              "Google Play", "Apple App Store", "Galaxy Store", "F-Droid"),
             ("Por que um app deve solicitar apenas as permissões necessárias?", "privacidade e seguranca do usuario", 2, "multiple",
              "Para ser mais rápido", "Para usar menos memória", "Privacidade e segurança do usuário", "Requisito técnico do hardware"),
             ("O que é assinar digitalmente um app?", "garantir que o app e autentico e nao foi alterado", 2, "multiple",
              "Adicionar o nome do desenvolvedor", "Garantir que o app é autêntico e não foi alterado", "Registrar copyright", "Comprimir o arquivo"),
             ("O que são 'notificações push'?", "mensagens enviadas pelo servidor ao app mesmo fechado", 2, "multiple",
              "Alertas de bateria fraca", "Mensagens enviadas pelo servidor ao app mesmo fechado", "Atualizações automáticas", "Backups automáticos"),
         ]),

        # ======= VERSIONAMENTO =======
        (6, 1, "Fundamentos do Git",
         "Git é um sistema de controle de versão distribuído criado por Linus Torvalds em 2005. Permite rastrear mudanças no código, trabalhar em equipe e reverter erros. Cada conjunto de mudanças salvo é chamado de 'commit'.",
         [
             ("Quem criou o Git?", "linus torvalds", 1, "multiple",
              "Bill Gates", "Linus Torvalds", "Mark Zuckerberg", "Guido van Rossum"),
             ("O que é um 'commit' no Git?", "registro de um conjunto de mudancas no codigo", 1, "multiple",
              "Um erro no código", "Registro de um conjunto de mudanças no código", "Uma branch nova", "Um repositório remoto"),
             ("Qual comando Git inicializa um repositório?", "git init", 1, "multiple",
              "git start", "git create", "git init", "git new"),
             ("Qual comando registra as mudanças no repositório local?", "git commit", 1, "multiple",
              "git push", "git save", "git commit", "git upload"),
             ("Qual comando envia commits locais para o repositório remoto?", "git push", 1, "multiple",
              "git send", "git upload", "git commit", "git push"),
         ]),

        (6, 2, "GitHub e Repositórios",
         "GitHub é uma plataforma de hospedagem de repositórios Git com recursos de colaboração: pull requests, issues, forks e actions. É o maior hub de código aberto do mundo. GitHub ≠ Git: Git é a ferramenta, GitHub é a plataforma.",
         [
             ("GitHub é a mesma coisa que Git?", "nao git e a ferramenta github e a plataforma", 1, "multiple",
              "Sim, são sinônimos", "Não, Git é a ferramenta; GitHub é a plataforma", "Sim, criados pela mesma empresa", "Não, são linguagens diferentes"),
             ("O que é um repositório no GitHub?", "pasta do projeto com historico de versoes", 1, "multiple",
              "Uma senha de acesso", "Pasta do projeto com histórico de versões", "Um servidor web", "Um banco de dados"),
             ("O que é um 'fork' no GitHub?", "copia de um repositorio para sua conta", 2, "multiple",
              "Um erro no código", "Um tipo de branch", "Cópia de um repositório para sua conta", "Uma solicitação de mudança"),
             ("O que é um 'Pull Request'?", "solicitacao para mesclar mudancas de uma branch", 2, "multiple",
              "Baixar o repositório", "Solicitação para mesclar mudanças de uma branch", "Apagar uma branch", "Criar um repositório"),
             ("O que são 'GitHub Actions'?", "pipelines de automacao de ci cd no github", 3, "multiple",
              "Animações do perfil", "Pipelines de automação de CI/CD no GitHub", "Extensões do navegador", "Plugins do VS Code"),
         ]),

        (6, 3, "Branches e Fluxo de Trabalho",
         "Branches permitem desenvolver funcionalidades isoladas sem afetar o código principal. O fluxo GitFlow usa branches padronizadas: main (produção), develop, feature/*, hotfix/*. Merge une branches; rebase reescreve o histórico.",
         [
             ("Para que serve uma branch?", "desenvolver funcionalidades isoladas sem afetar o principal", 1, "multiple",
              "Salvar o código em nuvem", "Desenvolver funcionalidades isoladas sem afetar o principal", "Apagar versões antigas", "Compartilhar código com outros"),
             ("Qual comando cria e muda para uma nova branch?", "git checkout -b", 2, "multiple",
              "git branch new", "git create branch", "git checkout -b", "git switch --create"),
             ("O que faz o 'git merge'?", "une o historico de duas branches", 2, "multiple",
              "Apaga uma branch", "Une o histórico de duas branches", "Envia código para o remoto", "Reverte um commit"),
             ("No GitFlow, qual branch contém o código em produção?", "main ou master", 2, "multiple",
              "develop", "feature", "hotfix", "main ou master"),
             ("O que é um 'merge conflict'?", "conflito quando duas branches alteram o mesmo trecho de codigo", 2, "multiple",
              "Erro de sintaxe no código", "Conflito quando duas branches alteram o mesmo trecho de código", "Falha de conexão com o GitHub", "Branch sem commits"),
         ]),

        (6, 4, "Boas Práticas de Versionamento",
         "Boas práticas incluem: commits pequenos e frequentes com mensagens claras, nunca commitar diretamente na main, usar .gitignore para ignorar arquivos desnecessários (node_modules, .env), e documentar o projeto com README.md.",
         [
             ("O que deve conter uma boa mensagem de commit?", "descricao clara do que foi alterado", 1, "multiple",
              "Apenas a data", "Descrição clara do que foi alterado", "Nome do programador", "Número de linhas alteradas"),
             ("Para que serve o arquivo .gitignore?", "especificar arquivos que o git nao deve rastrear", 2, "multiple",
              "Listar autores do projeto", "Especificar arquivos que o Git não deve rastrear", "Configurar o servidor", "Definir a branch principal"),
             ("Por que não se deve commitar o arquivo .env?", "ele contem senhas e segredos do projeto", 2, "multiple",
              "Porque é muito grande", "Ele contém senhas e segredos do projeto", "O Git não suporta esse formato", "Porque já é salvo automaticamente"),
             ("O que é um README.md?", "arquivo de documentacao principal do repositorio", 1, "multiple",
              "Arquivo de configuração do Git", "Arquivo de documentação principal do repositório", "Log de erros", "Lista de dependências"),
             ("Qual é a vantagem de commits pequenos e frequentes?", "facilita identificar onde um bug foi introduzido", 2, "multiple",
              "Ocupa menos espaço", "Facilita identificar onde um bug foi introduzido", "Evita merge conflicts", "Acelera o push"),
         ]),
    ]

    unit_id = 1
    for (trail_id, order_num, title, intro_text, questions) in data:
        cursor.execute(
            f"INSERT INTO units (id, trail_id, order_num, title, intro_text) VALUES ({p},{p},{p},{p},{p})",
            (unit_id, trail_id, order_num, title, intro_text)
        )
        for (q, a, diff, qtype, o1, o2, o3, o4) in questions:
            cursor.execute(
                f"""INSERT INTO questions (unit_id, question, answer, difficulty, type, opt1, opt2, opt3, opt4)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                (unit_id, q, a, diff, qtype, o1, o2, o3, o4)
            )
        unit_id += 1

    print(f"{unit_id - 1} unidades e {sum(len(q[4]) for q in data)} perguntas inseridas.")


if __name__ == "__main__":
    init_db()