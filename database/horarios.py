from database.connection import get_connection


def _formatar_hora(hora):
    """
    Converte valores de TIME do MySQL para HH:MM.

    Pode receber:
    - datetime.time
    - datetime.timedelta
    - string
    - None
    """

    if hora is None:
        return ""

    # datetime.time
    if hasattr(hora, "strftime"):
        return hora.strftime("%H:%M")

    # datetime.timedelta
    if hasattr(hora, "total_seconds"):
        total_segundos = int(hora.total_seconds())

        horas = (total_segundos // 3600) % 24
        minutos = (total_segundos % 3600) // 60

        return f"{horas:02d}:{minutos:02d}"

    valor = str(hora).strip()

    if not valor:
        return ""

    # Caso venha como HH:MM:SS
    if len(valor) >= 5 and ":" in valor:
        partes = valor.split(":")

        try:
            horas = int(partes[0])
            minutos = int(partes[1])

            return f"{horas:02d}:{minutos:02d}"

        except (ValueError, IndexError):
            pass

    return valor


def buscar_por_estabelecimento(estabelecimento_id):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,
                dia_semana,
                periodo,
                hora_abertura,
                hora_fechamento
            FROM horarios_funcionamento
            WHERE estabelecimento_id = %s
            ORDER BY
                dia_semana ASC,
                periodo ASC
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        horarios = cursor.fetchall()

        # Normaliza os horários para HH:MM.
        for horario in horarios:

            horario["hora_abertura"] = _formatar_hora(
                horario["hora_abertura"]
            )

            horario["hora_fechamento"] = _formatar_hora(
                horario["hora_fechamento"]
            )

        return horarios

    finally:

        cursor.close()
        conexao.close()


def salvar_horarios(
    estabelecimento_id,
    horarios
):
    """
    Salva exatamente os 7 dias e seus 2 períodos.

    Estrutura esperada:

    {
        1: [
            {
                "abertura": "08:00",
                "fechamento": "12:00"
            },
            {
                "abertura": "13:00",
                "fechamento": "18:00"
            }
        ],
        ...
    }

    Regras:

    - Dia não enviado -> remove os dois períodos.
    - Período vazio -> remove somente aquele período.
    - Período preenchido -> atualiza ou cria somente aquele período.
    - O outro período nunca é alterado.
    """

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        # Processa SEMPRE os 7 dias.
        for dia in range(1, 8):

            periodos = horarios.get(
                dia,
                [
                    {
                        "abertura": "",
                        "fechamento": ""
                    },
                    {
                        "abertura": "",
                        "fechamento": ""
                    }
                ]
            )

            # Garante exatamente dois períodos.
            while len(periodos) < 2:
                periodos.append({
                    "abertura": "",
                    "fechamento": ""
                })

            for indice in range(2):

                periodo = indice + 1

                horario = periodos[indice]

                abertura = (
                    horario.get("abertura", "")
                    or ""
                ).strip()

                fechamento = (
                    horario.get("fechamento", "")
                    or ""
                ).strip()

                # --------------------------------------------------
                # BUSCA O PERÍODO ATUAL
                # --------------------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM horarios_funcionamento
                    WHERE estabelecimento_id = %s
                      AND dia_semana = %s
                      AND periodo = %s
                    LIMIT 1
                    """,
                    (
                        estabelecimento_id,
                        dia,
                        periodo
                    )
                )

                existente = cursor.fetchone()

                # --------------------------------------------------
                # PERÍODO VAZIO
                # --------------------------------------------------

                if not abertura and not fechamento:

                    if existente:

                        cursor.execute(
                            """
                            DELETE FROM horarios_funcionamento
                            WHERE id = %s
                              AND estabelecimento_id = %s
                            """,
                            (
                                existente[0],
                                estabelecimento_id
                            )
                        )

                    continue

                # --------------------------------------------------
                # NÃO PERMITE SALVAR SÓ METADE DO PERÍODO
                # --------------------------------------------------

                if not abertura or not fechamento:

                    raise ValueError(
                        f"O dia {dia}, período {periodo}, "
                        "precisa ter abertura e fechamento."
                    )

                # --------------------------------------------------
                # ATUALIZA
                # --------------------------------------------------

                if existente:

                    cursor.execute(
                        """
                        UPDATE horarios_funcionamento
                        SET
                            hora_abertura = %s,
                            hora_fechamento = %s
                        WHERE id = %s
                          AND estabelecimento_id = %s
                        """,
                        (
                            abertura,
                            fechamento,
                            existente[0],
                            estabelecimento_id
                        )
                    )

                # --------------------------------------------------
                # CRIA
                # --------------------------------------------------

                else:

                    cursor.execute(
                        """
                        INSERT INTO horarios_funcionamento (
                            estabelecimento_id,
                            dia_semana,
                            periodo,
                            hora_abertura,
                            hora_fechamento
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            estabelecimento_id,
                            dia,
                            periodo,
                            abertura,
                            fechamento
                        )
                    )

        conexao.commit()

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()