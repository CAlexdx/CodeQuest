function enviar(){
    let resposta = document.getElementById("resposta").value
    enviarResposta(resposta)
}

function responder(opcao){
    enviarResposta(opcao)
}

function enviarResposta(resposta){

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
}else{
    resultado.innerText="Errado! Resposta: " + data.correct_answer
    resultado.style.color="red"
}

setTimeout(()=>{
    location.reload()
},1500)

})

}

// WORD BANK

let frase = []

function addWord(palavra){
    frase.push(palavra)
    document.getElementById("montagem").innerText = frase.join(" ")
}

function enviarMontagem(){
    let resposta = frase.join(" ")
    enviarResposta(resposta)
    frase = []
}