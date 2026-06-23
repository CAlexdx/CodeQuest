# CodeQuest

 **Acesse o projeto online:** https://codequest-rntp.onrender.com

---

## Sobre o Projeto

O **CodeQuest** evoluiu para um **LMS (Learning Management System) Gamificado** para ensino de programação. Fortemente inspirado em plataformas como Duolingo, ele transforma o aprendizado em uma jornada interativa e viciante.

Através de um sistema estruturado em **Trilhas e Unidades**, o usuário consome conteúdo, resolve desafios práticos de código, mantém ofensivas diárias (Streaks) e compete no ranking global para testar seus conhecimentos.

---

## Tecnologias Utilizadas

* **Back-end:** Python (Flask)
* **Banco de Dados:** PostgreSQL (Produção no Render) / SQLite (Desenvolvimento Local)
* **Front-end:** HTML5 (Jinja2), CSS3, JavaScript (Fetch API para validações assíncronas)
* **Segurança:** Werkzeug Security (Hashes de senha)
* **Deploy:** Render (Gunicorn)

---

## Funcionalidades Principais

### Trilhas de Aprendizagem
* **Árvore de Conhecimento:** Conteúdo dividido em Trilhas, que contêm Unidades.
* **Mapa Interativo:** Interface em zigue-zague mostrando o caminho do usuário.
* **Bloqueio Inteligente:** Novas unidades só são liberadas quando a anterior for concluída.
* **Barra de Progresso:** Cálculo em tempo real da porcentagem de conclusão da trilha.

### Sistema de Gamificação
* **Níveis:** Progressão automática a cada 50 XP.
* **Ofensiva (Streak 🔥):** Contador de dias consecutivos de atividade para incentivar o retorno diário.
* **Recompensas:** +10 XP por cada resposta correta.
* **🏆 Ranking Global:** Tabela com os Top 10 usuários com mais XP, com distribuição automática de medalhas (🥇, 🥈, 🥉).

### Tipos de Desafios

| Tipo | Descrição |
| :--- | :--- |
| **Múltipla Escolha** | O usuário seleciona a resposta correta entre 4 opções. |
| **Texto (Aberta)** | Resposta digitada livremente pelo usuário. |
| **Cloze (Lacunas)** | Completar o código faltando trechos específicos. |
| **Wordbank** | Montagem de código selecionando blocos/palavras na ordem certa. |

*Nota: O sistema de validação ignora letras maiúsculas/minúsculas e acentuação para não penalizar erros de digitação simples.*

### Segurança e Administração
* **Cadastro Restrito:** Validação de caracteres e limite de tamanho para login e senha.
* **Painel Admin:** Controle total de usuários (Edição de XP, Conceder privilégios de Admin, Exclusão em cascata segura).
* **Prevenção de Cheats:** Validações server-side para evitar que usuários burlem o ganho de XP.

---

## Sistema de Progressão

A matemática por trás dos níveis do usuário:
`nível = XP // 50`

**Exemplo de Evolução:**
* **0–49 XP** → Nível 0  
* **50–99 XP** → Nível 1  
* **100–149 XP** → Nível 2  

---

## Estrutura do Projeto


CodeQuest/
│
├── app.py                  # Lógica principal, rotas e regras de negócio
├── init_db.py              # Script de inicialização e popularização do banco
├── database.db             # Banco de dados local (SQLite)
├── requirements.txt        # Dependências do projeto
├── README.md               # Documentação
├── .gitignore              # Arquivos ignorados pelo Git
│
├── templates/              # Interfaces HTML (Jinja2)
│   ├── index.html          # Dashboard inicial
│   ├── login.html          # Tela de login
│   ├── register.html       # Tela de cadastro
│   ├── profile.html        # Perfil e barra de progresso do nível
│   ├── admin.html          # Painel de controle para administradores
│   ├── ranking.html        # Ranking Global (Top 10)
│   ├── trilhas.html        # Seleção de trilhas disponíveis
│   ├── trilha_detail.html  # Mapa de unidades da trilha selecionada
│   └── unidade.html        # Interface de gameplay e perguntas
│
└── static/                 # Arquivos estáticos
    ├── style.css           # Estilização global e responsividade
    ├── script.js           # Lógica front-end (Wordbank, requisições de resposta)
    ├── logo1.png           # Logo principal
    └── logo2.png           # Ícone/Favicon

```

---

## Como rodar localmente

1. Clone o repositório:

git clone [https://github.com/CAlexdx/CodeQuest.git](https://github.com/CAlexdx/CodeQuest.git)
cd CodeQuest




2. **Instale as dependências:**

pip install -r requirements.txt




3. **Inicie o banco de dados e o servidor:**

python app.py




4. **Acesse no navegador:**
Abra `http://127.0.0.1:5000`

---

## Autores

* **Calebe Alves**
* **Bruno**
* **Gabriel Nilmar**
* **Felipe Gustavo**
* **Anderson Thiago**

**Curso Técnico em Desenvolvimento de Sistemas**

---

*CodeQuest - Transformando o aprendizado de programação em uma verdadeira aventura.*
