// ===========================
// ESTADO GLOBAL
// ===========================
let enviando = false;
let frase = [];

// ===========================
// AUTO-FOCUS AO CARREGAR
// ===========================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("resposta");
    if (input) {
        input.focus();
        input.addEventListener("keydown", e => {
            if (e.key === "Enter") enviar();
        });
    }
});

// ===========================
// CAPTURA DE RESPOSTAS
// ===========================
function enviar() {
    const input = document.getElementById("resposta");
    const resposta = input ? input.value.trim() : "";
    if (!resposta) return;
    enviarResposta(resposta);
}

function responder(opcao) {
    enviarResposta(opcao);
}

// ===========================
// ENVIO PARA O SERVIDOR
// ===========================
function enviarResposta(resposta) {
    if (enviando || !question_id) return;

    enviando = true;
    desativarBotoes();

    fetch("/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: question_id, answer: resposta })
    })
    .then(res => {
        if (!res.ok) throw new Error("Erro de rede");
        return res.json();
    })
    .then(data => mostrarResultado(data))
    .catch(() => {
        mostrarMensagem("⚠️ Erro de conexão. Tente novamente.", "#f97316", "anim-errado");
        enviando = false;
        reativarBotoes();
    });
}

// ===========================
// VISUALIZAÇÃO DO FEEDBACK
// ===========================
function mostrarResultado(data) {
    const quizBox = document.querySelector(".quiz");

    if (data.result === "correct") {
        mostrarMensagem("🎉 Correto! +10 XP", "#22c55e", "anim-certo");
        if (quizBox) quizBox.classList.add("anim-certo");

        // Recarrega a página atual para seguir para a próxima pergunta da unidade
        setTimeout(() => {
            location.reload();
        }, 1600);

    } else if (data.result === "already_answered") {
        mostrarMensagem("Você já respondeu essa questão.", "#f97316", "");
        
        setTimeout(() => {
            location.reload();
        }, 1600);

    } else {
        mostrarMensagem("❌ Errado! Resposta: " + data.correct_answer, "#ef4444", "anim-errado");
        if (quizBox) quizBox.classList.add("anim-errado");
        
        setTimeout(() => {
            location.reload();
        }, 1600);
    }
}

function mostrarMensagem(texto, cor, classeAnimacao) {
    const el = document.getElementById("resultado");
    if (!el) return;
    
    el.textContent = texto;
    el.style.color = cor;
    
    if (classeAnimacao) {
        el.classList.add(classeAnimacao);
    }
}

// ===========================
// CONTROLE DE INPUTS
// ===========================
function desativarBotoes() {
    document.querySelectorAll("button, input").forEach(el => {
        el.disabled = true;
        el.style.opacity = "0.6";
        el.style.cursor = "not-allowed";
    });
}

function reativarBotoes() {
    document.querySelectorAll("button, input").forEach(el => {
        el.disabled = false;
        el.style.opacity = "1";
        el.style.cursor = "pointer";
    });
}

// ===========================
// MECÂNICA DO WORD BANK
// ===========================
function addWord(palavra) {
    if (enviando) return;
    frase.push(palavra);
    atualizarMontagem();
}

function atualizarMontagem() {
    const el = document.getElementById("montagem");
    if (!el) return;

    el.innerHTML = "";
    frase.forEach((palavra, i) => {
        const span = document.createElement("span");
        span.textContent = palavra;
        span.style.cssText = `
            background: #3b82f6;
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-block;
            margin: 4px;
        `;
        span.title = "Clique para remover";
        span.onclick = () => removerPalavra(i);
        el.appendChild(span);
    });
}

function removerPalavra(index) {
    if (enviando) return;
    frase.splice(index, 1);
    atualizarMontagem();
}

function enviarMontagem() {
    const resposta = frase.join(" ").trim();
    if (!resposta) return;
    enviarResposta(resposta);
    frase = [];
}

// ===========================
// MECÂNICA DO WORD BANK (ESTILO DUOLINGO)
// ===========================
function selecionarPalavra(botao) {
    if (enviando || botao.classList.contains("word-disabled")) return;

    const palavra = botao.textContent.trim();
    const index = botao.getAttribute("data-index");

    // Estilo Duolingo: Desativa visualmente o botão mantendo o espaço dele no layout
    botao.classList.add("word-disabled");

    // Adiciona o objeto à frase com o ID de rastreio original
    frase.push({ id: index, texto: palavra });
    atualizarMontagem();
}

function atualizarMontagem() {
    const el = document.getElementById("montagem");
    if (!el) return;

    el.innerHTML = "";

    if (frase.length === 0) {
        el.innerHTML = `<span class="placeholder-text">Toque nas palavras para ordenar...</span>`;
        return;
    }

    // Renderiza as palavras selecionadas na zona de montagem
    frase.forEach((item, i) => {
        const span = document.createElement("span");
        span.textContent = item.texto;
        span.className = "word-pill selected-word";
        span.title = "Clique para remover";
        span.onclick = () => removerPalavraDaMontagem(i, item.id);
        el.appendChild(span);
    });
}

function removerPalavraDaMontagem(posicaoNaFrase, originalIndex) {
    if (enviando) return;

    // Encontra o botão original no banco de palavras usando o índice e devolve a cor dele
    const botaoOriginal = document.querySelector(`#wordbank button[data-index="${originalIndex}"]`);
    if (botaoOriginal) {
        botaoOriginal.classList.remove("word-disabled");
    }

    // Remove do array da frase montada
    frase.splice(posicaoNaFrase, 1);
    atualizarMontagem();
}

function enviarMontagem() {
    // Une as palavras selecionadas separando por espaço simples
    const resposta = frase.map(item => item.texto).join(" ").trim();
    if (!resposta) return;
    
    enviarResposta(resposta);
    frase = []; // Reseta o estado local
}