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
            trail_order INTEGER NOT NULL
        )
    """)

    # UNIDADES
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS units (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            trail_id INTEGER NOT NULL,
            unit_order INTEGER NOT NULL,
            title TEXT NOT NULL,
            intro_text TEXT NOT NULL
        )
    """)

    # PERGUNTAS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS questions (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            type TEXT NOT NULL DEFAULT 'multiple',
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT,
            unit_id INTEGER NOT NULL
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
    """)

    # RESPOSTAS CONCLUÍDAS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answered (
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL
        )
    """)

    # ADMIN PADRÃO
    cursor.execute(f"SELECT id FROM users WHERE username={p}", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            f"INSERT INTO users (username, password, is_admin) VALUES ({p},{p},{p})",
            ("admin", generate_password_hash("admin123"), True)
        )

    # POPULAR DADOS SE ESTIVER VAZIO
    cursor.execute("SELECT COUNT(*) FROM trails")
    if cursor.fetchone()[0] == 0:
        print("Inserindo trilhas, unidades e perguntas completas...")
        _insert_data(cursor, p)

    conn.commit()
    conn.close()
    print("--- Setup Finalizado com Sucesso ---")


def _insert_data(cursor, p):
    is_pg = (p == "%s")
    
    # =====================
    # 1. INSERÇÃO DAS TRILHAS
    # =====================
    trails = [
        (1, "Banco de Dados",       "🗄️",  "Fundamentos de MySQL, SQL, normalização e transações.",        "#3b82f6", 1),
        (2, "Inteligência Artificial","🤖", "IA fraca e forte, modelos generativos e ética.",                "#8b5cf6", 2),
        (3, "Back-End",              "⚙️",  "HTTP, APIs, Node.js, Python e servidores.",                     "#22c55e", 3),
        (4, "Front-End",             "🎨",  "HTML, CSS, JavaScript, React e Vue.",                           "#f97316", 4),
        (5, "Mobile",                "📱",  "Desenvolvimento de apps iOS e Android.",                        "#06b6d4", 5),
        (6, "Versionamento",         "🔧",  "Git, GitHub, branches e boas práticas.",                        "#f59e0b", 6),
    ]
    for t in trails:
        cursor.execute(
            f"INSERT INTO trails (id, name, icon, description, color, trail_order) VALUES ({p},{p},{p},{p},{p},{p})",
            t
        )

    # =====================
    # 2. ESTRUTURA COMPLETA DE DADOS (UNIDADES + PERGUNTAS)
    # =====================
    raw_data = [
        # ======= 1. BANCO DE DADOS =======
        (1, 1, "Introdução ao MySQL",
         "O MySQL é um sistema de gerenciamento de banco de dados relacional (SGBD) de código aberto. Ele usa SQL para criar, ler, atualizar e deletar dados.",
         [
             ("O que é o MySQL Server?", "Um sistema de gerenciamento de banco de dados", 1, "multiple", "Um sistema de gerenciamento de banco de dados", "Uma ferramenta de design gráfico", "Um sistema operacional", "Um editor de texto"),
             ("Para que serve o MySQL Workbench?", "Criar diagramas ER e gerenciar bancos de dados", 1, "multiple", "Navegar na web", "Criar diagramas ER e gerenciar bancos de dados", "Desenvolver aplicativos móveis", "Editar imagens"),
             ("Qual é a linguagem usada pelo MySQL para consultas?", "sql", 1, "open", "", "", "", ""),
             ("MySQL é um banco de dados do tipo...?", "Relacional", 1, "multiple", "Relacional", "Orientado a objetos", "Hierárquico", "Em grafos"),
             ("Complete o comando para selecionar dados: ___ * FROM users;", "select", 1, "cloze", "", "", "", ""),
         ]),

        (1, 2, "Relacionamentos entre Tabelas",
         "Relacionamentos definem como tabelas se conectam. No tipo um-para-muitos (1:N), uma chave estrangeira (FK) é utilizada para implementar essa conexão no banco.",
         [
             ("Como os registros da entidade 'Muitos' se relacionam com a 'Um'?", "Um registro em 'Muitos' tem um na entidade 'Um'", 1, "multiple", "Um registro em 'Muitos' não tem relação", "Um registro em 'Muitos' tem vários na 'Um'", "Um registro em 'Muitos' tem um na entidade 'Um'", "Um registro em 'Muitos' só se relaciona com outras tabelas"),
             ("O que melhor exemplifica um relacionamento um-para-muitos?", "Um cliente faz vários pedidos", 1, "multiple", "Um funcionário com vários empregadores", "Um produto tem vários fornecedores", "Um pedido feito por vários clientes", "Um cliente faz vários pedidos"),
             ("O que é uma chave estrangeira (FK)?", "Coluna que referencia a chave primária de outra tabela", 2, "multiple", "Coluna que referencia a chave primária de outra tabela", "Uma chave duplicada", "O índice principal da tabela", "Uma senha de acesso"),
             ("No relacionamento N:N, como ele é implementado no banco?", "Tabela intermediária", 2, "multiple", "Duas chaves primárias", "Tabela intermediária", "Chave estrangeira direta", "Não é possível implementar"),
             ("Qual símbolo representa 'muitos' na notação de Crow's Foot?", "Pé de galinha", 2, "multiple", "Traço único", "Círculo", "Pé de galinha", "Seta dupla"),
         ]),

        (1, 3, "Normalização",
         "Normalização é o processo de organizar tabelas para reduzir redundância e evitar inconsistências. As formas normais (1NF, 2NF, 3NF) são regras progressivas.",
         [
             ("Qual é o principal objetivo da normalização?", "Evitar anomalias como redundância e inconsistência", 2, "multiple", "Reduzir espaço ao máximo", "Melhorar consultas complexas", "Evitar anomalias como redundância e inconsistência", "Eliminar índices"),
             ("O que a 3NF elimina?", "Dependências transitivas", 2, "multiple", "Relacionamentos entre tabelas", "Dados atômicos", "Dependências parciais", "Dependências transitivas"),
             ("Para estar na 3NF, a tabela deve primeiro estar em qual forma?", "2nf", 2, "open", "", "", "", ""),
             ("Qual é uma vantagem do banco normalizado?", "Minimiza redundâncias e melhora a integridade", 2, "multiple", "Cria tabelas com muitos campos", "Reduz número de junções", "Elimina chaves estrangeiras", "Minimiza redundâncias e melhora a integridade"),
             ("A normalização divide tabelas. O processo inverso chama-se...?", "desnormalizacao", 2, "open", "", "", "", ""),
         ]),

        (1, 4, "SQL e DML",
         "SQL tem subconjuntos: DDL (CREATE, DROP), DML (INSERT, UPDATE, DELETE, SELECT) e DCL (GRANT, REVOKE).",
         [
             ("Qual dos seguintes é um comando DML?", "DELETE", 2, "multiple", "CREATE", "DELETE", "GRANT", "DROP"),
             ("O artigo de Edgar F. Codd, que originou o SQL, foi publicado em?", "1970", 2, "open", "", "", "", ""),
             ("Qual comando SQL recupera dados de uma tabela?", "SELECT", 1, "multiple", "INSERT", "UPDATE", "SELECT", "DELETE"),
             ("Qual comando cria uma nova tabela no banco?", "CREATE TABLE", 2, "multiple", "INSERT TABLE", "MAKE TABLE", "CREATE TABLE", "NEW TABLE"),
             ("O comando UPDATE serve para...?", "Modificar dados existentes", 2, "multiple", "Apagar registros", "Inserir novos dados", "Modificar dados existentes", "Criar colunas"),
         ]),

        (1, 5, "Transações ACID e Índices",
         "ACID garante confiabilidade: Atomicidade, Consistência, Isolamento e Durabilidade. Índices aceleram buscas mas aumentam o custo de escrita.",
         [
             ("Qual propriedade ACID garante que o banco sempre respeita suas regras após uma transação?", "Consistência", 3, "multiple", "Consistência", "Atomicidade", "Durabilidade", "Isolamento"),
             ("Quando um banco reverte operações após uma falha, qual propriedade ACID está sendo aplicada?", "Atomicidade", 3, "multiple", "Durabilidade", "Atomicidade", "Isolamento", "Consistência"),
             ("Qual comando confirma permanentemente as alterações de uma transação?", "commit", 2, "open", "", "", "", ""),
             ("Qual é o principal objetivo de criar um índice?", "Acelerar consultas na coluna indexada", 2, "multiple", "Reduzir tamanho da tabela", "Ordenar dados alfabeticamente", "Acelerar consultas na coluna indexada", "Garantir integridade referencial"),
             ("Qual é o principal efeito colateral de muitos índices?", "Degradação em operações de escrita", 3, "multiple", "Melhora todas as consultas", "Degradação em operações de escrita", "Impossibilidade de criar tabelas", "Reduz espaço em disco"),
         ]),

        # ======= 2. INTELIGÊNCIA ARTIFICIAL =======
        (2, 1, "O que é Inteligência Artificial?",
         "IA é a área da computação que cria sistemas capazes de realizar tarefas cognitivas humanas. Divide-se em IA Fraca (estreita) e IA Forte (geral).",
         [
             ("O ChatGPT é classificado como qual tipo de IA atualmente?", "IA Fraca ou Estreita", 1, "multiple", "IA Forte", "IA Fraca ou Estreita", "IA Consciente", "IA Generalista"),
             ("O ChatGPT é classificado como qual tipo de IA em relação a histórico?", "IA com memória limitada", 2, "multiple", "IA com memória limitada", "IA com teoria da mente completa", "IA autoconsciente", "Máquina puramente reativa"),
             ("Qual é a diferença entre IA discriminativa e IA generativa?", "A discriminativa classifica; a generativa cria dados novos", 2, "multiple", "A discriminativa é mais moderna", "A generativa só usa imagens", "A discriminativa classifica; a generativa cria dados novos", "Não há diferença real"),
             ("Qual teste clássico avalia se uma máquina exibe comportamento inteligente?", "teste de turing", 1, "open", "", "", "", ""),
             ("Complete a sigla de Large Language Models: ___", "llm", 2, "cloze", "", "", "", ""),
         ]),

        (2, 2, "Tipos de IA e Aplicações",
         "Sistemas modernos geram recomendações, diagnósticos e automações baseados em dados, porém podem herdar vieses históricos do treinamento.",
         [
             ("Por que o Spotify recomenda músicas de artistas que você nunca ouviu?", "Porque analisa e compara padrões de gosto musical", 1, "multiple", "Porque grava conversas", "Porque os artistas pagam", "Porque analisa e compara padrões de gosto musical", "Porque é aleatório"),
             ("Carros autônomos que usam dados de viagens anteriores são classificados como IA de...?", "Memória limitada", 2, "multiple", "Memória limitada", "Teoria da mente", "IA reativa", "IA forte"),
             ("Qual é a principal causa de vieses em sistemas de IA?", "Dados de treinamento que refletem preconceitos históricos", 2, "multiple", "Bugs no código", "Falta de capacidade", "Dados de treinamento que refletem preconceitos históricos", "Má intenção"),
             ("Em decisões de alto impacto social, qual deve ser o papel ideal da IA?", "Servir como ferramenta de apoio com humanos decidindo", 2, "multiple", "Substituir decisões", "Decidir autonomamente", "Servir como ferramenta de apoio com humanos decidindo", "Não ser usada"),
             ("Um sistema que apenas filtra e-mails sem guardar histórico é uma IA...?", "reativa", 2, "open", "", "", "", ""),
         ]),

        (2, 3, "História da IA",
         "A história da IA possui ciclos de otimismo e 'invernos' devido a limitações técnicas. O boom moderno iniciou com o Deep Learning.",
         [
             ("Qual foi o principal motivo dos 'Invernos da IA'?", "Expectativas irreais contra limitações técnicas", 2, "multiple", "Falta de cientistas", "Expectativas irreais contra limitações técnicas", "Proibição governamental", "Competição"),
             ("Qual fator impulsionou o boom recente da IA?", "Big data, GPUs e deep learning", 2, "multiple", "Leis governamentais", "Big data, GPUs e deep learning", "Redução do custo de energia", "Aumento de programadores"),
             ("Em que ano Alan Turing propôs o famoso teste?", "1950", 2, "open", "", "", "", ""),
             ("O computador Deep Blue ficou famoso por vencer o campeão mundial de...?", "xadrez", 1, "open", "", "", "", ""),
             ("Ordene o termo correspondente a aprendizado profundo: [deep] [learning]", "deep learning", 1, "wordbank", "deep", "learning", "", ""),
         ]),

        (2, 4, "IA Generativa e Modelos",
         "Modelos Generativos include GANs (redes adversárias), VAEs (autoencoders variacionais) e Transformers (focados em atenção textual).",
         [
             ("Uma empresa quer gerar logos com controle fino de variações. Qual modelo é ideal?", "VAE – pelo controle fino das variações", 3, "multiple", "VAE – pelo controle fino das variações", "Transformer", "GAN – pela qualidade fotorrealista", "BERT"),
             ("O site ThisPersonDoesNotExist usa StyleGAN. Qual a arquitetura base?", "gan", 2, "open", "", "", "", ""),
             ("O que significa a sigla GAN?", "Redes Adversárias Generativas", 3, "multiple", "Redes Adversárias Generativas", "Rede Alternada Neural", "Gráfico Aberto Neural", "Garantia de Atenção Nova"),
             ("A arquitetura base de modelos de linguagem como GPT chama-se...?", "transformer", 3, "open", "", "", "", ""),
             ("Complete: Redes Neurais Artificiais tentam imitar o funcionamento dos ___ humanos.", "neuronios", 1, "cloze", "", "", "", ""),
         ]),

        (2, 5, "Ética em IA",
         "O avanço traz debates éticos sobre Deepfakes, privacidade de dados e regulamentações como o AI Act da União Europeia.",
         [
             ("O que é um deepfake?", "Mídia manipulada com IA para substituir rostos ou vozes", 2, "multiple", "Mídia manipulada com IA para substituir rostos ou vozes", "Um vírus", "Uma compressão", "Um filtro"),
             ("Qual lei europeia regula o uso de IA por nível de risco?", "ai act", 3, "open", "", "", "", ""),
             ("Por que sistemas faciais falham mais em minorias?", "Treinados com dados majoritariamente de pessoas brancas", 2, "multiple", "Problema de iluminação", "Treinados com dados majoritariamente de pessoas brancas", "Algoritmo incorreto", "Câmeras ruins"),
             ("O termo 'explainability' refere-se à capacidade de...?", "Entender como a IA chegou a uma decisão", 3, "multiple", "Entender como a IA chegou a uma decisão", "Velocidade da IA", "Custo de treino", "Tamanho do modelo"),
             ("Decisões judiciais por IA geram risco de reproduzir preconceitos ___", "historicos", 2, "cloze", "", "", "", ""),
         ]),

        # ======= 3. BACK-END =======
        (3, 1, "Fundamentos de Back-End",
         "O Back-End gerencia as regras de negócio, segurança e comunicação com bancos de dados a partir de um servidor remoto.",
         [
             ("Qual é a principal função do servidor web?", "Receber e responder requisições HTTP", 1, "multiple", "Interface gráfica", "Receber e responder requisições HTTP", "Plugins visuais", "Design front-end"),
             ("O que é Back-End?", "Parte do sistema que roda no servidor", 1, "multiple", "A interface visual", "Parte do sistema que roda no servidor", "O banco de dados somente", "O design"),
             ("Qual linguagem é usada nativamente com o framework Flask?", "python", 1, "open", "", "", "", ""),
             ("Qual porta padrão o protocolo HTTP usa?", "80", 2, "open", "", "", "", ""),
             ("A porta padrão segura HTTPS é a...?", "443", 2, "open", "", "", "", ""),
         ]),

        (3, 2, "HTTP e APIs",
         "O protocolo HTTP trafega verbos comuns (GET, POST, PUT, DELETE) para realizar as operações de CRUD nas APIs REST.",
         [
             ("Qual método HTTP busca dados sem alterá-los?", "GET", 1, "multiple", "POST", "DELETE", "GET", "PUT"),
             ("Qual método HTTP cria um novo recurso no servidor?", "POST", 1, "multiple", "GET", "POST", "PUT", "PATCH"),
             ("O que é uma API REST?", "Interface que usa HTTP para comunicação entre sistemas", 2, "multiple", "Um banco de dados", "Interface que usa HTTP para comunicação entre sistemas", "Um servidor web", "Uma linguagem"),
             ("Qual código HTTP indica que um recurso não foi encontrado?", "404", 2, "open", "", "", "", ""),
             ("Qual formato estruturado em chaves e valores é o mais usado em APIs modernas?", "json", 1, "open", "", "", "", ""),
         ]),

        (3, 3, "Bancos de Dados no Back-End",
         "Sistemas interagem com bancos SQL ou NoSQL (como MongoDB). Ferramentas ORM traduzem tabelas em objetos de código.",
         [
             ("O que é um ORM?", "Ferramenta que mapeia objetos para tabelas do banco", 2, "multiple", "Um banco de dados", "Ferramenta que mapeia objetos para tabelas do banco", "Uma linguagem", "Um servidor"),
             ("Qual banco NoSQL armazena dados em documentos similares a JSON?", "MongoDB", 2, "multiple", "MySQL", "PostgreSQL", "MongoDB", "SQLite"),
             ("O SQLite armazena o banco inteiro em um único...?", "arquivo", 1, "open", "", "", "", ""),
             ("Injeção de código malicioso em inputs para quebrar o banco chama-se SQL ___", "injection", 2, "cloze", "", "", "", ""),
             ("Qual propriedade protege o banco contra SQL Injection?", "Parametrização", 3, "multiple", "Parametrização", "Deleção", "Criptografia", "Indexação"),
         ]),

        (3, 4, "Node.js",
         "Node.js executa JavaScript no lado do servidor utilizando a arquitetura V8, sendo assíncrono e orientado a eventos.",
         [
             ("O que é Node.js?", "Ambiente de execução de JavaScript no servidor", 2, "multiple", "Um banco de dados", "Um navegador", "Ambiente de execução de JavaScript no servidor", "Uma linguagem"),
             ("Qual é o gerenciador de pacotes padrão do Node.js?", "npm", 1, "open", "", "", "", ""),
             ("Node.js destaca-se por ser assíncrono e não-___", "bloqueante", 2, "cloze", "", "", "", ""),
             ("Qual framework minimalista de rotas é o mais famoso no ecossistema Node?", "Express", 2, "multiple", "Django", "Flask", "Express", "Spring"),
             ("Complete o comando de importação moderno: import express ___ 'express';", "from", 1, "cloze", "", "", "", ""),
         ]),

        (3, 5, "Python no Back-End",
         "Python brilha no Back-end com Flask (microframework maleável) e Django (framework robusto 'batteries-included').",
         [
             ("Qual framework Python é robusto e traz ORM e painel Admin nativos?", "Django", 2, "multiple", "Flask", "FastAPI", "Django", "Express"),
             ("Como Python delimita blocos de escopo de código?", "identacao", 1, "open", "", "", "", ""),
             ("Qual gerenciador de pacotes baixa bibliotecas no ecossistema Python?", "pip", 1, "open", "", "", "", ""),
             ("Qual decorador Flask vincula uma rota a uma função?", "@app.route", 2, "multiple", "@app.url", "@route.path", "@app.route", "@flask.path"),
             ("Ordene o comando para instalar o Flask via terminal: [pip] [install] [flask]", "pip install flask", 1, "wordbank", "pip", "install", "flask", ""),
         ]),

        # ======= 4. FRONT-END =======
        (4, 1, "HTML e CSS",
         "A fundação das páginas web consiste na marcação estrutural do HTML e nas regras de renderização em cascata do CSS.",
         [
             ("Qual tag HTML cria um parágrafo de texto?", "p", 1, "multiple", "div", "p", "span", "h1"),
             ("Qual propriedade CSS altera a cor do fundo de um elemento?", "background-color", 1, "multiple", "color", "background-color", "border-color", "font-color"),
             ("Para selecionar elementos de uma ID no CSS, usamos o caractere...?", "#", 1, "open", "", "", "", ""),
             ("Qual propriedade CSS adiciona espaçamento externo?", "margin", 1, "multiple", "margin", "padding", "border", "display"),
             ("Complete a tag de link estrutural: <a ___=\"url\">Texto</a>", "href", 1, "cloze", "", "", "", ""),
         ]),

        (4, 2, "Interfaces e Usabilidade",
         "UI foca no aspecto estético da tela, enquanto UX estuda os fluxos de usabilidade e a responsividade em múltiplas telas.",
         [
             ("O que significa a sigla UX?", "User Experience", 1, "multiple", "User Execution", "User Experience", "Universal Exchange", "Unified Experience"),
             ("Uma interface responsiva altera sua estrutura baseado no quê?", "Tamanho da tela", 1, "multiple", "Idioma", "Tamanho da tela", "Sistema Operacional", "Velocidade"),
             ("O atributo 'alt' em imagens é fundamental para garantir a...?", "acessibilidade", 2, "open", "", "", "", ""),
             ("Qual modelo CSS organiza itens facilmente de forma unidimensional?", "Flexbox", 2, "multiple", "Float", "Position", "Flexbox", "Block"),
             ("Para layouts de duas dimensões em linhas e colunas fixas, usamos o CSS ___", "grid", 2, "cloze", "", "", "", ""),
         ]),

        (4, 3, "JavaScript",
         "JavaScript traz dinamismo ao cliente manipulando a estrutura DOM de acordo com cliques e requisições assíncronas.",
         [
             ("Qual método exibe alertas ou mensagens de debug no painel de desenvolvedor?", "console.log()", 1, "multiple", "print()", "console.log()", "alert.show()", "log.print()"),
             ("O acrônimo DOM significa Document ___ Object Model.", "object", 2, "cloze", "", "", "", ""),
             ("Qual API nativa do JS realiza requisições HTTP assíncronas de forma moderna?", "fetch", 2, "open", "", "", "", ""),
             ("Como declarar variáveis cujo escopo é de bloco mas aceita reatribuição?", "let", 1, "multiple", "var", "let", "const", "global"),
             ("Para travar o valor de uma variável impedindo reatribuição, usamos ___", "const", 1, "cloze", "", "", "", ""),
         ]),

        (4, 4, "React",
         "React quebra páginas em componentes reativos gerenciados via Hooks de ciclo de vida e estado como useState.",
         [
             ("React baseia-se em qual empresa mantenedora?", "Meta", 2, "multiple", "Google", "Microsoft", "Meta", "Apple"),
             ("Dados imutáveis passados de um componente pai para um componente filho chamam-se...?", "props", 2, "open", "", "", "", ""),
             ("Qual Hook do React serve para criar estados dinâmicos locais?", "useState", 2, "multiple", "useEffect", "useContext", "useState", "useRef"),
             ("O React usa uma cópia otimizada em memória do DOM real chamada...?", "virtual dom", 3, "open", "", "", "", ""),
             ("A mistura sintática de HTML dentro do código JavaScript chama-se...?", "jsx", 2, "open", "", "", "", ""),
         ]),

        (4, 5, "Vue.js e Build Tools",
         "Vue.js é um framework progressivo. Ferramentas de build modernas como o Vite empacotam o ecossistema com performance.",
         [
             ("No Vue 3, qual função do pacote nativo cria uma aplicação?", "createapp", 2, "open", "", "", "", ""),
             ("Complete a diretiva de renderização condicional do Vue: v-___=\"condicao\"", "if", 1, "cloze", "", "", "", ""),
             ("Qual ferramenta moderna de build substitui o Webpack em novos apps?", "Vite", 2, "multiple", "Vite", "Webpack", "Babel", "Gulp"),
             ("Qual diretiva do Vue realiza o data binding bidirecional em inputs?", "v-model", 2, "open", "", "", "", ""),
             ("Ordene a estrutura de condicional reversa do Vue: [v-else]", "v-else", 1, "wordbank", "v-else", "", "", ""),
         ]),

        # ======= 5. MOBILE =======
        (5, 1, "Introdução ao Mobile",
         "O desenvolvimento de aplicativos móveis divide-se em desenvolvimento nativo e multiplataforma.",
         [
             ("Qual framework multiplataforma utiliza a linguagem Dart?", "Flutter", 1, "multiple", "Flutter", "React Native", "Cordova", "Xamarin"),
             ("React Native executa código mobile baseado em qual linguagem mãe?", "JavaScript", 1, "multiple", "Java", "JavaScript", "Swift", "Kotlin"),
             ("Qual linguagem substituiu o Java como oficial recomendada pela Google para Android?", "kotlin", 2, "open", "", "", "", ""),
             ("Para criar aplicativos nativos de iOS da Apple, qual linguagem é usada?", "swift", 2, "open", "", "", "", ""),
             ("Complete: Aplicativos compilados direto para a linguagem do processador são chamados de ___.", "nativos", 1, "cloze", "", "", "", ""),
         ]),

        (5, 2, "Componentes e Layouts",
         "No desenvolvimento móvel, tags HTML não existem. Usamos componentes nativos ou equivalentes abstratos ajustados por Flexbox.",
         [
             ("Qual componente do React Native equivale estruturalmente à tag <div>?", "View", 1, "multiple", "View", "Text", "Div", "Scroll"),
             ("Complete o componente utilizado para exibir textos no React Native: <___>Texto</___>", "text", 1, "cloze", "", "", "", ""),
             ("Qual propriedade alinha elementos no eixo principal do Flexbox?", "justifycontent", 2, "open", "", "", "", ""),
             ("Por padrão, qual a direção padrão (flexDirection) no React Native?", "column", 2, "multiple", "row", "column", "row-reverse", "column-reverse"),
             ("Qual componente adiciona barras de rolagem em telas compridas no React Native?", "scrollview", 2, "open", "", "", "", ""),
         ]),

        (5, 3, "Navegação e Estado",
         "Aplicativos móveis guiam telas empilhando fluxos (Stack), chaveando abas inferiores (Tabs) ou gavetas laterais (Drawer).",
         [
             ("Qual navegação empilha telas permitindo que o usuário 'volte' deslizando?", "Stack", 2, "multiple", "Stack", "Tabs", "Drawer", "Switch"),
             ("Menus que deslizam a partir das laterais da tela chamam-se...?", "Drawer", 2, "multiple", "Tab", "Stack", "Drawer", "Modal"),
             ("Botões com efeitos visuais de opacidade ao clique usam o componente Touchable___", "opacity", 1, "cloze", "", "", "", ""),
             ("Qual biblioteca é o padrão de facto para navegação no React Native?", "react navigation", 2, "open", "", "", "", ""),
             ("Complete: Abas inferiores fixas usam a estratégia de Bottom ___ Navigation.", "tab", 2, "cloze", "", "", "", ""),
         ]),

        (5, 4, "APIs e Persistência",
         "Dispositivos móveis salvam dados locais simples de forma chave-valor ou gerenciam estados complexos assíncronos.",
         [
             ("Qual módulo guarda pequenos dados chave-valor locais de forma assíncrona?", "AsyncStorage", 2, "multiple", "AsyncStorage", "Redux", "MySQL", "Fetch"),
             ("Para buscar dados de APIs externas em segundo plano, usamos funções ___", "async", 2, "cloze", "", "", "", ""),
             ("Qual banco de dados local embarcado e leve (NoSQL) é muito usado em mobile?", "realm", 3, "open", "", "", "", ""),
             ("O AsyncStorage grava dados diretamente em formato de texto. Para objetos usamos JSON.___", "stringify", 2, "cloze", "", "", "", ""),
             ("Para reverter o texto do banco local em objeto JS, usamos o método JSON.___", "parse", 2, "cloze", "", "", "", ""),
         ]),

        (5, 5, "Compilação e Publicação",
         "Para distribuir o app, geramos pacotes assinados e submetemos às diretrizes rigorosas das lojas oficiais.",
         [
             ("Qual formato moderno (.aab) substituiu o .apk para novos envios na Google Play?", "AAB", 3, "multiple", "APK", "AAB", "IPA", "EXE"),
             ("Qual o formato de arquivo final gerado para instalar aplicativos no iOS?", "ipa", 3, "open", "", "", "", ""),
             ("A loja oficial de aplicativos de dispositivos Apple chama-se App...?", "store", 1, "open", "", "", "", ""),
             ("A plataforma web para submeter e gerenciar apps Android chama-se Google Play ___", "console", 2, "cloze", "", "", "", ""),
             ("Ordene o termo referente a testes internos antes de lançar: [beta] [test]", "beta test", 2, "wordbank", "beta", "test", "", ""),
         ]),

        # ======= 6. VERSIONAMENTO =======
        (6, 1, "Introdução ao Git",
         "O Git é um sistema de controle de versão distribuído que rastreia modificações no código de forma histórica e segura.",
         [
             ("Qual comando cria e inicializa um repositório Git local vazio?", "git init", 1, "multiple", "git init", "git start", "git clone", "git create"),
             ("O Git é classificado como um sistema de controle de versão do tipo...?", "Distribuído", 2, "multiple", "Centralizado", "Distribuído", "Local", "Monolítico"),
             ("Quem criou o Git original em 2005?", "linus torvalds", 3, "open", "", "", "", ""),
             ("Complete: O local temporário onde arquivos aguardam o commit chama-se Staging ___", "area", 1, "cloze", "", "", "", ""),
             ("Qual comando Git lista arquivos modificados que ainda não foram salvos?", "git status", 1, "open", "", "", "", ""),
         ]),

        (6, 2, "Rastreamento e Commits",
         "Commits consolidam alterações locais de forma definitiva na árvore histórica através de mensagens descritivas.",
         [
             ("Qual comando indexa absolutamente todas as alterações da pasta atual?", "git add .", 1, "multiple", "git add .", "git commit", "git push", "git save"),
             ("Ordene os blocos para formar um commit com mensagem padrão: [git] [commit] [-m] ['mensagem']", "git commit -m 'mensagem'", 1, "wordbank", "git", "commit", "-m", "'mensagem'"),
             ("Qual parâmetro do comando git commit define a mensagem curta?", "-m", 1, "open", "", "", "", ""),
             ("Para visualizar o histórico cronológico de commits feitos, usamos git ___", "log", 1, "cloze", "", "", "", ""),
             ("Um commit gera um identificador único alfanumérico longo baseado em algoritmo chamado...?", "hash", 2, "open", "", "", "", ""),
         ]),

        (6, 3, "Branches e Fusões",
         "Branches isolam frentes de trabalho. Ao finalizar uma tarefa, mesclamos o código de volta à linha de produção principal.",
         [
             ("Qual comando unificado cria e altera imediatamente para uma nova branch?", "git checkout -b", 2, "multiple", "git branch", "git checkout -b", "git merge", "git switch"),
             ("Para fundir e trazer alterações de outra branch para a sua atual, usamos git ___", "merge", 2, "cloze", "", "", "", ""),
             ("Como chama-se a branch principal padrão criada por omissão em novos repositórios?", "main", 1, "open", "", "", "", ""),
             ("Qual comando apenas lista as ramificações locais existentes?", "git branch", 1, "multiple", "git branch", "git checkout", "git status", "git log"),
             ("A estratégia alternativa ao merge que reescreve o histórico de commits linearmente chama-se...?", "rebase", 3, "open", "", "", "", ""),
         ]),

        (6, 4, "Git Remoto e GitHub",
         "Plataformas em nuvem como o GitHub guardam repositórios remotos para sincronizar códigos entre membros da equipe.",
         [
             ("Qual comando empurra seus commits locais salvos para o servidor remoto configurado?", "git push", 1, "multiple", "git push", "git pull", "git fetch", "git clone"),
             ("Qual comando baixa e mescla diretamente as atualizações do servidor remoto na sua máquina?", "git pull", 1, "multiple", "git push", "git pull", "git fetch", "git clone"),
             ("Para baixar e copiar um repositório remoto inteiro pela primeira vez para seu PC, usamos git ___", "clone", 1, "cloze", "", "", "", ""),
             ("Qual o nome padrão atribuído ao apelido do repositório remoto principal?", "origin", 2, "open", "", "", "", ""),
             ("Uma solicitação formal para fundir seu código no repositório de terceiros chama-se Pull ___", "request", 2, "cloze", "", "", "", ""),
         ]),

        (6, 5, "Conflitos e Boas Práticas",
         "Conflitos acontecem quando alterações concorrentes afetam as mesmas linhas. Devem ser resolvidos manualmente pelo dev.",
         [
             ("O que acarreta um Conflito (Conflict) no Git?", "Alterações na mesma linha do mesmo arquivo por pessoas diferentes", 2, "multiple", "Falta de internet", "Alterações na mesma linha do mesmo arquivo por pessoas diferentes", "Mudar branch", "Commit rápido"),
             ("Mensagens de commit eficientes e profissionais devem ser curtas e ___", "claras", 1, "cloze", "", "", "", ""),
             ("Qual arquivo oculto configurado na raiz instrui o Git a ignorar pastas como node_modules/ ou venv/?", ".gitignore", 2, "open", "", "", "", ""),
             ("Qual comando limpa arquivos temporários não rastreados do diretório de trabalho?", "git clean", 3, "multiple", "git clean", "git reset", "git revert", "git rm"),
             ("Para salvar modificações incompletas provisoriamente sem comitar, usamos o comando git ___", "stash", 3, "open", "", "", "", ""),
         ]),
    ]

    # =====================
    # 3. LAÇO DE INSERÇÃO DINÂMICA
    # =====================
    for trail_id, unit_order, title, intro_text, questions_list in raw_data:
        if is_pg:
            cursor.execute(
                f"INSERT INTO units (trail_id, unit_order, title, intro_text) VALUES ({p}, {p}, {p}, {p}) RETURNING id",
                (trail_id, unit_order, title, intro_text)
            )
            unit_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                f"INSERT INTO units (trail_id, unit_order, title, intro_text) VALUES ({p}, {p}, {p}, {p})",
                (trail_id, unit_order, title, intro_text)
            )
            unit_id = cursor.lastrowid

        for q in questions_list:
            cursor.execute(
                f"""INSERT INTO questions 
                    (question, answer, difficulty, type, opt1, opt2, opt3, opt4, unit_id) 
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})""",
                (q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], unit_id)
            )

    total_unidades = len(raw_data)
    total_perguntas = sum(len(u[4]) for u in raw_data)
    print(f"{total_unidades} unidades e {total_perguntas} perguntas inseridas com sucesso.")


if __name__ == "__main__":
    init_db()