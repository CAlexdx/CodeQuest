# 🚀 CodeQuest

CodeQuest é uma plataforma web gamificada de aprendizado em programação, inspirada em aplicativos como Duolingo e plataformas educacionais como Alura.

O sistema permite que usuários respondam perguntas, ganhem XP e evoluam de nível conforme avançam no aprendizado.

---

## 🎯 Objetivo

Criar uma plataforma interativa e progressiva para ensino de programação, utilizando conceitos de gamificação para aumentar o engajamento dos usuários.

---

## 🛠️ Tecnologias Utilizadas

- Python (Flask)
- SQLite
- HTML (Jinja2)
- CSS
- JavaScript (Fetch API)
- Gunicorn (produção)

---

## ⚙️ Funcionalidades

### 👤 Sistema de usuários
- Cadastro de conta
- Login com senha criptografada
- Sessão de usuário
- Logout

### 📈 Sistema de progresso
- +10 XP por resposta correta
- Sistema de níveis automático
- Exibição de progresso (XP atual / próximo nível)

### 🧠 Sistema de perguntas
- Perguntas baseadas no nível do usuário
- Sistema de dificuldade:
  - Fácil
  - Médio
  - Difícil
- Seleção eficiente (sem sobrecarga no servidor)

### ❓ Tipos de perguntas
- Resposta aberta (texto)
- Múltipla escolha (4 opções)

### ✅ Validação inteligente
- Ignora maiúsculas/minúsculas
- Ignora acentos
- Comparação segura de respostas

### 📊 Ranking
- Ranking global de usuários
- Ordenado por XP
- Top 10 jogadores

### 🧾 Histórico
- Registro das respostas do usuário
- Base para análise de desempenho

---

## 🧠 Sistema de níveis

O nível é definido pela fórmula:


nível = XP // 50


### Exemplo:
- 0–49 XP → nível 0  
- 50–99 XP → nível 1  
- 100–149 XP → nível 2  

---

## 🗂️ Estrutura do Projeto


CodeQuest/
│
├── app.py
├── init_db.py
├── database.db
├── README.md
│
├── templates/
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── profile.html
│ ├── ranking.html
│ ├── admin.html
│
└── static/
├── style.css
└── script.js


---

## 📂 Organização

### `templates/`
Arquivos HTML processados pelo Flask (Jinja2), responsáveis pela interface do usuário.

### `static/`
Arquivos estáticos enviados diretamente ao navegador:
- CSS (estilo)
- JavaScript (interatividade)

### Backend (`app.py`)
Responsável por:
- lógica do sistema  
- controle de rotas  
- autenticação  
- banco de dados  

---

## 🚀 Como rodar o projeto localmente

### 1. Clonar o repositório

git clone <seu-repositorio>
cd CodeQuest


### 2. Criar ambiente virtual (opcional)

**Windows**

python -m venv venv
venv\Scripts\activate


**Linux/Mac**

python3 -m venv venv
source venv/bin/activate


### 3. Instalar dependências

pip install flask


### 4. Executar o projeto

python app.py


O sistema irá automaticamente:
- criar o banco de dados  
- inserir perguntas iniciais  

### 5. Acessar no navegador

http://127.0.0.1:5000


---

## 🌐 Deploy no Render

### 📦 Dependências (`requirements.txt`)

flask
gunicorn


### ▶️ Comando de inicialização

gunicorn app:app


### ⚠️ Observação
O SQLite pode ser reiniciado no ambiente do Render.  
O sistema recria automaticamente o banco ao iniciar.

---

## ⚡ Otimizações

- Uso de `OFFSET` ao invés de `ORDER BY RANDOM()`
- Índices no banco de dados
- Conexões leves com SQLite
- Código preparado para baixo consumo de memória

---

## 🔮 Melhorias futuras

- Interface estilo Duolingo
- Feedback visual (cores e animações)
- Explicação das respostas
- Sistema de conquistas
- Progresso por categoria (Python, SQL, etc.)
- Perguntas com código formatado
- Migração para PostgreSQL
- Sistema de vidas

---

## 👨‍💻 Autores

Projeto desenvolvido por:

- Calebe Alves  
- Bruno  
- Gabriel Nilmar  
- Felipe Gustavo  
- Anderson Thiago  

Curso Técnico de Desenvolvimento de Sistemas

---

## 🏁 Conclusão

O CodeQuest demonstra a aplicação prática de conceitos de desenvolvimento web, banco de dados e lógica de programação, utilizando gamificação como estratégia para melhorar a experiência de aprendizado.
