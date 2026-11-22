# Anime Tracker

Aplicación web en Python (Flask + SQLite) para llevar una lista de seguimiento de anime por perfil y por temporada: qué estás viendo, cuántos episodios llevas, tu calificación y tu reseña. Incluye un catálogo de series y temporadas con sus personajes.

Catálogo incluido: **Death Note**, **Attack on Titan**, **Jujutsu Kaisen** y **Chainsaw Man**, con todas sus temporadas emitidas en TV hasta noviembre de 2026.

La documentación completa está en [`docs/Documentacion.pdf`](docs/Documentacion.pdf) (y su versión editable en [`docs/Documentacion.md`](docs/Documentacion.md)).

## Qué hace

| Módulo | Operaciones |
|---|---|
| Perfiles | Crear perfiles y cambiar entre ellos (cada uno con su lista) |
| Mi lista | Agregar series, sumar episodios (+1), editar avance, calificar, reseñar y quitar |
| Catálogo | Alta, consulta, edición y baja de series y temporadas |
| Personajes | Alta, consulta y baja de personajes por serie |
| Resumen | Series en la lista, completadas, viendo, episodios vistos y calificación promedio |

## Catálogo incluido

Al arrancar por primera vez carga el catálogo real al 21 de noviembre de 2026, tomado de [AniList](https://anilist.co): 12 temporadas emitidas en TV con su estudio, año de estreno y número de episodios; 16 personajes; y un perfil «Demo» con avance de ejemplo (sin calificaciones ni reseñas).

| Serie | Temporada | Estudio | Año | Episodios |
|---|---|---|---|---|
| Death Note | Temporada única | Madhouse | 2006 | 37 |
| Attack on Titan | Temporada 1 | Wit Studio | 2013 | 25 |
| Attack on Titan | Temporada 2 | Wit Studio | 2017 | 12 |
| Attack on Titan | Temporada 3 · Parte 1 | Wit Studio | 2018 | 12 |
| Attack on Titan | Temporada 3 · Parte 2 | Wit Studio | 2019 | 10 |
| Attack on Titan | Temporada final · Parte 1 | MAPPA | 2020 | 16 |
| Attack on Titan | Temporada final · Parte 2 | MAPPA | 2022 | 12 |
| Attack on Titan | Temporada final · Capítulos finales (especiales) | MAPPA | 2023 | 2 |
| Jujutsu Kaisen | Temporada 1 | MAPPA | 2020 | 24 |
| Jujutsu Kaisen | Temporada 2 | MAPPA | 2023 | 23 |
| Jujutsu Kaisen | Temporada 3 · The Culling Game, parte 1 | MAPPA | 2026 | 12 |
| Chainsaw Man | Temporada 1 | MAPPA | 2022 | 12 |

No se incluyen películas (por ejemplo, *Chainsaw Man – The Movie: Reze Arc*, 2025) porque la aplicación lleva temporadas por episodios. AniList ya registra la parte 2 de *The Culling Game* de Jujutsu Kaisen como próxima, pero sin fecha de estreno ni episodios; se puede agregar desde *Catálogo* cuando salga.

## Reglas de negocio

Están definidas en [`reglas_negocio.toml`](reglas_negocio.toml), programadas en [`app/reglas.py`](app/reglas.py) y documentadas en la [documentación](docs/Documentacion.md); cada una tiene pruebas en [`tests/test_reglas.py`](tests/test_reglas.py) con su clave en el nombre (por ejemplo, `test_rn002_...`). Cuando una operación no las cumple, la pantalla avisa y no guarda nada.

| Clave | Regla |
|---|---|
| RN-001 | Los episodios vistos van de 0 al total de la temporada |
| RN-002 | El estado (Pendiente, Viendo, Completada) se calcula con los episodios vistos; no se captura a mano |
| RN-003 | Calificación de 1 a 10 solo si viste al menos un episodio; la reseña solo con la temporada completada |
| RN-004 | Una temporada aparece una sola vez en la lista de cada perfil |
| RN-005 | El nombre de un personaje no se repite dentro de la misma temporada del catálogo |
| RN-006 | No se elimina una temporada que está en la lista de algún perfil |
| RN-007 | El total de episodios de una temporada no puede bajar de lo que alguien ya vio |

## Ejecutar en local

Requiere Python 3.11 o más reciente.

```bash
python -m venv .venv
source .venv/bin/activate            # En Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
flask --app app run --debug          # http://127.0.0.1:5000
```

La base de datos se crea sola en `instance/anime.db`. Para volver al catálogo original, borra ese archivo.

## Pruebas

```bash
pytest                       # todas (34)
pytest -k rn -v              # solo las de reglas de negocio
```

## Desplegar en Render (gratis)

1. Sube este proyecto a un repositorio de GitHub.
2. Entra a [render.com](https://render.com), inicia sesión con GitHub y elige **New + → Blueprint**.
3. Selecciona el repositorio. Render lee [`render.yaml`](render.yaml) y crea el servicio web.
4. Al terminar el despliegue, Render da una dirección pública del tipo `https://anime-tracker.onrender.com`.

En el plan gratuito el disco no es permanente: cuando el servicio se reinicia, la base de datos vuelve al catálogo original. Para una demo esto no es problema.

Otras plataformas que lean un `Procfile` (Railway, Heroku) sirven igual; el comando de arranque es `gunicorn "app:create_app()"`.

### Variables de entorno

| Variable | Para qué | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Firma de los mensajes de la sesión | Una clave de desarrollo |
| `DATABASE` | Ruta del archivo SQLite | `instance/anime.db` |
| `DATOS_EJEMPLO` | `1` carga el catálogo si la base está vacía; `0` arranca vacía | `1` |

## Estructura

```
app/
  __init__.py      create_app(): configuración de Flask
  db.py            tablas SQLite y catálogo incluido
  reglas.py        reglas de negocio (toda escritura pasa por aquí)
  rutas.py         pantallas y formularios
  templates/       HTML (Jinja2)
  static/          estilos
tests/
  test_reglas.py   pruebas de cada regla RN-###
  test_web.py      pruebas de las pantallas
docs/              documentación y capturas
reglas_negocio.toml   reglas de negocio (clave, descripción, severidad, historia y criterio)
render.yaml · Procfile
```

Proyecto escolar sin relación oficial con las series, sus autores ni sus estudios. No incluye imágenes ni material de las series; solo títulos, número de episodios y nombres de personajes.
