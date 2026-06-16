// ===========================
// ESTADO GLOBAL
// ===========================
let enviando = false;
let frase = [];

// ===========================
// RESPOSTA DE TEXTO
// ===========================
function enviar() {
    const input = document.getElementById("resposta");
    const resposta = input ? input.value.trim() : "";
    if (!resposta) return;
    enviarResposta(resposta);
}

// ===========================
// RESPOSTA DE MÚLTIPLA ESCOLHA
// ===========================
function responder(opcao) {
    enviarResposta(opcao);
}

// ===========================
// ENVIO PARA O SERVIDOR
// ===========================
function enviarResposta(resposta) {
    if (enviando) return;
    if (!question_id) return;

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
        mostrarMensagem("Erro de conexão. Tente novamente.", "#f97316");
        enviando = false;
        reativarBotoes();
    });
}

// ===========================
// EXIBIÇÃO DO RESULTADO
// ===========================
function mostrarResultado(data) {
    const el = document.getElementById("resultado");
    if (!el) return;

    if (data.result === "correct") {
        mostrarMensagem("✓ Correto! +10 XP", "#22c55e");
    } else if (data.result === "already_answered") {
        mostrarMensagem("Você já respondeu essa questão.", "#f97316");
    } else {
        mostrarMensagem("✗ Errado! Resposta: " + data.correct_answer, "#ef4444");
    }

    setTimeout(() => location.reload(), 1600);
}

function mostrarMensagem(texto, cor) {
    const el = document.getElementById("resultado");
    if (!el) return;
    el.textContent = texto;
    el.style.color = cor;
}

// ===========================
// CONTROLE DE BOTÕES
// ===========================
function desativarBotoes() {
    document.querySelectorAll("button").forEach(btn => {
        btn.disabled = true;
    });
    const input = document.getElementById("resposta");
    if (input) input.disabled = true;
}

function reativarBotoes() {
    document.querySelectorAll("button").forEach(btn => {
        btn.disabled = false;
    });
    const input = document.getElementById("resposta");
    if (input) input.disabled = false;
}

// ===========================
// ENTER NO INPUT DE TEXTO
// ===========================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("resposta");
    if (input) {
        input.addEventListener("keydown", e => {
            if (e.key === "Enter") enviar();
        });
    }
});

// ===========================
// WORD BANK
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
            background: #1d4ed8;
            color: #dbeafe;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
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

function limparMontagem() {
    frase = [];
    atualizarMontagem();
}