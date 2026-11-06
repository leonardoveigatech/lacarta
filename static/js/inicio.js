// JS DA LANDING PAGE (login.html)

const navTriggers = document.querySelectorAll('.navTrigger');
const itemTriggers = document.querySelectorAll('.itemTrigger');

function fechar(botao) {
    const alvo = document.getElementById(botao.dataset.toggle);
    if (alvo) alvo.hidden = true;
    botao.setAttribute('aria-expanded', 'false');
}

function fecharTodos(exceto) {
    navTriggers.forEach(b => { if (b !== exceto) fechar(b); });
}

navTriggers.forEach(botao => {
    botao.addEventListener('click', () => {
        const alvo = document.getElementById(botao.dataset.toggle);
        if (!alvo) return;
        const abrir = alvo.hidden;
        fecharTodos(botao);
        alvo.hidden = !abrir;
        botao.setAttribute('aria-expanded', String(abrir));
    });
});

itemTriggers.forEach(botao => {
    botao.addEventListener('click', () => {
        const alvo = document.getElementById(botao.dataset.toggle);
        if (!alvo) return;
        const abrir = alvo.hidden;
        alvo.hidden = !abrir;
        botao.setAttribute('aria-expanded', String(abrir));
    });
});

// Esc ou clique fora fecham os painéis
document.addEventListener('keydown', e => { if (e.key === 'Escape') fecharTodos(); });
document.addEventListener('click', e => {
    if (!e.target.closest('.topbar')) fecharTodos();
});

// ---- GSAP: scroll suave (somente desktop e sem "reduzir movimento") ----
if (window.gsap && window.ScrollTrigger && window.ScrollSmoother) {
    gsap.registerPlugin(ScrollTrigger, ScrollSmoother);

    const mm = gsap.matchMedia();

    mm.add('(min-width: 960px) and (prefers-reduced-motion: no-preference)', () => {
        const smoother = ScrollSmoother.create({
            wrapper: '#smooth-wrapper',
            content: '#smooth-content',
            smooth: 1.2,
            effects: true // ativa o data-speed das imagens
        });
        return () => smoother.kill();
    });

    // Entrada única do hero
    mm.add('(prefers-reduced-motion: no-preference)', () => {
        gsap.from('.hero-inner > *', {
            y: 24, opacity: 0, duration: 0.9, ease: 'power3.out', stagger: 0.12
        });
    });
}