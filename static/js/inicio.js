// JS PARA A LANDING PAGE (inicio.html)

const duvidas = document.getElementById("duvidasFrequentes");
duvidas.addEventListener("click", () => {
    window.location.href = "/faq";
});

// ------------------

// Separado em dois grupos, porque só os dropdowns principais do
// nav (Por que / Recursos / Como funciona) precisam ser mutuamente
// exclusivos. Os itens expansíveis dentro de Recursos (Gestão pelo
// Painel, QR Code) continuam independentes — fechar um não deve
// fechar o .navDropdown pai que os contém.
const navTriggers = document.querySelectorAll('.navTrigger');
const itemTriggers = document.querySelectorAll('.itemTrigger');

function fecharOutrosDropdowns(exceto) {
    navTriggers.forEach(botao => {
        if (botao === exceto) return;

        const alvo = document.getElementById(botao.dataset.toggle);
        if (alvo && !alvo.hidden) {
            alvo.hidden = true;
            botao.setAttribute('aria-expanded', 'false');
        }
    });
}

navTriggers.forEach(botao => {
    botao.addEventListener('click', () => {

        const alvo = document.getElementById(botao.dataset.toggle);
        if (!alvo) return;

        const estaAberto = !alvo.hidden;

        // fecha qualquer outro dropdown de nav aberto antes de
        // decidir o estado deste — evita sobreposição
        fecharOutrosDropdowns(botao);

        alvo.hidden = estaAberto;
        botao.setAttribute('aria-expanded', String(!estaAberto));
    });
});

itemTriggers.forEach(botao => {
    botao.addEventListener('click', () => {

        const alvo = document.getElementById(botao.dataset.toggle);
        if (!alvo) return;

        const estaAberto = !alvo.hidden;

        alvo.hidden = estaAberto;
        botao.setAttribute('aria-expanded', String(!estaAberto));
    });
});