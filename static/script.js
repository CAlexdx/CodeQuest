let enviando = false // trava anti-spam

function enviar(){
    let resposta = document.getElementById("resposta").value.trim()

    if(!resposta) return

    enviarResposta(resposta)
}

function responder(opcao){
    enviarResposta(opcao)
}

function enviarResposta(resposta){

    if(enviando) return // 🔥 trava spam
    enviando = true

    desativarBotoes()

    fetch("/answer",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            id:question_id,
            answer:resposta
        })
    })

    .then(res=>res.json())

    .then(data=>{

        let resultado = document.getElementById("resultado")

        if(data.result=="correct"){
            resultado.innerText="Correto! +10 XP"
            resultado.style.color="lime"
        }
        else if(data.result=="already_answered"){
            resultado.innerText="Você já respondeu essa questão"
            resultado.style.color="orange"
        }
        else{
            resultado.innerText="Errado! Resposta: " + data.correct_answer
            resultado.style.color="red"
        }

        setTimeout(()=>{
            location.reload()
        },1500)

    })

}

// 🔥 desativa tudo após clicar
function desativarBotoes(){
    let botoes = document.querySelectorAll("button")
    botoes.forEach(btn=>{
        btn.disabled = true
        btn.style.opacity = "0.6"
    })
}

// ==========================
// WORD BANK
// ==========================

let frase = []

function addWord(palavra){
    if(enviando) return

    frase.push(palavra)
    document.getElementById("montagem").innerText = frase.join(" ")
}

function enviarMontagem(){
    let resposta = frase.join(" ")
    if(!resposta) return

    enviarResposta(resposta)
    frase = []
}