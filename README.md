# La Carta

> SaaS de cardápio digital para restaurantes e estabelecimentos.

O La Carta é uma aplicação web desenvolvida para permitir que estabelecimentos criem e gerenciem seus próprios cardápios digitais, disponibilizados aos clientes por meio de uma página pública.

O projeto foi desenvolvido como uma aplicação completa, envolvendo backend, banco de dados, autenticação, controle de acesso, gerenciamento de conteúdo e interface responsiva.

---

## 📱 Interface

### Cardápio público

<p align="center">
<img width="1920" height="1080" alt="Captura de tela 2026-09-21 214418" src="https://github.com/user-attachments/assets/0fc676b4-d675-47eb-8980-37f0d8fe76b3"/>
<img width="220"  alt="Captura de tela 2026-09-21 215905" src="https://github.com/user-attachments/assets/82c4c162-331b-4bf7-b9aa-ce448b7ad084" />
<img width="220"  alt="Captura de tela 2026-09-21 215841" src="https://github.com/user-attachments/assets/276e9919-7a7b-47b9-bc41-5ab4a6e3a56b" />
<img width="220"  alt="Captura de tela 2026-09-21 215806" src="https://github.com/user-attachments/assets/e910b304-9ee7-4912-a9c9-0b082e0609ce" />
<img width="220"  alt="Captura de tela 2026-09-21 215711" src="https://github.com/user-attachments/assets/cd56c736-0a8e-4e08-8393-ce85b328d914" />


</p>

### Painel administrativo

<p align="center">
<img width="600" height="566" src="https://github.com/user-attachments/assets/e7f4184b-d8fd-4c95-a159-024bbb9cd456" />
<img width="600" height="586" src="https://github.com/user-attachments/assets/51614728-4380-400f-b4b6-7b09630498ea" />

</p>

---

# Sobre o projeto

O La Carta foi desenvolvido utilizando Python e Flask no backend, MySQL (persistência de dados) e Jinja2, HTML, CSS e JavaScript para a interface, porque eu preciso que o HTML se adapte aos dados de cada estabelecimento, então eu não pude simplesmente criar um HTML único, pois cada estabelecimento vai ter o seu de acordo com seu cardápio.

A aplicação possui uma arquitetura preparada para múltiplos estabelecimentos, mantendo os dados de cada estabelecimento isolados por meio de seu identificador.

O projeto também possui recursos relacionados à segurança da aplicação, autenticação de usuários e gerenciamento de sessões.

---

# Funcionalidades

### Gerenciamento do cardápio

- Cadastro, edição e exclusão de categorias
- Cadastro, edição e exclusão de subcategorias
- Cadastro, edição e exclusão de produtos
- Controle de disponibilidade de categorias e subcategorias
- Controle de disponibilidade de produtos
- Organização hierárquica do cardápio

### Gerenciamento do estabelecimento

- Informações do estabelecimento
- Logo e imagem de capa
- Descrição
- Telefone e WhatsApp
- Endereço
- Horários de funcionamento
- Redes sociais

### Autenticação e conta

- Login de usuários
- Controle de sessão
- Logout protegido
- Validação de usuário ativo
- Alteração de senha
- Recuperação de senha
- Alteração de e-mail
- Tokens para operações sensíveis

### Segurança

- Autenticação e autorização
- Controle de acesso por estabelecimento
- Isolamento de dados entre estabelecimentos
- Proteção contra CSRF
- Rate limiting para operações sensíveis
- Validação de dados
- Senhas armazenadas utilizando hash
- Variáveis sensíveis mantidas fora do código-fonte

### Interface

- Design responsivo
- Abordagem mobile-first
- Interface administrativa (PAINEL ADMINISTRATIVO)
- Página pública do cardápio
- Personalização visual
- Configuração dinâmica de aparência
- Navegação adaptada para dispositivos móveis

---

## Arquitetura

O projeto utiliza uma estrutura modular baseada em Flask.

LA CARTA
│
├── app.py
├── config.py
├── requirements.txt
├── .env.example
│
├── database/
│   └── conexão e acesso ao MySQL
│
├── routes/
│   ├── admin.py
│   ├── auth.py
│   └── public.py
│
├── utils/
│   ├── autenticação
│   ├── e-mail
│   ├── segurança
│   └── validações
│
├── templates/
│   ├── admin/
│   ├── auth/
│   └── public/
│
└── static/
    ├── css/
    ├── js/
    └── imagens
