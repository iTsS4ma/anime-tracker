# Anime Tracker

Aplicación web en Python (Flask + SQLite) para llevar una lista de seguimiento de anime por perfil: qué series estás viendo, cuántos episodios llevas, tu calificación y tu reseña. Incluye un catálogo de series con sus personajes.

Series de ejemplo: **Death Note**, **Attack on Titan**, **Jujutsu Kaisen** y **Chainsaw Man**.

La documentación completa está en [`docs/Documentacion.pdf`](docs/Documentacion.pdf) (y su versión editable en [`docs/Documentacion.md`](docs/Documentacion.md)).

## Qué hace

| Módulo | Operaciones |
|---|---|
| Perfiles | Crear perfiles y cambiar entre ellos (cada uno con su lista) |
| Mi lista | Agregar series, sumar episodios (+1), editar avance, calificar, reseñar y quitar |
| Catálogo | Alta, consulta, edición y baja de series y temporadas |
| Personajes | Alta, consulta y baja de personajes por serie |
| Resumen | Series en la lista, completadas, viendo, episodios vistos y calificación promedio |

Al arrancar por primera vez carga datos de ejemplo: 5 temporadas con su número real de episodios, 16 personajes y un perfil «Demo» con su lista.

| Serie | Temporada | Estudio | Año | Episodios |
|---|---|---|---|---|
| Death Note | 1 | Madhouse | 2006 | 37 |
| Attack on Titan | 1 | Wit Studio | 2013 | 25 |
| Jujutsu Kaisen | 1 | MAPPA | 2020 | 24 |
| Jujutsu Kaisen | 2 | MAPPA | 2023 | 23 |
| Chainsaw Man | 1 | MAPPA | 2022 | 12 |

## Reglas de negocio

Están programadas en [`app/reglas.py`](app/reglas.py) y cada una tiene pruebas en [`tests/test_reglas.py`](tests/test_reglas.py) con su clave en el nombre (por ejemplo, `test_rn002_...`). Cuando una operación incumple una regla, la pantalla muestra el aviso con su clave (por ejemplo, «RN-004 · Death Note T1 ya está en tu lista.»).

| Clave | Regla |
|---|---|
| RN-001 | Los episodios vistos van de 0 al total de la temporada |
| RN-002 | El estado (Pendiente, Viendo, Completada) se calcula con los episodios vistos; no se captura a mano |
| RN-003 | Calificación de 1 a 10 solo si viste al menos un episodio; la reseña solo con la serie completada |
| RN-004 | Una serie aparece una sola vez en la lista de cada perfil |
| RN-005 | El nombre de un personaje no se repite dentro de la misma serie |
| RN-006 | No se elimina una serie que está en la lista de algún perfil |
| RN-007 | El total de episodios de una serie no puede bajar de lo que alguien ya vio |

## Ejecutar en local

Requiere Python 3.11 o más reciente.

```bash
python -m venv .venv
source .venv/bin/activate            # En Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
flask --app app run --debug          # http://127.0.0.1:5000
```

La base de datos se crea sola en `instance/anime.db`. Para empezar de cero, borra ese archivo.

## Pruebas

```bash
pytest                       # todas (32)
pytest -k rn -v              # solo las de reglas de negocio
```

## Desplegar en Render (gratis)

1. Sube este proyecto a un repositorio de GitHub.
2. Entra a [render.com](https://render.com), inicia sesión con GitHub y elige **New + → Blueprint**.
3. Selecciona el repositorio. Render lee [`render.yaml`](render.yaml) y crea el servicio web.
4. Al terminar el despliegue, Render da una dirección pública del tipo `https://anime-tracker.onrender.com`.

En el plan gratuito el disco no es permanente: cuando el servicio se reinicia, la base de datos vuelve a los datos de ejemplo. Para una demo esto no es problema.

Otras plataformas que lean un `Procfile` (Railway, Heroku) sirven igual; el comando de arranque es `gunicorn "app:create_app()"`.

### Variables de entorno

| Variable | Para qué | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Firma de los mensajes de la sesión | Una clave de desarrollo |
| `DATABASE` | Ruta del archivo SQLite | `instance/anime.db` |
| `DATOS_EJEMPLO` | `1` carga los datos de ejemplo si la base está vacía; `0` arranca vacía | `1` |

## Estructura

```
app/
  __init__.py      create_app(): configuración de Flask
  db.py            tablas SQLite y datos de ejemplo
  reglas.py        reglas de negocio (toda escritura pasa por aquí)
  rutas.py         pantallas y formularios
  templates/       HTML (Jinja2)
  static/          estilos
tests/
  test_reglas.py   pruebas de cada regla RN-###
  test_web.py      pruebas de las pantallas
docs/              documentación y capturas
render.yaml · Procfile
```

Proyecto escolar sin relación oficial con las series, sus autores ni sus estudios. No incluye imágenes ni material de las series; solo títulos, número de episodios y nombres de personajes.
