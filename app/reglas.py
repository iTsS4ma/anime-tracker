"""Reglas de negocio de Anime Tracker.

Toda escritura a la base de datos pasa por este módulo, para que las reglas de negocio RN-### (documentadas en
docs/Documentacion.md) se cumplan sin importar desde dónde se llame (interfaz web o pruebas).
"""
import sqlite3

PENDIENTE, VIENDO, COMPLETADA = "Pendiente", "Viendo", "Completada"
CALIFICACION_MIN, CALIFICACION_MAX = 1, 10  # RN-003
ROLES = ("Principal", "Secundario")


class ReglaNegocioError(Exception):
    """Se lanza cuando una operación incumple una regla de negocio."""

    def __init__(self, regla: str, mensaje: str):
        super().__init__(mensaje)
        self.regla = regla
        self.mensaje = mensaje


class DatoInvalido(ValueError):
    """Dato vacío o con formato incorrecto (no es una regla de negocio)."""


def _texto(valor: str, campo: str) -> str:
    valor = (valor or "").strip()
    if not valor:
        raise DatoInvalido(f"El campo «{campo}» es obligatorio.")
    return valor


def _entero(valor, campo: str) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise DatoInvalido(f"El campo «{campo}» debe ser un número entero.") from None


# ---------------------------------------------------------------- RN-002 Estado calculado
def estado_de(vistos: int, episodios: int) -> str:
    """El estado nunca se captura a mano: sale de los episodios vistos."""
    if vistos <= 0:
        return PENDIENTE
    if vistos >= episodios:
        return COMPLETADA
    return VIENDO


# ---------------------------------------------------------------- Series
def _datos_serie(titulo, temporada, estudio, anio, episodios):
    titulo, temporada, estudio = _texto(titulo, "Título"), _texto(temporada, "Temporada"), _texto(estudio, "Estudio")
    anio, episodios = _entero(anio, "Año"), _entero(episodios, "Episodios")
    if episodios < 1:
        raise DatoInvalido("Los episodios deben ser 1 o más.")
    if not 1900 <= anio <= 2100:
        raise DatoInvalido("El año no es válido.")
    return titulo, temporada, estudio, anio, episodios


def crear_serie(conn: sqlite3.Connection, titulo, temporada, estudio, anio, episodios) -> int:
    datos = _datos_serie(titulo, temporada, estudio, anio, episodios)
    if conn.execute("SELECT 1 FROM series WHERE lower(titulo) = lower(?) AND lower(temporada) = lower(?)", (datos[0], datos[1])).fetchone():
        raise DatoInvalido(f"Ya existe «{datos[0]} · {datos[1]}».")
    cur = conn.execute("INSERT INTO series (titulo, temporada, estudio, anio, episodios) VALUES (?, ?, ?, ?, ?)", datos)
    conn.commit()
    return cur.lastrowid


def editar_serie(conn: sqlite3.Connection, serie_id: int, titulo, temporada, estudio, anio, episodios) -> None:
    titulo, temporada, estudio, anio, episodios = _datos_serie(titulo, temporada, estudio, anio, episodios)
    otra = conn.execute(
        "SELECT 1 FROM series WHERE lower(titulo) = lower(?) AND lower(temporada) = lower(?) AND id <> ?", (titulo, temporada, serie_id)
    ).fetchone()
    if otra:
        raise DatoInvalido(f"Ya existe «{titulo} · {temporada}».")
    # RN-007: el total de episodios no baja de lo que alguien ya vio.
    maximo = conn.execute("SELECT COALESCE(MAX(vistos), 0) FROM seguimiento WHERE serie_id = ?", (serie_id,)).fetchone()[0]
    if episodios < maximo:
        raise ReglaNegocioError("RN-007", f"Alguien ya vio {maximo} episodios; el total no puede ser menor.")
    with conn:
        conn.execute(
            "UPDATE series SET titulo = ?, temporada = ?, estudio = ?, anio = ?, episodios = ? WHERE id = ?",
            (titulo, temporada, estudio, anio, episodios, serie_id),
        )
        for s in conn.execute("SELECT id, vistos FROM seguimiento WHERE serie_id = ?", (serie_id,)).fetchall():
            conn.execute("UPDATE seguimiento SET estado = ? WHERE id = ?", (estado_de(s["vistos"], episodios), s["id"]))


def eliminar_serie(conn: sqlite3.Connection, serie_id: int) -> None:
    # RN-006: una serie que alguien sigue no se elimina.
    n = conn.execute("SELECT COUNT(*) FROM seguimiento WHERE serie_id = ?", (serie_id,)).fetchone()[0]
    if n:
        raise ReglaNegocioError("RN-006", f"La serie está en {n} lista(s); primero hay que quitarla de ellas.")
    conn.execute("DELETE FROM series WHERE id = ?", (serie_id,))
    conn.commit()


# ---------------------------------------------------------------- Personajes
def crear_personaje(conn: sqlite3.Connection, serie_id, nombre: str, rol: str) -> int:
    serie_id, nombre = _entero(serie_id, "Serie"), _texto(nombre, "Nombre")
    if rol not in ROLES:
        raise DatoInvalido("El rol debe ser Principal o Secundario.")
    if not conn.execute("SELECT 1 FROM series WHERE id = ?", (serie_id,)).fetchone():
        raise DatoInvalido("La serie no existe.")
    # RN-005: el nombre no se repite dentro de la misma serie.
    if conn.execute("SELECT 1 FROM personajes WHERE serie_id = ? AND lower(nombre) = lower(?)", (serie_id, nombre)).fetchone():
        raise ReglaNegocioError("RN-005", f"«{nombre}» ya está registrado en esta serie.")
    cur = conn.execute("INSERT INTO personajes (serie_id, nombre, rol) VALUES (?, ?, ?)", (serie_id, nombre, rol))
    conn.commit()
    return cur.lastrowid


def eliminar_personaje(conn: sqlite3.Connection, personaje_id: int) -> None:
    conn.execute("DELETE FROM personajes WHERE id = ?", (personaje_id,))
    conn.commit()


# ---------------------------------------------------------------- Perfiles
def crear_perfil(conn: sqlite3.Connection, nombre: str) -> int:
    nombre = _texto(nombre, "Nombre")
    if conn.execute("SELECT 1 FROM perfiles WHERE lower(nombre) = lower(?)", (nombre,)).fetchone():
        raise DatoInvalido(f"Ya existe el perfil «{nombre}».")
    cur = conn.execute("INSERT INTO perfiles (nombre) VALUES (?)", (nombre,))
    conn.commit()
    return cur.lastrowid


# ---------------------------------------------------------------- Lista de seguimiento
def agregar_a_lista(conn: sqlite3.Connection, perfil_id, serie_id) -> int:
    perfil_id, serie_id = _entero(perfil_id, "Perfil"), _entero(serie_id, "Serie")
    serie = conn.execute("SELECT titulo, temporada, episodios FROM series WHERE id = ?", (serie_id,)).fetchone()
    if serie is None or not conn.execute("SELECT 1 FROM perfiles WHERE id = ?", (perfil_id,)).fetchone():
        raise DatoInvalido("El perfil o la serie no existen.")
    # RN-004: una serie aparece una sola vez en la lista de cada perfil.
    if conn.execute("SELECT 1 FROM seguimiento WHERE perfil_id = ? AND serie_id = ?", (perfil_id, serie_id)).fetchone():
        raise ReglaNegocioError("RN-004", f"«{serie['titulo']} · {serie['temporada']}» ya está en tu lista.")
    cur = conn.execute(
        "INSERT INTO seguimiento (perfil_id, serie_id, vistos, estado) VALUES (?, ?, 0, ?)",
        (perfil_id, serie_id, estado_de(0, serie["episodios"])),
    )
    conn.commit()
    return cur.lastrowid


def _seguimiento(conn, seguimiento_id):
    fila = conn.execute(
        "SELECT s.*, se.episodios FROM seguimiento s JOIN series se ON se.id = s.serie_id WHERE s.id = ?", (seguimiento_id,)
    ).fetchone()
    if fila is None:
        raise DatoInvalido("Ese registro de la lista no existe.")
    return fila


def actualizar_seguimiento(conn: sqlite3.Connection, seguimiento_id: int, vistos, calificacion=None, resena=None) -> str:
    """Guarda el avance de una serie y devuelve el estado calculado."""
    fila = _seguimiento(conn, seguimiento_id)
    vistos = _entero(vistos, "Episodios vistos")
    # RN-001: los episodios vistos van de 0 al total de la serie.
    if not 0 <= vistos <= fila["episodios"]:
        raise ReglaNegocioError("RN-001", f"Los episodios vistos deben estar entre 0 y {fila['episodios']}.")
    estado = estado_de(vistos, fila["episodios"])  # RN-002

    calificacion = None if calificacion in (None, "") else _entero(calificacion, "Calificación")
    resena = (resena or "").strip() or None
    # RN-003: calificar requiere haber visto algo; reseñar requiere haber terminado.
    if calificacion is not None:
        if not CALIFICACION_MIN <= calificacion <= CALIFICACION_MAX:
            raise ReglaNegocioError("RN-003", f"La calificación va de {CALIFICACION_MIN} a {CALIFICACION_MAX}.")
        if vistos == 0:
            raise ReglaNegocioError("RN-003", "Para calificar una serie hay que ver al menos un episodio.")
    if resena and estado != COMPLETADA:
        raise ReglaNegocioError("RN-003", "La reseña se escribe al terminar la serie.")

    conn.execute(
        "UPDATE seguimiento SET vistos = ?, estado = ?, calificacion = ?, resena = ?, actualizado = datetime('now') WHERE id = ?",
        (vistos, estado, calificacion, resena, seguimiento_id),
    )
    conn.commit()
    return estado


def sumar_episodio(conn: sqlite3.Connection, seguimiento_id: int) -> str:
    fila = _seguimiento(conn, seguimiento_id)
    return actualizar_seguimiento(conn, seguimiento_id, fila["vistos"] + 1, fila["calificacion"], fila["resena"])


def quitar_de_lista(conn: sqlite3.Connection, seguimiento_id: int) -> None:
    conn.execute("DELETE FROM seguimiento WHERE id = ?", (seguimiento_id,))
    conn.commit()


def lista_de(conn: sqlite3.Connection, perfil_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT s.*, se.titulo, se.temporada, se.episodios, se.estudio
           FROM seguimiento s JOIN series se ON se.id = s.serie_id
           WHERE s.perfil_id = ?
           ORDER BY CASE s.estado WHEN 'Viendo' THEN 0 WHEN 'Pendiente' THEN 1 ELSE 2 END, se.titulo, se.anio, se.id""",
        (perfil_id,),
    ).fetchall()


def resumen_de(conn: sqlite3.Connection, perfil_id: int) -> dict:
    fila = conn.execute(
        """SELECT COUNT(*) AS series,
                  COALESCE(SUM(vistos), 0) AS episodios,
                  COALESCE(SUM(estado = 'Completada'), 0) AS completadas,
                  COALESCE(SUM(estado = 'Viendo'), 0) AS viendo,
                  COALESCE(SUM(estado = 'Pendiente'), 0) AS pendientes,
                  ROUND(AVG(calificacion), 1) AS promedio
           FROM seguimiento WHERE perfil_id = ?""",
        (perfil_id,),
    ).fetchone()
    return dict(fila)
