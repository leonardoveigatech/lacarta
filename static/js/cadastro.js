// MENU HAMBURGUER

const menuButton = document.getElementById('menuButton');
const closeButton = document.getElementById('closeButton');
const asideMenu = document.getElementById('asideMenu');

if (menuButton && asideMenu) {
    menuButton.addEventListener('click', () => {
        asideMenu.classList.add('open');
        document.body.style.overflow = 'hidden';
    });
}

if (closeButton && asideMenu) {
    closeButton.addEventListener('click', () => {
        asideMenu.classList.remove('open');
        document.body.style.overflow = '';
    });
}


// CADASTRO

const form = document.getElementById('formCadastro');
const steps = document.querySelectorAll('.formStep');
const progressFill = document.getElementById('progressFill');
const progressLabel = document.getElementById('progressLabel');

const totalSteps = steps.length;


// NAVEGAÇÃO

function irParaPasso(numero) {

    steps.forEach(step => {
        step.classList.toggle(
            'active',
            step.dataset.step === String(numero)
        );
    });

    if (progressFill) {
        progressFill.style.width =
            `${(numero / totalSteps) * 100}%`;
    }

    if (progressLabel) {
        progressLabel.textContent =
            `Passo ${numero} de ${totalSteps}`;
    }

    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}


// ERROS

function mostrarErro(input, mensagem) {

    if (!input) {
        return;
    }

    input.classList.add('campoInvalido');

    const campo = input.closest('.campo');

    if (!campo) {
        return;
    }

    const erro = campo.querySelector('.mensagemErro');

    if (erro) {
        erro.textContent = mensagem;
    }
}


function limparErro(input) {

    if (!input) {
        return;
    }

    input.classList.remove('campoInvalido');

    const campo = input.closest('.campo');

    if (!campo) {
        return;
    }

    const erro = campo.querySelector('.mensagemErro');

    if (erro) {
        erro.textContent = '';
    }
}


function limparErrosPasso(passo) {

    if (!passo) {
        return;
    }

    passo.querySelectorAll('.campoInvalido').forEach(input => {
        input.classList.remove('campoInvalido');
    });

    passo.querySelectorAll('.mensagemErro').forEach(erro => {
        erro.textContent = '';
    });

    passo.querySelectorAll('.mensagemErroGeral').forEach(erro => {
        erro.textContent = '';
    });
}


function limparErroGeral(id) {

    const erro = document.getElementById(id);

    if (erro) {
        erro.textContent = '';
    }
}


// LIMPAR ERRO AO CORRIGIR

document.querySelectorAll(
    '#formCadastro input, #formCadastro textarea, #formCadastro select'
).forEach(campo => {

    campo.addEventListener('input', () => {
        limparErro(campo);
    });

    campo.addEventListener('change', () => {
        limparErro(campo);
    });

});


// TERMOS

const termos = document.getElementById('termos');
const erroTermos = document.getElementById('erroTermos');

if (termos) {

    termos.addEventListener('change', () => {

        termos.classList.remove('campoInvalido');

        if (termos.checked && erroTermos) {
            erroTermos.textContent = '';
        }

    });

}


// VALIDAÇÃO CAMPO OBRIGATÓRIO

function validarCampoObrigatorio(input, mensagem) {

    if (!input) {
        return false;
    }

    if (!input.value.trim()) {

        mostrarErro(
            input,
            mensagem
        );

        return false;
    }

    limparErro(input);

    return true;
}


// PASSO 1

function validarPasso1() {

    const passo = document.querySelector(
        '[data-step="1"]'
    );

    limparErrosPasso(passo);
    limparErroGeral('erroPasso1');

    let valido = true;

    const nome = document.getElementById('nome');
    const email = document.getElementById('email');
    const senha = document.getElementById('senha');
    const confirmarSenha =
        document.getElementById('confirmarSenha');

    const termos =
        document.getElementById('termos');

    const erroTermos =
        document.getElementById('erroTermos');


    if (!nome.value.trim()) {

        mostrarErro(
            nome,
            'Informe seu nome completo.'
        );

        valido = false;
    }


    if (!email.value.trim()) {

        mostrarErro(
            email,
            'Informe seu e-mail.'
        );

        valido = false;

    } else if (!email.validity.valid) {

        mostrarErro(
            email,
            'Digite um e-mail válido.'
        );

        valido = false;

    } else {

        limparErro(email);
    }


    if (!senha.value) {

        mostrarErro(
            senha,
            'Informe uma senha.'
        );

        valido = false;

    } else if (senha.value.length < 8) {

        mostrarErro(
            senha,
            'A senha deve ter pelo menos 8 caracteres.'
        );

        valido = false;

    } else {

        limparErro(senha);
    }


    if (!confirmarSenha.value) {

        mostrarErro(
            confirmarSenha,
            'Confirme sua senha.'
        );

        valido = false;

    } else if (
        confirmarSenha.value !== senha.value
    ) {

        mostrarErro(
            confirmarSenha,
            'As senhas não coincidem.'
        );

        valido = false;

    } else {

        limparErro(confirmarSenha);
    }


    if (!termos.checked) {

        termos.classList.add('campoInvalido');

        if (erroTermos) {

            erroTermos.textContent =
                'Você precisa aceitar os Termos de Uso e a Política de Privacidade.';
        }

        valido = false;

    } else {

        termos.classList.remove('campoInvalido');

        if (erroTermos) {
            erroTermos.textContent = '';
        }
    }


    return valido;
}


// PASSO 2

function validarPasso2() {

    const passo = document.querySelector(
        '[data-step="2"]'
    );

    limparErrosPasso(passo);
    limparErroGeral('erroPasso2');

    let valido = true;

    const nomeEstabelecimento =
        document.getElementById(
            'nomeEstabelecimento'
        );


    if (
        !validarCampoObrigatorio(
            nomeEstabelecimento,
            'Informe o nome do estabelecimento.'
        )
    ) {

        valido = false;
    }


    return valido;
}


// VALIDAÇÃO DE HORÁRIOS

function validarHorarioPeriodo(
    abertura,
    fechamento,
    diaNome,
    numeroPeriodo
) {

    const temAbertura =
        abertura.value !== '';

    const temFechamento =
        fechamento.value !== '';


    if (!temAbertura && !temFechamento) {
        return true;
    }


    if (!temAbertura) {

        mostrarErro(
            abertura,
            `Informe o horário de abertura do ${numeroPeriodo}º período de ${diaNome}.`
        );

        return false;
    }


    if (!temFechamento) {

        mostrarErro(
            fechamento,
            `Informe o horário de fechamento do ${numeroPeriodo}º período de ${diaNome}.`
        );

        return false;
    }


    if (fechamento.value <= abertura.value) {

        mostrarErro(
            fechamento,
            `O fechamento deve ser posterior à abertura em ${diaNome}.`
        );

        return false;
    }


    limparErro(abertura);
    limparErro(fechamento);

    return true;
}


// VALIDAR DIA

function validarDia(dia) {

    const checkbox =
        document.querySelector(
            `input[name="dias_funcionamento"][value="${dia}"]`
        );


    if (!checkbox || !checkbox.checked) {
        return true;
    }


    const nomesDias = {

        1: 'segunda-feira',
        2: 'terça-feira',
        3: 'quarta-feira',
        4: 'quinta-feira',
        5: 'sexta-feira',
        6: 'sábado',
        7: 'domingo'

    };


    const nomeDia =
        nomesDias[dia];


    const abertura1 =
        document.querySelector(
            `input[name="horarios[${dia}][0][abertura]"]`
        );

    const fechamento1 =
        document.querySelector(
            `input[name="horarios[${dia}][0][fechamento]"]`
        );


    const abertura2 =
        document.querySelector(
            `input[name="horarios[${dia}][1][abertura]"]`
        );

    const fechamento2 =
        document.querySelector(
            `input[name="horarios[${dia}][1][fechamento]"]`
        );


    let valido = true;


    if (
        !validarHorarioPeriodo(
            abertura1,
            fechamento1,
            nomeDia,
            1
        )
    ) {

        valido = false;
    }


    if (
        abertura2 &&
        fechamento2 &&
        (
            !abertura2.disabled ||
            !fechamento2.disabled
        )
    ) {

        if (
            !validarHorarioPeriodo(
                abertura2,
                fechamento2,
                nomeDia,
                2
            )
        ) {

            valido = false;
        }
    }


    return valido;
}




function validarPasso3() {

    const passo = document.querySelector(
        '[data-step="3"]'
    );

    limparErrosPasso(passo);
    limparErroGeral('erroPasso3');

    let valido = true;


    const camposObrigatorios = [

        {
            elemento: document.getElementById('cep'),
            mensagem: 'Informe o CEP.'
        },

        {
            elemento: document.getElementById('estado'),
            mensagem: 'Informe o estado.'
        },

        {
            elemento: document.getElementById('cidade'),
            mensagem: 'Informe a cidade.'
        },

        {
            elemento: document.getElementById('bairro'),
            mensagem: 'Informe o bairro.'
        },

        {
            elemento: document.getElementById('rua'),
            mensagem: 'Informe a rua.'
        },

        {
            elemento: document.getElementById('numero'),
            mensagem: 'Informe o número.'
        }

    ];


    camposObrigatorios.forEach(campo => {

        if (
            !validarCampoObrigatorio(
                campo.elemento,
                campo.mensagem
            )
        ) {

            valido = false;
        }

    });


    const diasSelecionados =
        document.querySelectorAll(
            'input[name="dias_funcionamento"]:checked'
        );


    const erroPasso =
        document.getElementById(
            'erroPasso3'
        );


    if (diasSelecionados.length === 0) {

        if (erroPasso) {

            erroPasso.textContent =
                'Selecione pelo menos um dia de funcionamento.';
        }

        valido = false;
    }


    diasSelecionados.forEach(checkbox => {

        if (!validarDia(checkbox.value)) {
            valido = false;
        }

    });


    return valido;
}




function validarPasso(numero) {

    if (numero === 1) {
        return validarPasso1();
    }

    if (numero === 2) {
        return validarPasso2();
    }

    if (numero === 3) {
        return validarPasso3();
    }

    return false;
}



document.querySelectorAll('[data-next]').forEach(botao => {

    botao.addEventListener('click', () => {

        const proximoPasso =
            Number(botao.dataset.next);

        const passoAtual =
            Number(
                botao.closest('.formStep').dataset.step
            );


        if (!validarPasso(passoAtual)) {
            return;
        }


        irParaPasso(proximoPasso);

    });

});




document.querySelectorAll('[data-prev]').forEach(botao => {

    botao.addEventListener('click', () => {

        const passoAnterior =
            Number(botao.dataset.prev);

        irParaPasso(passoAnterior);

    });

});



document.querySelectorAll(
    'input[name="dias_funcionamento"]'
).forEach(checkbox => {

    checkbox.addEventListener('change', () => {

        const dia = checkbox.value;


        const campos =
            document.querySelectorAll(
                `input[name^="horarios[${dia}]"]`
            );


        campos.forEach(campo => {

            campo.disabled =
                !checkbox.checked;


            if (!checkbox.checked) {

                campo.value = '';

                limparErro(campo);
            }

        });


        const diaContainer =
            checkbox.closest('.horarioDia');


        if (!diaContainer) {
            return;
        }


        const botaoPeriodo =
            diaContainer.querySelector(
                '.btnAdicionarPeriodo'
            );


        const segundoPeriodo =
            diaContainer.querySelector(
                '.segundoPeriodo'
            );


        if (!checkbox.checked) {

            if (segundoPeriodo) {
                segundoPeriodo.hidden = true;
            }

            if (botaoPeriodo) {
                botaoPeriodo.hidden = true;
            }


            if (segundoPeriodo) {

                segundoPeriodo
                    .querySelectorAll('input')
                    .forEach(campo => {

                        campo.value = '';
                        campo.disabled = true;
                        limparErro(campo);

                    });

            }

        } else {

            if (botaoPeriodo) {
                botaoPeriodo.hidden = false;
            }

            if (segundoPeriodo) {
                segundoPeriodo.hidden = true;
            }


            const primeiroPeriodo =
                diaContainer.querySelector(
                    '.periodoHorario:not(.segundoPeriodo)'
                );


            if (primeiroPeriodo) {

                primeiroPeriodo
                    .querySelectorAll('input')
                    .forEach(campo => {

                        campo.disabled = false;

                    });

            }

        }

    });

});



document.querySelectorAll(
    '.btnAdicionarPeriodo'
).forEach(botao => {

    botao.addEventListener('click', () => {

        const diaContainer =
            botao.closest('.horarioDia');


        if (!diaContainer) {
            return;
        }


        const segundoPeriodo =
            diaContainer.querySelector(
                '.segundoPeriodo'
            );


        if (!segundoPeriodo) {
            return;
        }


        segundoPeriodo.hidden = false;


        segundoPeriodo
            .querySelectorAll('input')
            .forEach(campo => {

                campo.disabled = false;

            });


        botao.hidden = true;

    });

});



document.querySelectorAll(
    '.uploadBox'
).forEach(box => {

    const inputId =
        box.getAttribute('for');


    const input =
        document.getElementById(inputId);


    if (!input) {
        return;
    }


    input.addEventListener('change', () => {

        if (
            !input.files ||
            !input.files[0]
        ) {

            return;
        }


        const arquivo =
            input.files[0];


        const tiposPermitidos = [

            'image/jpeg',
            'image/png',
            'image/webp'

        ];


        const limite =
            5 * 1024 * 1024;


        const erroId =
            input.id === 'logo'
                ? 'erroLogo'
                : 'erroImagemCapa';


        const erro =
            document.getElementById(
                erroId
            );


        if (erro) {
            erro.textContent = '';
        }


        input.classList.remove(
            'campoInvalido'
        );


        if (
            !tiposPermitidos.includes(
                arquivo.type
            )
        ) {

            if (erro) {

                erro.textContent =
                    'Use uma imagem JPG, PNG ou WEBP.';
            }


            input.value = '';

            box.classList.remove(
                'preenchido'
            );

            return;
        }


        if (arquivo.size > limite) {

            if (erro) {

                erro.textContent =
                    'A imagem deve ter no máximo 5 MB.';
            }


            input.value = '';

            box.classList.remove(
                'preenchido'
            );

            return;
        }


        box.querySelector(
            '.uploadTexto'
        ).textContent =
            arquivo.name;


        box.classList.add(
            'preenchido'
        );

    });

});



if (form) {

    form.addEventListener(
        'submit',
        event => {

            event.preventDefault();


            if (!validarPasso1()) {

                irParaPasso(1);

                return;
            }


            if (!validarPasso2()) {

                irParaPasso(2);

                return;
            }


            if (!validarPasso3()) {

                irParaPasso(3);

                return;
            }


            form.querySelectorAll(
                'input[type="time"]:disabled'
            ).forEach(input => {

                input.disabled = true;

            });


            form.submit();

        }
    );

}




irParaPasso(1);
