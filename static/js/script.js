// JS PARA O MENU HAMBURGUER

const menuButton = document.getElementById('menuButton');
const closeButton = document.getElementById('closeButton');
const asideMenu = document.getElementById('asideMenu');

menuButton.addEventListener('click', () => {
    asideMenu.classList.add('open');
    document.body.style.overflow = 'hidden';
});

closeButton.addEventListener('click', () => {
    asideMenu.classList.remove('open');
    document.body.style.overflow = '';
});

// JS PARA AS CATEGORIAS/SUBCATEGORIAS/PRODUTOS DAS SUBCATEGORIAS
document.addEventListener("DOMContentLoaded", function () {

    const categoriaSelect = document.getElementById("categoria_id");
    const subcategoriaSelect = document.getElementById("subcategoria_id");
    const subcategoriaField = document.getElementById("subcategoria-field");

    if (!categoriaSelect || !subcategoriaSelect) {
        return;
    }


    /*
    |--------------------------------------------------------------------------
    | SUBCATEGORIA QUE VEIO PELA URL
    |--------------------------------------------------------------------------
    */

    const subcategoriaInicial =
        subcategoriaSelect.dataset.selected || "";


    /*
    |--------------------------------------------------------------------------
    | CARREGAR SUBCATEGORIAS
    |--------------------------------------------------------------------------
    */

    async function carregarSubcategorias(
        categoriaId,
        manterSelecionada = false
    ) {

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

                throw new Error(
                    "Erro ao carregar subcategorias."
                );

            }


            const data = await response.json();


            subcategoriaSelect.innerHTML = `
                <option value="">
                    Nenhuma subcategoria
                </option>
            `;


            if (
                !data.subcategorias ||
                data.subcategorias.length === 0
            ) {

                subcategoriaField.style.display = "none";

                return;
            }


            data.subcategorias.forEach(function (subcategoria) {

                const option =
                    document.createElement("option");

                option.value = subcategoria.id;

                option.textContent = subcategoria.nome;


                /*
                |--------------------------------------------------------------------------
                | MANTER A SUBCATEGORIA QUE VEIO DO BOTÃO "+ PRODUTO"
                |--------------------------------------------------------------------------
                */

                if (
                    manterSelecionada &&
                    String(subcategoria.id) ===
                    String(subcategoriaInicial)
                ) {

                    option.selected = true;

                }


                subcategoriaSelect.appendChild(option);

            });


            subcategoriaField.style.display = "block";


        } catch (error) {

            console.error(
                "Erro ao carregar subcategorias:",
                error
            );

            subcategoriaSelect.innerHTML = `
                <option value="">
                    Erro ao carregar subcategorias
                </option>
            `;

            subcategoriaField.style.display = "block";
        }
    }


    /*
    |--------------------------------------------------------------------------
    | MUDANÇA DE CATEGORIA
    |--------------------------------------------------------------------------
    */

    categoriaSelect.addEventListener(
        "change",
        function () {

            const categoriaId =
                this.value;


            /*
            | Quando o usuário troca manualmente
            | de categoria, não devemos manter
            | a subcategoria antiga.
            */

            carregarSubcategorias(
                categoriaId,
                false
            );

        }
    );


    /*
    |--------------------------------------------------------------------------
    | CARREGAMENTO INICIAL
    |--------------------------------------------------------------------------
    */

    if (categoriaSelect.value) {

        /*
        | Se já existe uma subcategoria enviada
        | pela rota, preservamos ela.
        */

        if (subcategoriaInicial) {

            carregarSubcategorias(
                categoriaSelect.value,
                true
            );

        } else {

            /*
            | Se abriu o formulário normalmente
            | apenas carregamos as subcategorias
            | da categoria.
            */

            carregarSubcategorias(
                categoriaSelect.value,
                false
            );

        }

    } else {

        subcategoriaField.style.display = "none";

    }

});