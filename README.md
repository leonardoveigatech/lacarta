# La Carta

> SaaS de cardápio digital para restaurantes e estabelecimentos.

O La Carta é uma aplicação web desenvolvida para permitir que estabelecimentos criem e gerenciem seus próprios cardápios digitais, disponibilizados aos clientes por meio de uma página pública.

O projeto foi desenvolvido como uma aplicação completa, envolvendo backend, banco de dados, autenticação, controle de acesso, gerenciamento de conteúdo e interface responsiva.


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
