// JS PARA O MENU HAMBURGUER

const menuButton = document.getElementById('menuButton');
const closeButton = document.getElementById('closeButton');
const asideMenu = document.getElementById('asideMenu');

function abrirMenu() {
    asideMenu.classList.add('open');
    menuButton.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
}

function fecharMenu() {
    asideMenu.classList.remove('open');
    menuButton.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
}

if (menuButton && closeButton && asideMenu) {
    menuButton.setAttribute('aria-expanded', 'false');

    menuButton.addEventListener('click', abrirMenu);
    closeButton.addEventListener('click', fecharMenu);

    // fecha ao tocar em um link do menu
    asideMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', fecharMenu));

    // fecha com a tecla Esc
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && asideMenu.classList.contains('open')) fecharMenu();
    });

    // fecha ao clicar fora do menu (útil no desktop, onde o menu não ocupa a tela toda)
    document.addEventListener('click', e => {
        if (!asideMenu.classList.contains('open')) return;
        if (asideMenu.contains(e.target) || menuButton.contains(e.target)) return;
        fecharMenu();
    });
}

// JS PARA AS CATEGORIAS/SUBCATEGORIAS/PRODUTOS DAS SUBCATEGORIAS
document.addEventListener("DOMContentLoaded", function () {

    const categoriaSelect = document.getElementById("categoria_id");
    const subcategoriaSelect = document.getElementById("subcategoria_id");
    const subcategoriaField = document.getElementById("subcategoria-field");

    if (!categoriaSelect || !subcategoriaSelect) {
        return;
    }

    const subcategoriaInicial = subcategoriaSelect.dataset.selected || "";

    async function carregarSubcategorias(categoriaId, manterSelecionada = false) {

        if (!categoriaId) {
            subcategoriaSelect.innerHTML = `
                <option value="">
                    Nenhuma subcategoria
                </option>
            `;
            subcategoriaField.style.display = "none";
            return;
        }

        try {

            const response = await fetch(
                `/admin/categorias/${categoriaId}/subcategorias/json`
            );

            if (!response.ok) {
                throw new Error("Erro ao carregar subcategorias.");
            }

            const data = await response.json();

            subcategoriaSelect.innerHTML = `
                <option value="">
                    Nenhuma subcategoria
                </option>
            `;

            if (!data.subcategorias || data.subcategorias.length === 0) {
                subcategoriaField.style.display = "none";
                return;
            }

            data.subcategorias.forEach(function (subcategoria) {

                const option = document.createElement("option");

                option.value = subcategoria.id;
                option.textContent = subcategoria.nome;

                if (
                    manterSelecionada &&
                    String(subcategoria.id) === String(subcategoriaInicial)
                ) {
                    option.selected = true;
                }

                subcategoriaSelect.appendChild(option);

            });

            subcategoriaField.style.display = "block";

        } catch (error) {

            console.error("Erro ao carregar subcategorias:", error);

            subcategoriaSelect.innerHTML = `
                <option value="">
                    Erro ao carregar subcategorias
                </option>
            `;

            subcategoriaField.style.display = "block";
        }
    }

    categoriaSelect.addEventListener("change", function () {
        carregarSubcategorias(this.value, false);
    });

    if (categoriaSelect.value) {

        if (subcategoriaInicial) {
            carregarSubcategorias(categoriaSelect.value, true);
        } else {
            carregarSubcategorias(categoriaSelect.value, false);
        }

    } else {

        subcategoriaField.style.display = "none";

    }

});