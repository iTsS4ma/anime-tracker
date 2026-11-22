"""Conexión a SQLite, creación de tablas y datos de ejemplo."""
import sqlite3

from flask import Flask, current_app, g

ESQUEMA = """
CREATE TABLE IF NOT EXISTS series (
    id         INTEGER PRIMARY KEY,
    titulo     TEXT NOT NULL,
    temporada  INTEGER NOT NULL DEFAULT 1,
    estudio    TEXT NOT NULL,
    anio       INTEGER NOT NULL,
    episodios  INTEGER NOT NULL CHECK (episodios > 0),
    UNIQUE (titulo, temporada)
);
CREATE TABLE IF NOT EXISTS personajes (
    id        INTEGER PRIMARY KEY,
    serie_id  INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    nombre    TEXT NOT NULL,
    rol       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS perfiles (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS seguimiento (
    id            INTEGER PRIMARY KEY,
    perfil_id     INTEGER NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    serie_id      INTEGER NOT NULL REFERENCES series(id),
    vistos        INTEGER NOT NULL DEFAULT 0,
    estado        TEXT NOT NULL,
    calificacion  INTEGER,
    resena        TEXT,
    actualizado   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (perfil_id, serie_id)
);
"""

# Datos de ejemplo: series reales con su número de episodios por temporada.
SERIES = [  # (título, temporada, estudio, año, episodios)
    ("Death Note", 1, "Madhouse", 2006, 37),
    ("Attack on Titan", 1, "Wit Studio", 2013, 25),
    ("Jujutsu Kaisen", 1, "MAPPA", 2020, 24),
    ("Jujutsu Kaisen", 2, "MAPPA", 2023, 23),
    ("Chainsaw Man", 1, "MAPPA", 2022, 12),
]
PERSONAJES = {  # título → [(nombre, rol)]
    "Death Note": [("Light Yagami", "Principal"), ("L", "Principal"), ("Ryuk", "Secundario"), ("Misa Amane", "Secundario")],
    "Attack on Titan": [("Eren Yeager", "Principal"), ("Mikasa Ackerman", "Principal"), ("Armin Arlert", "Principal"), ("Levi", "Secundario")],
    "Jujutsu Kaisen": [("Yuji Itadori", "Principal"), ("Megumi Fushiguro", "Principal"), ("Nobara Kugisaki", "Principal"), ("Satoru Gojo", "Secundario")],
    "Chainsaw Man": [("Denji", "Principal"), ("Power", "Principal"), ("Aki Hayakawa", "Principal"), ("Makima", "Secundario")],
}
LISTA_DEMO = [  # (título, temporada, vistos, calificación, reseña)
    ("Death Note", 1, 37, 10, "Un duelo de inteligencia de principio a fin."),
    ("Chainsaw Man", 1, 8, 9, None),
    ("Jujutsu Kaisen", 1, 24, 9, "Peleas muy bien animadas."),
    ("Jujutsu Kaisen", 2, 0, None, None),
    ("Attack on Titan", 1, 13, 8, None),
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def conectar(ruta: str) -> sqlite3.Connection:
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def cerrar_db(_error=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def crear_tablas(conn: sqlite3.Connection, datos_ejemplo: bool = True) -> None:
    conn.executescript(ESQUEMA)
    vacia = conn.execute("SELECT COUNT(*) FROM series").fetchone()[0] == 0
    if datos_ejemplo and vacia:
        cargar_ejemplo(conn)
    conn.commit()


def cargar_ejemplo(conn: sqlite3.Connection) -> None:
    from . import reglas

    ids = {}
    for titulo, temporada, estudio, anio, episodios in SERIES:
        ids[(titulo, temporada)] = reglas.crear_serie(conn, titulo, temporada, estudio, anio, episodios)
    for titulo, personajes in PERSONAJES.items():
        for nombre, rol in personajes:
            reglas.crear_personaje(conn, ids[(titulo, 1)], nombre, rol)
    perfil = reglas.crear_perfil(conn, "Demo")
    reglas.crear_perfil(conn, "Invitado")
    for titulo, temporada, vistos, calif, resena in LISTA_DEMO:
        sid = reglas.agregar_a_lista(conn, perfil, ids[(titulo, temporada)])
        reglas.actualizar_seguimiento(conn, sid, vistos, calif, resena)


def init_app(app: Flask) -> None:
    app.teardown_appcontext(cerrar_db)
    conn = conectar(app.config["DATABASE"])
    try:
        crear_tablas(conn, app.config["DATOS_EJEMPLO"])
    finally:
        conn.close()
