"""Conexión a SQLite, creación de tablas y datos de ejemplo."""
import sqlite3

from flask import Flask, current_app, g

ESQUEMA = """
CREATE TABLE IF NOT EXISTS series (
    id         INTEGER PRIMARY KEY,
    titulo     TEXT NOT NULL,
    temporada  TEXT NOT NULL,
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

# Catálogo real al 21 de noviembre de 2026: temporadas emitidas en TV con su número de episodios.
# Fuente: AniList (anilist.co), consultada el 21 de noviembre de 2026.
SERIES = [  # (título, temporada, estudio, año de estreno, episodios)
    ("Death Note", "Temporada única", "Madhouse", 2006, 37),
    ("Attack on Titan", "Temporada 1", "Wit Studio", 2013, 25),
    ("Attack on Titan", "Temporada 2", "Wit Studio", 2017, 12),
    ("Attack on Titan", "Temporada 3 · Parte 1", "Wit Studio", 2018, 12),
    ("Attack on Titan", "Temporada 3 · Parte 2", "Wit Studio", 2019, 10),
    ("Attack on Titan", "Temporada final · Parte 1", "MAPPA", 2020, 16),
    ("Attack on Titan", "Temporada final · Parte 2", "MAPPA", 2022, 12),
    ("Attack on Titan", "Temporada final · Capítulos finales (especiales)", "MAPPA", 2023, 2),
    ("Jujutsu Kaisen", "Temporada 1", "MAPPA", 2020, 24),
    ("Jujutsu Kaisen", "Temporada 2", "MAPPA", 2023, 23),
    ("Jujutsu Kaisen", "Temporada 3 · The Culling Game, parte 1", "MAPPA", 2026, 12),
    ("Chainsaw Man", "Temporada 1", "MAPPA", 2022, 12),
]
PERSONAJES = {  # título → [(nombre, rol)]; se registran en la primera temporada de cada serie
    "Death Note": [("Light Yagami", "Principal"), ("L", "Principal"), ("Ryuk", "Secundario"), ("Misa Amane", "Secundario")],
    "Attack on Titan": [("Eren Yeager", "Principal"), ("Mikasa Ackerman", "Principal"), ("Armin Arlert", "Principal"), ("Levi", "Secundario")],
    "Jujutsu Kaisen": [("Yuji Itadori", "Principal"), ("Megumi Fushiguro", "Principal"), ("Nobara Kugisaki", "Principal"), ("Satoru Gojo", "Secundario")],
    "Chainsaw Man": [("Denji", "Principal"), ("Power", "Principal"), ("Aki Hayakawa", "Principal"), ("Makima", "Secundario")],
}
# Lista del perfil de demostración: solo avance (sin calificaciones ni reseñas, que son opinión de cada usuario).
LISTA_DEMO = [  # (título, temporada, episodios vistos)
    ("Death Note", "Temporada única", 37),
    ("Chainsaw Man", "Temporada 1", 8),
    ("Jujutsu Kaisen", "Temporada 1", 24),
    ("Jujutsu Kaisen", "Temporada 2", 23),
    ("Jujutsu Kaisen", "Temporada 3 · The Culling Game, parte 1", 0),
    ("Attack on Titan", "Temporada 1", 13),
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
    primera = {}
    for (titulo, temporada), sid in ids.items():
        primera.setdefault(titulo, sid)
    for titulo, personajes in PERSONAJES.items():
        for nombre, rol in personajes:
            reglas.crear_personaje(conn, primera[titulo], nombre, rol)
    perfil = reglas.crear_perfil(conn, "Demo")
    reglas.crear_perfil(conn, "Invitado")
    for titulo, temporada, vistos in LISTA_DEMO:
        sid = reglas.agregar_a_lista(conn, perfil, ids[(titulo, temporada)])
        reglas.actualizar_seguimiento(conn, sid, vistos)


def init_app(app: Flask) -> None:
    app.teardown_appcontext(cerrar_db)
    conn = conectar(app.config["DATABASE"])
    try:
        crear_tablas(conn, app.config["DATOS_EJEMPLO"])
    finally:
        conn.close()
