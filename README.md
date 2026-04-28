# 🚀 CodeQuest

🔗 **Acesse o projeto online:**  
https://codequest-rntp.onrender.com

---

## 🎯 Sobre o Projeto

O **CodeQuest** é uma plataforma web gamificada de aprendizado em programação, inspirada em aplicativos como Duolingo e plataformas educacionais como Alura.

O sistema permite que usuários respondam perguntas, ganhem XP e evoluam de nível conforme avançam no aprendizado.

---

## 🧠 Objetivo

Criar uma plataforma interativa para ensino de programação, utilizando gamificação para aumentar o engajamento e facilitar o aprendizado.

---

## 🛠️ Tecnologias Utilizadas

- Python (Flask)
- PostgreSQL (Render)
- HTML (Jinja2)
- CSS
- JavaScript (Fetch API)
- Gunicorn (deploy)

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
- Exibição de progresso

### 🧠 Sistema de perguntas
- Perguntas baseadas no nível
- Sistema de dificuldade:
  - Fácil
  - Médio
  - Difícil

### ❓ Tipos de perguntas
- Resposta aberta
- Múltipla escolha
- Complete o código (cloze)
- Montagem de código (word bank)

### ✅ Validação inteligente
- Ignora maiúsculas/minúsculas
- Ignora acentos

### 📊 Ranking
- Ranking global por XP

### 🛠️ Painel Admin
- Visualizar usuários
- Ver XP
- Deletar usuários

---

## 🧠 Sistema de níveis


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
├── README.md
│
├── templates/
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── profile.html
│ ├── admin.html
│
└── static/
├── style.css
└── script.js


---

## 🚀 Como rodar localmente

```bash
git clone https://github.com/CAlexdx/CodeQuest.git
cd CodeQuest
pip install -r requirements.txt
python app.py

Acesse:

http://127.0.0.1:5000
🌐 Deploy

O projeto está hospedado no Render, utilizando:

Web Service (Flask + Gunicorn)
PostgreSQL (banco de dados persistente)
🔐 Segurança
Senhas criptografadas com werkzeug.security
Sessões protegidas
Acesso admin restrito
⚡ Otimizações
Seleção eficiente de perguntas
Código leve
Baixo consumo de recursos
🔮 Melhorias futuras
Interface estilo Duolingo
Feedback visual avançado
Sistema de conquistas
Progresso por categoria
Dashboard administrativo completo
Sistema de vidas
👨‍💻 Autores
Calebe Alves
Bruno
Gabriel Nilmar
Felipe Gustavo
Anderson Thiago

Curso Técnico em Desenvolvimento de Sistemas

🏁 Conclusão

O CodeQuest demonstra a aplicação prática de conceitos de desenvolvimento web, banco de dados e lógica de programação, utilizando gamificação para transformar o aprendizado em uma experiência interativa.