"""Pruebas de las pantallas con el catálogo real cargado."""
import pytest

PANTALLAS = ["/", "/?perfil=2", "/series", "/series/1", "/series/1/editar", "/lista/1"]


@pytest.mark.parametrize("ruta", PANTALLAS)
def test_pantallas_cargan(cliente, ruta):
    assert cliente.get(ruta).status_code == 200


def test_pantallas_no_muestran_claves_de_reglas(cliente):
    for ruta in PANTALLAS:
        assert "RN-0" not in cliente.get(ruta).get_data(as_text=True)


def test_catalogo_tiene_las_temporadas_reales(cliente):
    html = cliente.get("/series").get_data(as_text=True)
    for texto in ["Temporada 3 · Parte 2", "Temporada final · Capítulos finales (especiales)", "Temporada 3 · The Culling Game, parte 1"]:
        assert texto in html


def test_inicio_muestra_la_lista_de_ejemplo(cliente):
    html = cliente.get("/").get_data(as_text=True)
    assert "Death Note" in html and "Completada" in html


def test_ruta_inexistente_da_404(cliente):
    assert cliente.get("/series/999").status_code == 404


def test_web_mas1_suma_un_episodio(cliente):
    # En la lista de ejemplo, Chainsaw Man (registro 2) va en 8 de 12
    r = cliente.post("/lista/2/mas1", follow_redirects=True)
    assert "9 / 12 episodios" in r.get_data(as_text=True)


def test_web_avisa_vistos_de_mas_sin_clave(cliente):
    html = cliente.post("/lista/2", data={"vistos": "50"}, follow_redirects=True).get_data(as_text=True)
    assert "entre 0 y 12" in html and "RN-0" not in html


def test_web_avisa_serie_repetida(cliente):
    r = cliente.post("/lista", data={"perfil_id": "1", "serie_id": "1"}, follow_redirects=True)
    assert "ya está en tu lista" in r.get_data(as_text=True)


def test_web_avisa_serie_seguida(cliente):
    r = cliente.post("/series/1/eliminar", follow_redirects=True)
    assert "primero hay que quitarla" in r.get_data(as_text=True)


def test_web_crud_de_serie(cliente):
    cliente.post("/series", data={"titulo": "Serie de prueba", "temporada": "Temporada 1", "estudio": "Estudio X", "anio": "2026", "episodios": "10"})
    assert "Serie de prueba" in cliente.get("/series").get_data(as_text=True)
    sid = 13
    cliente.post(f"/series/{sid}/personajes", data={"nombre": "Personaje A", "rol": "Principal"})
    assert "Personaje A" in cliente.get(f"/series/{sid}").get_data(as_text=True)
    r = cliente.post(f"/series/{sid}/eliminar", follow_redirects=True)
    assert "Serie eliminada" in r.get_data(as_text=True)
