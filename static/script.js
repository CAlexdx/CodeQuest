function responder(opcao){

let correta = "print()"

if(opcao == correta){

document.getElementById("resultado").innerText =
"Resposta correta! +10 XP"

}
else{

document.getElementById("resultado").innerText =
"Resposta errada"

}

}