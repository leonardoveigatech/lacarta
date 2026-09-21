import time
from collections import defaultdict, deque
from threading import Lock

from flask import request


_tentativas = defaultdict(deque)
_lock = Lock()

def limite_excedido(acao, identificador, limite, janela_segundos):
    """Limite em memória; em múltiplos servidores, use Redis."""
    agora = time.monotonic()
    chave = f"{acao}:{identificador}"

    with _lock:

        tentativas = _tentativas.get(chave)

        if tentativas is None:
            tentativas = deque()
            _tentativas[chave] = tentativas

        while tentativas and tentativas[0] <= agora - janela_segundos:
            tentativas.popleft()

        if len(tentativas) >= limite:
            return True

        tentativas.append(agora)

        limite_expiracao = agora - janela_segundos

        chaves_vazias = []

        for chave_existente, fila in _tentativas.items():

            while fila and fila[0] <= limite_expiracao:
                fila.popleft()

            if not fila:
                chaves_vazias.append(
                    chave_existente
                )

        for chave_existente in chaves_vazias:
            _tentativas.pop(
                chave_existente,
                None
            )

        return False

def identificador_cliente():
    return request.remote_addr or "desconhecido"
