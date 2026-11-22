"""Una o más pruebas por regla de negocio; el nombre de cada prueba lleva la clave de su regla (test_rn###_...)."""
import pytest

from app import reglas
from app.reglas import ReglaNegocioError


@pytest.fixture
def datos(conn):
    """Un perfil, dos series (Chainsaw Man y Death Note) y Chainsaw Man en la lista."""
    perfil = reglas.crear_perfil(conn, "Emi")
    csm = reglas.crear_serie(conn, "Chainsaw Man", "Temporada 1", "MAPPA", 2022, 12)
    dn = reglas.crear_serie(conn, "Death Note", "Temporada única", "Madhouse", 2006, 37)
    sid = reglas.agregar_a_lista(conn, perfil, csm)
    return {"perfil": perfil, "csm": csm, "dn": dn, "sid": sid}


def _fila(conn, sid):
    return conn.execute("SELECT * FROM seguimiento WHERE id = ?", (sid,)).fetchone()


@pytest.mark.parametrize("vistos", [-1, 13])
def test_rn001_vistos_fuera_de_rango(conn, datos, vistos):
    with pytest.raises(ReglaNegocioError) as e:
        reglas.actualizar_seguimiento(conn, datos["sid"], vistos)
    assert e.value.regla == "RN-001"
    assert _fila(conn, datos["sid"])["vistos"] == 0  # no se guardó nada


def test_rn001_mas1_no_pasa_del_total(conn, datos):
    reglas.actualizar_seguimiento(conn, datos["sid"], 12)
    with pytest.raises(ReglaNegocioError):
        reglas.sumar_episodio(conn, datos["sid"])


@pytest.mark.parametrize("vistos,estado", [(0, "Pendiente"), (1, "Viendo"), (11, "Viendo"), (12, "Completada")])
def test_rn002_estado_se_calcula(conn, datos, vistos, estado):
    assert reglas.actualizar_seguimiento(conn, datos["sid"], vistos) == estado
    assert _fila(conn, datos["sid"])["estado"] == estado


def test_rn002_al_agregar_queda_pendiente(conn, datos):
    assert _fila(conn, datos["sid"])["estado"] == "Pendiente"


def test_rn003_no_se_califica_sin_ver_nada(conn, datos):
    with pytest.raises(ReglaNegocioError) as e:
        reglas.actualizar_seguimiento(conn, datos["sid"], 0, calificacion=8)
    assert e.value.regla == "RN-003"


@pytest.mark.parametrize("calificacion", [0, 11])
def test_rn003_calificacion_de_1_a_10(conn, datos, calificacion):
    with pytest.raises(ReglaNegocioError):
        reglas.actualizar_seguimiento(conn, datos["sid"], 3, calificacion=calificacion)


def test_rn003_resena_solo_al_terminar(conn, datos):
    with pytest.raises(ReglaNegocioError):
        reglas.actualizar_seguimiento(conn, datos["sid"], 6, 9, "Va muy bien")
    reglas.actualizar_seguimiento(conn, datos["sid"], 12, 9, "La terminé")
    assert _fila(conn, datos["sid"])["resena"] == "La terminé"


def test_rn004_serie_no_se_repite_en_la_lista(conn, datos):
    with pytest.raises(ReglaNegocioError) as e:
        reglas.agregar_a_lista(conn, datos["perfil"], datos["csm"])
    assert e.value.regla == "RN-004"


def test_rn004_otro_perfil_si_puede_agregarla(conn, datos):
    otro = reglas.crear_perfil(conn, "Andrea")
    reglas.agregar_a_lista(conn, otro, datos["csm"])


def test_rn005_personaje_no_se_repite_en_la_serie(conn, datos):
    reglas.crear_personaje(conn, datos["csm"], "Denji", "Principal")
    with pytest.raises(ReglaNegocioError) as e:
        reglas.crear_personaje(conn, datos["csm"], "denji", "Secundario")
    assert e.value.regla == "RN-005"


def test_rn005_mismo_nombre_en_otra_serie_si(conn, datos):
    reglas.crear_personaje(conn, datos["csm"], "L", "Secundario")
    reglas.crear_personaje(conn, datos["dn"], "L", "Principal")


def test_rn006_no_se_elimina_serie_en_una_lista(conn, datos):
    with pytest.raises(ReglaNegocioError) as e:
        reglas.eliminar_serie(conn, datos["csm"])
    assert e.value.regla == "RN-006"
    reglas.eliminar_serie(conn, datos["dn"])  # nadie la sigue: sí se elimina


def test_rn007_total_no_baja_de_lo_visto(conn, datos):
    reglas.actualizar_seguimiento(conn, datos["sid"], 10)
    with pytest.raises(ReglaNegocioError) as e:
        reglas.editar_serie(conn, datos["csm"], "Chainsaw Man", "Temporada 1", "MAPPA", 2022, 9)
    assert e.value.regla == "RN-007"


def test_rn007_al_cambiar_el_total_se_recalcula_el_estado(conn, datos):
    reglas.actualizar_seguimiento(conn, datos["sid"], 10)
    reglas.editar_serie(conn, datos["csm"], "Chainsaw Man", "Temporada 1", "MAPPA", 2022, 10)
    assert _fila(conn, datos["sid"])["estado"] == "Completada"
