# Anime Tracker · Documentación

**Versión 2.0** · Aplicación web en Python para llevar una lista de seguimiento de anime por perfil y por temporada.

## 1. Descripción

Anime Tracker permite que cada perfil lleve su lista de temporadas: cuántos episodios ha visto, en qué estado va cada una, su calificación y su reseña. También mantiene un catálogo de series y temporadas con sus personajes.

**Usuario:** cualquier persona que quiera llevar el registro de lo que ve. Cada perfil tiene su propia lista. No hay inicio de sesión: los perfiles se eligen desde la pantalla principal.

**Datos:** la aplicación trae el catálogo real al 21 de noviembre de 2026 de Death Note, Attack on Titan, Jujutsu Kaisen y Chainsaw Man (12 temporadas emitidas en TV), tomado de AniList.

**Fuera de alcance:** películas, imágenes de las series, recomendaciones automáticas y cuentas con contraseña.

## 2. Tecnología

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.11+ |
| Web | Flask 3 con plantillas Jinja2 (HTML renderizado en el servidor) |
| Base de datos | SQLite (módulo `sqlite3` de Python) |
| Servidor en producción | Gunicorn |
| Pruebas | pytest |
| Despliegue | Render (`render.yaml`) o cualquier plataforma con `Procfile` |

## 3. Requerimientos funcionales

| Clave | Requerimiento |
|---|---|
| RF-01 | Registrar, consultar, editar y eliminar temporadas del catálogo (serie, temporada, estudio, año de estreno y episodios). |
| RF-02 | Registrar, consultar y eliminar personajes (nombre y rol). |
| RF-03 | Crear perfiles y cambiar entre ellos. |
| RF-04 | Agregar temporadas a la lista de un perfil y quitarlas. |
| RF-05 | Registrar el avance: episodios vistos, calificación y reseña; botón para sumar un episodio. |
| RF-06 | Calcular el estado de cada temporada de la lista y un resumen del perfil. |
| RF-07 | Avisar en pantalla cuando una operación no cumple una regla de negocio, sin guardar nada. |

## 4. Historias de usuario

| Clave | Historia |
|---|---|
| HU-01 | Como administrador del catálogo, quiero registrar series y temporadas con su número de episodios. |
| HU-02 | Como usuario, quiero agregar temporadas a mi lista para llevar lo que estoy viendo. |
| HU-03 | Como usuario, quiero marcar los episodios que veo para saber en qué voy. |
| HU-04 | Como usuario, quiero calificar y reseñar lo que veo para recordar qué me pareció. |
| HU-05 | Como administrador del catálogo, quiero registrar los personajes de cada serie. |

## 5. Reglas de negocio

Programadas en `app/reglas.py`. Cada una tiene pruebas en `tests/test_reglas.py` con su clave en el nombre de la prueba (por ejemplo, `test_rn004_...`).

| Clave | Regla | Severidad | Historia | Criterio de aceptación |
|---|---|---|---|---|
| RN-001 | Los episodios vistos van de 0 al total de la temporada; el botón +1 no pasa del total. | Alta | HU-03 | Dada Chainsaw Man temporada 1 con 12 episodios, cuando se capturan 13 vistos, entonces se rechaza. |
| RN-002 | El estado se calcula: Pendiente con 0 episodios, Viendo con al menos 1, Completada al llegar al total. No se captura a mano. | Media | HU-03 | Dada una temporada de 12 episodios, cuando se marcan 12 vistos, entonces el estado es Completada. |
| RN-003 | La calificación va de 1 a 10 y requiere haber visto al menos un episodio; la reseña solo se escribe con la temporada completada. | Media | HU-04 | Dada una temporada en Pendiente, cuando se califica con 8, entonces se rechaza. |
| RN-004 | Una temporada aparece una sola vez en la lista de cada perfil; otro perfil sí puede agregarla. | Media | HU-02 | Dada Death Note en la lista del perfil Demo, cuando se agrega otra vez, entonces se rechaza. |
| RN-005 | El nombre de un personaje no se repite dentro de la misma temporada del catálogo (sin distinguir mayúsculas). | Baja | HU-05 | Dado Denji en Chainsaw Man, cuando se registra «denji» en la misma temporada, entonces se rechaza. |
| RN-006 | Una temporada que está en la lista de algún perfil no se elimina del catálogo. | Alta | HU-01 | Dada Death Note en una lista, cuando se intenta eliminar, entonces se rechaza. |
| RN-007 | El total de episodios de una temporada no baja de lo visto por cualquier perfil; al cambiarlo se recalcula el estado de todos. | Media | HU-01 | Dados 10 episodios vistos, cuando el total se cambia a 9, entonces se rechaza. |

## 6. Casos de uso

### CU-01 Agregar una temporada a mi lista
- **Actor:** usuario.
- **Flujo principal:** 1) En *Mi lista* elige su perfil. 2) En *Agregar a mi lista* elige la temporada. 3) Presiona *Agregar*. 4) El sistema valida RN-004, la agrega en estado Pendiente (RN-002) y muestra «Serie agregada a tu lista.».
- **Flujo alterno:** si ya está en su lista, no se agrega y se muestra el aviso.

### CU-02 Registrar avance
- **Actor:** usuario.
- **Flujo principal:** 1) Presiona *+1 episodio*, o *Editar* para capturar episodios, calificación y reseña. 2) El sistema valida RN-001 y RN-003, calcula el estado (RN-002) y guarda.
- **Flujo alterno:** si los episodios salen del rango, se califica sin haber visto nada o se reseña sin terminar, no se guarda y se muestra el aviso.

### CU-03 Administrar el catálogo
- **Actor:** administrador del catálogo.
- **Flujo principal:** 1) En *Catálogo* registra una temporada. 2) Desde la temporada edita sus datos, agrega personajes (RN-005) o la elimina (RN-006).
- **Flujo alterno:** si el nuevo total de episodios es menor a lo que alguien ya vio, no se guarda y se muestra el aviso (RN-007).

## 7. Modelo de datos

| Tabla | Campos | Restricciones |
|---|---|---|
| series | id, titulo, temporada, estudio, anio, episodios | (título, temporada) único; episodios > 0. Cada fila es una temporada o parte emitida |
| personajes | id, serie_id, nombre, rol | se borran con su temporada; nombre único por temporada (RN-005) |
| perfiles | id, nombre | nombre único |
| seguimiento | id, perfil_id, serie_id, vistos, estado, calificacion, resena, actualizado | (perfil, temporada) único (RN-004) |

## 8. Arquitectura

```
Navegador ──HTTP──▶ rutas.py (pantallas) ──▶ reglas.py (reglas de negocio) ──▶ SQLite
                         │                          │
                    templates/ (HTML)        ReglaNegocioError (aviso en pantalla)
```

Toda escritura a la base de datos pasa por `reglas.py`, incluida la carga del catálogo. Si una operación no cumple una regla, se lanza `ReglaNegocioError` y la pantalla muestra el aviso sin guardar nada.

## 9. Pruebas

34 pruebas automatizadas con pytest, todas en verde:

- `tests/test_reglas.py`: al menos una prueba por regla RN-001 a RN-007.
- `tests/test_web.py`: que cada pantalla cargue, que no muestre claves internas de reglas, que el catálogo traiga las temporadas reales, que el CRUD funcione desde la web y que los avisos aparezcan.

Para correrlas: `pytest`. Solo las de reglas: `pytest -k rn -v`.

## 10. Despliegue

El repositorio incluye `render.yaml` para desplegar en Render con el plan gratuito (New + → Blueprint). El paso a paso está en el `README.md`. En el plan gratuito la base de datos vuelve al catálogo original cada vez que el servicio se reinicia.

## 11. Fuentes

- Temporadas, estudios, fechas de estreno y número de episodios: AniList (`https://anilist.co`, API GraphQL `https://graphql.anilist.co`), consultada el 21 de noviembre de 2026.
- El catálogo incluye solo temporadas emitidas en TV y los dos especiales de los capítulos finales de Attack on Titan; no incluye películas.

## 12. Capturas

![Mi lista](capturas/01_mi_lista.png)
*Lista del perfil Demo con su resumen, avance y estado calculado.*

![Catálogo](capturas/02_catalogo.png)
*Catálogo con las temporadas emitidas al 21 de noviembre de 2026.*

![Aviso de episodios](capturas/04_aviso_episodios.png)
*Aviso al capturar más episodios vistos que los de la temporada.*

![Aviso de calificación](capturas/05_aviso_calificacion.png)
*Aviso al calificar una temporada sin haber visto ningún episodio.*
