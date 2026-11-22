"""Pruebas de las pantallas: que carguen y que muestren el aviso de la regla incumplida."""
import pytest


@pytest.mark.parametrize("ruta", ["/", "/?perfil=2", "/series", "/series/1", "/series/1/editar", "/lista/1"])
def test_pantallas_cargan(cliente, ruta):
    assert cliente.get(ruta).status_code == 200


def test_inicio_muestra_la_lista_de_ejemplo(cliente):
    html = cliente.get("/").get_data(as_text=True)
    assert "Death Note" in html and "Completada" in html


def test_ruta_inexistente_da_404(cliente):
    assert cliente.get("/series/999").status_code == 404


def test_web_mas1_suma_un_episodio(cliente):
    # La lista de ejemplo tiene Chainsaw Man (id 2) en 8 de 12
    r = cliente.post("/lista/2/mas1", follow_redirects=True)
    assert "9 / 12 episodios" in r.get_data(as_text=True)


def test_web_rn001_avisa_vistos_de_mas(cliente):
    r = cliente.post("/lista/2", data={"vistos": "50"}, follow_redirects=True)
    assert "RN-001" in r.get_data(as_text=True)


def test_web_rn004_avisa_serie_repetida(cliente):
    r = cliente.post("/lista", data={"perfil_id": "1", "serie_id": "1"}, follow_redirects=True)
    assert "RN-004" in r.get_data(as_text=True)


def test_web_rn006_avisa_serie_seguida(cliente):
    r = cliente.post("/series/1/eliminar", follow_redirects=True)
    assert "RN-006" in r.get_data(as_text=True)


def test_web_crud_de_serie(cliente):
    cliente.post("/series", data={"titulo": "Attack on Titan", "temporada": "2", "estudio": "Wit Studio", "anio": "2017", "episodios": "12"})
    assert "T2" in cliente.get("/series").get_data(as_text=True)
    sid = 6
    cliente.post(f"/series/{sid}/personajes", data={"nombre": "Reiner Braun", "rol": "Secundario"})
    assert "Reiner Braun" in cliente.get(f"/series/{sid}").get_data(as_text=True)
    r = cliente.post(f"/series/{sid}/eliminar", follow_redirects=True)
    assert "Serie eliminada" in r.get_data(as_text=True)
