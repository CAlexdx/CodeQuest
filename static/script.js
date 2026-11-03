// ===========================
// CodeQuest - perguntas, corações, revisão e teoria em cards
// Páginas que usam: unidade.html (quiz_mode = "unit") e revisao.html (quiz_mode = "review")
// ===========================
let enviando = false;
let frase = [];
let botaoEscolhido = null;

const MODO = typeof quiz_mode !== "undefined" ? quiz_mode : "unit";

// ===========================
// AO CARREGAR
// ===========================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("resposta");
    if (input) {
        input.addEventListener("keydown", e => {
            if (e.key === "Enter") enviar();
        });
        // foco automático só em telas grandes (no celular abriria o teclado e esconderia a pergunta)
        if (window.matchMedia && window.matchMedia("(min-width: 700px)").matches) input.focus();
    }
    iniciarTeoria();
});

// ===========================
// TEORIA EM CARDS
// ===========================
function iniciarTeoria() {
    const root = document.getElementById("teoria");
    if (!root) return;

    const cards = Array.from(root.querySelectorAll(".theory-card"));
    const dots = Array.from(root.querySelectorAll(".theory-dot"));
    const btnNext = document.getElementById("theory-next");
    const btnBack = document.getElementById("theory-back");
    const mustRead = root.dataset.mustRead === "1";
    const outOfHearts = root.dataset.outOfHearts === "1";
    const afterUrl = root.dataset.afterUrl || "/";
    const unitId = root.dataset.unitId;
    let i = 0;

    function lastLabel() {
        if (!mustRead) return "Fechar ✔";
        return outOfHearts ? "Recarregar corações 💖" : "Começar a prática 🚀";
    }

    function render() {
        cards.forEach((c, k) => { c.hidden = k !== i; });
        dots.forEach((d, k) => d.classList.toggle("active", k === i));
        dots.forEach((d, k) => d.classList.toggle("seen", k < i));
        btnBack.hidden = i === 0;
        btnNext.textContent = i < cards.length - 1 ? "Continuar →" : lastLabel();
        btnNext.disabled = false;
    }

    async function concluir() {
        if (!mustRead) { window.location.href = afterUrl; return; }
        btnNext.disabled = true;
        btnNext.textContent = "Carregando...";
        try {
            const res = await fetch("/api/unidade/" + unitId + "/teoria", { method: "POST" });
            if (!res.ok) throw new Error("falhou");
            window.location.href = afterUrl;
        } catch (e) {
            btnNext.disabled = false;
            btnNext.textContent = "Tentar de novo";
        }
    }

    btnNext.addEventListener("click", () => {
        if (i < cards.length - 1) { i += 1; render(); window.scrollTo({ top: 0, behavior: "smooth" }); }
        else concluir();
    });
    btnBack.addEventListener("click", () => { if (i > 0) { i -= 1; render(); } });
    document.addEventListener("keydown", e => {
        if (e.key === "ArrowRight") btnNext.click();
        if (e.key === "ArrowLeft" && i > 0) btnBack.click();
    });
    render();
}

// ===========================
// CAPTURA DE RESPOSTAS
// ===========================
function enviar() {
    const input = document.getElementById("resposta");
    const resposta = input ? input.value.trim() : "";
    if (!resposta) return;
    enviarResposta(resposta);
}

function responder(opcao, botao) {
    // remove quebras de linha e espaços extras invisíveis gerados pelo HTML das alternativas
    const opcaoLimpa = opcao.replace(/\s+/g, " ").trim();
    botaoEscolhido = botao || null;
    enviarResposta(opcaoLimpa);
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
        body: JSON.stringify({ id: question_id, answer: resposta, mode: MODO })
    })
    .then(res => res.json().catch(() => ({})).then(data => ({ status: res.status, ok: res.ok, data })))
    .then(({ status, ok, data }) => {
        if (status === 409 && data.result === "theory_required") {
            window.location.reload();  // o servidor mostra a teoria
            return;
        }
        if (status === 403 && data.login_url) {
            window.location.href = data.login_url;
            return;
        }
        if (!ok) throw new Error(data.error || "Erro de rede");
        mostrarResultado(data);
    })
    .catch(() => {
        mostrarMensagem("⚠️ Erro de conexão. Tente novamente.", "#f97316");
        enviando = false;
        frase = [];
        reativarBotoes();
    });
}

// ===========================
// VISUALIZAÇÃO DO FEEDBACK
// ===========================
function mostrarResultado(data) {
    const quizBox = document.querySelector(".quiz");

    if (data.result === "already_answered") {
        window.location.reload();
        return;
    }

    const extra = document.getElementById("resultado-extra");
    const certo = data.result === "correct";

    if (certo) {
        const bonus = data.mode === "review" ? " (XP em dobro!)" : "";
        mostrarMensagem("🎉 Correto! +" + data.xp_gained + " XP" + bonus, "#22c55e");
        if (quizBox) quizBox.classList.add("anim-certo");
        if (botaoEscolhido) botaoEscolhido.classList.add("opcao-certa");
    } else {
        mostrarMensagem("❌ Não foi dessa vez", "#ef4444");
        if (quizBox) quizBox.classList.add("anim-errado");
        if (botaoEscolhido) botaoEscolhido.classList.add("opcao-errada");
    }

    const partes = [];
    if (!certo) partes.push("Resposta correta: " + data.correct_answer);
    if (data.leveled_up) partes.push("⭐ Subiu para o nível " + data.level + "!");
    if (data.heart_regained) partes.push("💖 3 acertos seguidos: você recuperou um coração!");
    if (data.mode === "review" && !certo) partes.push("Sem problema: ela continua no banco de erros para você tentar de novo.");
    if (extra) extra.textContent = partes.join(" ");

    if (typeof data.hearts === "number") atualizarCoracoes(data.hearts);
    if (typeof data.done === "number") atualizarProgresso(data.done, data.total);
    if (data.mode === "review") {
        const left = document.getElementById("errors-left");
        if (left) left.textContent = String(data.errors_left);
    }

    prepararContinuar(data);
}

function prepararContinuar(data) {
    const fb = document.getElementById("feedback");
    const btn = document.getElementById("btn-continuar");
    if (!fb || !btn) return;

    let destino = null;
    if (MODO === "review") {
        btn.textContent = data.errors_left > 0 ? "Próxima questão →" : "Concluir revisão 🎉";
        destino = "/revisao" + (data.result === "wrong" ? "?skip=" + encodeURIComponent(question_id) : "");
    } else if (data.out_of_hearts) {
        btn.textContent = "📖 Reler a teoria para recarregar";
        destino = null;  // recarregar: o servidor mostra os cards
    } else if (data.unit_complete) {
        btn.textContent = "Concluir unidade 🎉";
    } else {
        btn.textContent = "Continuar →";
    }

    fb.hidden = false;
    btn.disabled = false;
    btn.onclick = () => {
        if (destino) window.location.href = destino;
        else window.location.reload();
    };
    btn.focus({ preventScroll: false });
    try { fb.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch (e) { /* ignora */ }
}

function atualizarCoracoes(n) {
    const box = document.getElementById("hearts");
    if (!box) return;
    const items = box.querySelectorAll(".heart");
    items.forEach((el, k) => {
        const viva = k < n;
        const estavaViva = !el.classList.contains("lost");
        el.textContent = viva ? "❤️" : "🖤";
        el.classList.toggle("lost", !viva);
        if (estavaViva && !viva) el.classList.add("heart-break");
    });
    box.setAttribute("aria-label", "Corações restantes: " + n + " de " + items.length);
}

function atualizarProgresso(done, total) {
    const label = document.getElementById("steps-label");
    const bar = document.getElementById("steps-bar");
    if (label) label.textContent = done >= total ? "Unidade completa!" : "Pergunta " + (done + 1) + " de " + total;
    if (bar && total) bar.style.width = Math.round(100 * done / total) + "%";
}

function mostrarMensagem(texto, cor) {
    const el = document.getElementById("resultado");
    if (!el) return;
    el.textContent = texto;
    el.style.color = cor;
}

// ===========================
// CONTROLE DE INPUTS
// ===========================
function desativarBotoes() {
    document.querySelectorAll("#area-resposta button, #area-resposta input, #montagem .word-pill").forEach(el => {
        el.disabled = true;
        el.style.opacity = "0.6";
        el.style.cursor = "not-allowed";
    });
}

function reativarBotoes() {
    document.querySelectorAll("#area-resposta button, #area-resposta input").forEach(el => {
        el.disabled = false;
        el.style.opacity = "1";
        el.style.cursor = "pointer";
    });
}

// ===========================
// MECÂNICA DO WORD BANK (ESTILO DUOLINGO)
// ===========================
function selecionarPalavra(botao) {
    if (enviando || botao.classList.contains("word-disabled")) return;

    const palavra = botao.textContent.trim();
    const index = botao.getAttribute("data-index");

    // Desativa visualmente o botão mantendo o espaço dele no layout
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
        el.innerHTML = '<span class="placeholder-text">Toque nas palavras para ordenar...</span>';
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
    const botaoOriginal = document.querySelector('#wordbank button[data-index="' + originalIndex + '"]');
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
}
