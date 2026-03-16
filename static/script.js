function enviar(){

let resposta = document.getElementById("resposta").value

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

.then(res => res.json())
.then(data => {

if(data.result == "correct"){
document.getElementById("resultado").innerText = "Acertou! +10 XP"
}
else{
document.getElementById("resultado").innerText = "Errou!"
}

setTimeout(()=>{

location.reload()

},1500)

})

}