"""Pantallas de la aplicación."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from . import reglas
from .db import get_db
from .reglas import DatoInvalido, ReglaNegocioError

bp = Blueprint("anime", __name__)


def _intentar(accion, exito: str | None) -> bool:
    """Ejecuta una operación y muestra el resultado; devuelve True si salió bien."""
    try:
        resultado = accion()
    except (ReglaNegocioError, DatoInvalido) as e:
        flash(str(e), "error")
        return False
    if exito:
        flash(exito.format(resultado=resultado), "ok")
    return True


def _uno(sql: str, *args):
    fila = get_db().execute(sql, args).fetchone()
    if fila is None:
        abort(404)
    return fila


# ---------------------------------------------------------------- Mi lista
@bp.get("/")
def inicio():
    conn = get_db()
    perfiles = conn.execute("SELECT * FROM perfiles ORDER BY id").fetchall()
    if not perfiles:
        return render_template("inicio.html", perfil=None, perfiles=[], lista=[], disponibles=[], resumen=None)
    pid = request.args.get("perfil", type=int) or perfiles[0]["id"]
    perfil = next((p for p in perfiles if p["id"] == pid), None) or abort(404)
    disponibles = conn.execute(
        "SELECT * FROM series WHERE id NOT IN (SELECT serie_id FROM seguimiento WHERE perfil_id = ?) ORDER BY titulo, anio, id",
        (pid,),
    ).fetchall()
    return render_template(
        "inicio.html",
        perfil=perfil,
        perfiles=perfiles,
        lista=reglas.lista_de(conn, pid),
        disponibles=disponibles,
        resumen=reglas.resumen_de(conn, pid),
    )


@bp.post("/perfiles")
def crear_perfil():
    ok = _intentar(lambda: reglas.crear_perfil(get_db(), request.form.get("nombre")), "Perfil creado.")
    if ok:
        pid = get_db().execute("SELECT MAX(id) FROM perfiles").fetchone()[0]
        return redirect(url_for(".inicio", perfil=pid))
    return redirect(url_for(".inicio"))


@bp.post("/lista")
def agregar():
    f = request.form
    _intentar(lambda: reglas.agregar_a_lista(get_db(), f.get("perfil_id"), f.get("serie_id")), "Serie agregada a tu lista.")
    return redirect(url_for(".inicio", perfil=f.get("perfil_id")))


@bp.post("/lista/<int:sid>/mas1")
def mas1(sid):
    s = _uno("SELECT perfil_id FROM seguimiento WHERE id = ?", sid)
    _intentar(lambda: reglas.sumar_episodio(get_db(), sid), "Episodio sumado · Estado: {resultado}.")
    return redirect(url_for(".inicio", perfil=s["perfil_id"]))


@bp.route("/lista/<int:sid>", methods=["GET", "POST"])
def avance(sid):
    s = _uno(
        """SELECT s.*, se.titulo, se.temporada, se.episodios, p.nombre AS perfil
           FROM seguimiento s JOIN series se ON se.id = s.serie_id JOIN perfiles p ON p.id = s.perfil_id
           WHERE s.id = ?""",
        sid,
    )
    if request.method == "POST":
        f = request.form
        accion = lambda: reglas.actualizar_seguimiento(get_db(), sid, f.get("vistos"), f.get("calificacion"), f.get("resena"))
        if _intentar(accion, "Avance guardado · Estado: {resultado}."):
            return redirect(url_for(".inicio", perfil=s["perfil_id"]))
    form = request.form if request.method == "POST" else s
    return render_template("avance.html", s=s, form=form)


@bp.post("/lista/<int:sid>/quitar")
def quitar(sid):
    s = _uno("SELECT perfil_id FROM seguimiento WHERE id = ?", sid)
    _intentar(lambda: reglas.quitar_de_lista(get_db(), sid), "Serie quitada de tu lista.")
    return redirect(url_for(".inicio", perfil=s["perfil_id"]))


# ---------------------------------------------------------------- Catálogo
@bp.route("/series", methods=["GET", "POST"])
def series():
    conn = get_db()
    if request.method == "POST":
        f = request.form
        accion = lambda: reglas.crear_serie(conn, f.get("titulo"), f.get("temporada"), f.get("estudio"), f.get("anio"), f.get("episodios"))
        if _intentar(accion, "Serie agregada al catálogo."):
            return redirect(url_for(".series"))
    filas = conn.execute(
        """SELECT se.*, (SELECT COUNT(*) FROM personajes p WHERE p.serie_id = se.id) AS personajes,
                  (SELECT COUNT(*) FROM seguimiento s WHERE s.serie_id = se.id) AS seguidores
           FROM series se ORDER BY titulo, anio, id"""
    ).fetchall()
    return render_template("series.html", series=filas, form=request.form)


@bp.get("/series/<int:serie_id>")
def serie(serie_id):
    conn = get_db()
    se = _uno("SELECT * FROM series WHERE id = ?", serie_id)
    personajes = conn.execute("SELECT * FROM personajes WHERE serie_id = ? ORDER BY rol, nombre", (serie_id,)).fetchall()
    seguidores = conn.execute(
        """SELECT p.nombre, s.vistos, s.estado, s.calificacion FROM seguimiento s JOIN perfiles p ON p.id = s.perfil_id
           WHERE s.serie_id = ? ORDER BY p.nombre""",
        (serie_id,),
    ).fetchall()
    return render_template("serie.html", se=se, personajes=personajes, seguidores=seguidores, roles=reglas.ROLES)


@bp.route("/series/<int:serie_id>/editar", methods=["GET", "POST"])
def editar_serie(serie_id):
    se = _uno("SELECT * FROM series WHERE id = ?", serie_id)
    if request.method == "POST":
        f = request.form
        accion = lambda: reglas.editar_serie(get_db(), serie_id, f.get("titulo"), f.get("temporada"), f.get("estudio"), f.get("anio"), f.get("episodios"))
        if _intentar(accion, "Serie actualizada."):
            return redirect(url_for(".serie", serie_id=serie_id))
    return render_template("serie_editar.html", se=se, form=request.form or se)


@bp.post("/series/<int:serie_id>/eliminar")
def eliminar_serie(serie_id):
    if _intentar(lambda: reglas.eliminar_serie(get_db(), serie_id), "Serie eliminada del catálogo."):
        return redirect(url_for(".series"))
    return redirect(url_for(".serie", serie_id=serie_id))


@bp.post("/series/<int:serie_id>/personajes")
def crear_personaje(serie_id):
    f = request.form
    _intentar(lambda: reglas.crear_personaje(get_db(), serie_id, f.get("nombre"), f.get("rol")), "Personaje agregado.")
    return redirect(url_for(".serie", serie_id=serie_id))


@bp.post("/personajes/<int:pid>/eliminar")
def eliminar_personaje(pid):
    p = _uno("SELECT serie_id FROM personajes WHERE id = ?", pid)
    _intentar(lambda: reglas.eliminar_personaje(get_db(), pid), "Personaje eliminado.")
    return redirect(url_for(".serie", serie_id=p["serie_id"]))


@bp.app_errorhandler(404)
def no_encontrado(_e):
    return render_template("404.html"), 404
