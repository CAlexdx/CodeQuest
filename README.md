Perfeito — vou te mandar um **README completo atualizado**, já refletindo tudo que você construiu até agora (login, XP, níveis, múltipla escolha, etc.), pronto pra colar no GitHub.

---

# README.md (COMPLETO – SUBSTITUA TUDO)

```md
# CodeQuest

CodeQuest é uma plataforma web gamificada de aprendizado em programação, inspirada em aplicativos como Duolingo e plataformas educacionais como Alura.

O sistema permite que usuários respondam perguntas relacionadas a desenvolvimento de sistemas e ganhem XP, evoluindo de nível conforme avançam.

---

# Tecnologias utilizadas

- Python (Flask)
- SQLite
- HTML
- CSS
- JavaScript (Fetch API)

---

# Funcionalidades atuais

## Sistema de usuários
- Cadastro de conta
- Login com senha criptografada
- Sessão de usuário
- Logout

## Sistema de progresso
- XP por acerto (+10 XP)
- Sistema de níveis baseado em XP
- Exibição de XP atual e XP necessário para o próximo nível

## Sistema de perguntas
- Perguntas baseadas no nível do usuário
- Sistema de dificuldade (fácil, médio, difícil)
- Perguntas aleatórias dentro da dificuldade

## Tipos de perguntas
- Resposta aberta (texto)
- Múltipla escolha (botões)

## Conteúdos abordados
- Lógica de programação
- Python
- Banco de dados (SQL)
- Desenvolvimento web (frontend/backend)

## Validação inteligente
- Respostas não diferenciam maiúsculas/minúsculas
- Suporte a acentos (ex: Brasília = brasilia)

## Ranking
- Sistema de ranking entre usuários
- Base para competição entre jogadores

---

# Estrutura do projeto

```

CodeQuest/
│
├── app.py
├── init_db.py
├── database.db
├── README.md
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│
└── static/
├── style.css
└── script.js

```

---

# Como rodar o projeto

## 1. Clonar o repositório

```

git clone <seu-repositorio>
cd CodeQuest

```

---

## 2. Criar ambiente virtual (opcional)

Windows:
```

python -m venv venv
venv\Scripts\activate

```

Linux/Mac:
```

python3 -m venv venv
source venv/bin/activate

```

---

## 3. Instalar dependências

```

pip install flask

```

---

## 4. Rodar o projeto

```

python app.py

```

O sistema irá automaticamente:
- criar o banco de dados
- inserir perguntas iniciais

---

## 5. Acessar no navegador

```

[http://127.0.0.1:5000](http://127.0.0.1:5000)

```

---

# Como funciona

1. Usuário faz login
2. Sistema calcula o nível com base no XP
3. Uma pergunta é selecionada com base na dificuldade
4. O usuário responde:
   - digitando (texto)
   - ou clicando (múltipla escolha)
5. O sistema valida a resposta
6. Se correto:
   - ganha +10 XP
7. O sistema atualiza o progresso

---

# Sistema de níveis

O nível do usuário é definido por:

```

nível = XP // 50

```

Exemplo:
- 0–49 XP → nível 0
- 50–99 XP → nível 1
- 100–149 XP → nível 2

---

# Objetivo do projeto

Criar uma plataforma de aprendizado interativo focada em programação, com progressão gamificada e experiência envolvente.

---

# Melhorias futuras

- Interface estilo Duolingo
- Feedback visual (acerto/erro)
- Explicação das respostas
- Sistema de conquistas
- Progresso por tema (Python, SQL, etc.)
- Perguntas com código formatado
- Deploy online (Render)

---

# Autor

Projeto desenvolvido por Calebe Alves, Bruno, Gabriel nilmar, Felipe gustavo, Anderson thiago

Curso técnico de Desenvolvimento de Sistemas
```

