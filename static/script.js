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
    } else if (data.result === "already_answered") {
        mostrarMensagem("Você já respondeu essa questão.", "#f97316", "");
    } else {
        mostrarMensagem("❌ Errado! Resposta: " + data.correct_answer, "#ef4444", "anim-errado");
        if (quizBox) quizBox.classList.add("anim-errado");
    }

    // Mantém o reload padrão para atualizar o estado do progresso
    setTimeout(() => location.reload(), 1600);
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

// Exemplo de código dentro da sua tela de Quiz/Unidade concluída:
function finalizarUnidade(unidadeId) {
    // Salva qual unidade acabou de ser realizada com sucesso
    localStorage.setItem('last_completed_id', unidadeId);
    
    // Redireciona de volta para a trilha
    window.location.href = "/trilhas/1"; 
}