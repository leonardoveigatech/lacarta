# La Carta — pacote de publicação

## O que foi ajustado
- `requirements.txt` convertido para UTF-8 sem BOM.
- Comprovantes Pix gravados em `instance/uploads/comprovantes/`, fora de `static/`.
- A rota de visualização dos comprovantes exige autenticação do proprietário e usa somente o nome do arquivo.
- `app.py` não inicia o servidor com `debug=True`.
- `.env` e caches Python não foram incluídos no pacote.
- Comprovantes de teste não foram incluídos.

## Antes de publicar
1. Crie um banco MySQL na hospedagem e importe o schema/migrations necessários.
2. Configure as variáveis do `.env` no ambiente de produção (ou crie o arquivo no servidor): `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SECRET_KEY`, `SESSION_COOKIE_SECURE=true`, `LA_CARTA_OWNER_EMAIL` e `LA_CARTA_OWNER_PASSWORD_HASH`. Configure também SMTP se for usar e-mails.
3. Gere uma `SECRET_KEY` nova e uma senha/hash novos para o proprietário. Não reutilize credenciais que tenham sido compartilhadas em arquivos ou conversas.
4. Instale dependências com `pip install -r requirements.txt`.
5. Configure o servidor WSGI para apontar para `wsgi:application` (ou para `app:app`, conforme o painel da hospedagem).
6. Garanta permissão de escrita para o processo Python em `instance/uploads/comprovantes/` e em `static/uploads/` se a aplicação continuar gravando logos/capas nessa pasta.
7. Ative HTTPS; com HTTPS, mantenha `SESSION_COOKIE_SECURE=true`.
8. Teste login, upload e visualização de comprovante, aprovação Pix, menu público, QR Code e bloqueio por vencimento.

## Atenção ao banco existente
A aplicação espera que as tabelas já estejam criadas. Este ZIP não cria automaticamente um banco de produção nem migra os dados de teste. Confirme se a hospedagem usa o schema atualizado, incluindo tabelas de assinaturas/pagamentos e configurações Pix.
