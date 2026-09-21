-- Execute uma única vez no banco de dados do La Carta antes de ativar
-- a confirmação de troca de e-mail. A tabela usuarios já possui
-- senha_alterada_em, índice de e-mail e password_reset_tokens.

CREATE TABLE IF NOT EXISTS email_change_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    novo_email VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expira_em DATETIME NOT NULL,
    usado TINYINT(1) NOT NULL DEFAULT 0,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_email_change_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_email_change_usuario (usuario_id)
);
