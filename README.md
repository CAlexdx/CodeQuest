# CodeQuest

CodeQuest é uma plataforma web gamificada de perguntas e respostas para aprendizado, inspirada em aplicativos como Duolingo e plataformas de quiz.

O objetivo do projeto é permitir que usuários respondam perguntas e ganhem XP ao acertar, tornando o aprendizado mais interativo.

---

# Tecnologias utilizadas

* Python
* Flask
* SQLite
* HTML
* CSS
* JavaScript
* Fetch API

---

# Estrutura do projeto

```
CodeQuest/
│
├── app.py
├── init_db.py
├── database.db
├── requirements.txt
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
```

---

# Como rodar o projeto

## 1 Criar ambiente virtual (opcional mas recomendado)

Windows:

```
python -m venv venv
venv\Scripts\activate
```

Linux / Mac:

```
python3 -m venv venv
source venv/bin/activate
```

---

## 2 Instalar dependências

```
pip install flask
```

ou

```
pip install -r requirements.txt
```

---

## 3 Criar banco de dados

Execute o arquivo responsável por criar a tabela e inserir perguntas iniciais:

```
python init_db.py
```

Isso criará o arquivo:

```
database.db
```

---

## 4 Rodar o servidor

```
python app.py
```

O servidor iniciará em:

```
http://127.0.0.1:5000
```

Abra no navegador para usar o sistema.

---

# Como funciona o sistema

1. O backend em Flask busca uma pergunta aleatória no banco SQLite.
2. A pergunta é exibida na interface web.
3. O usuário digita a resposta.
4. O JavaScript envia a resposta para o backend usando Fetch API.
5. O servidor verifica se a resposta está correta.
6. O sistema retorna:

* correct → resposta correta
* wrong → resposta incorreta

7. A página mostra o resultado e carrega uma nova pergunta.

---

# Banco de dados

Tabela: `questions`

Campos:

```
id
question
answer
```

Exemplo de perguntas:

* Quanto é 2 + 2?
* Capital do Brasil?
* Quanto é 10 / 2?

---

# Funcionalidades atuais

* Perguntas aleatórias
* Verificação de resposta
* Interface web simples
* Comunicação frontend/backend com Fetch API

---

# Funcionalidades planejadas

* Sistema de XP
* Ranking de usuários
* Login e cadastro
* Perguntas de programação
* Questões de múltipla escolha
* Sistema de níveis
* Progresso de aprendizado

---

# Autor

Projeto desenvolvido por Calebe Alves.

Curso técnico de Desenvolvimento de Sistemas.
