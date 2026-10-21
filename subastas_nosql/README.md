# Casa de Subastas NoSQL

Aplicación de consola en Python para consultar el catálogo y pujar en tiempo real sobre MongoDB Atlas. La puja no compara el precio en el cliente: `update_one` solo modifica el artículo si `precio_actual` es menor que la oferta.

## Requisitos

- Python 3.10 o superior
- Acceso de red al clúster (la IP `0.0.0.0/0` ya está habilitada en Atlas)

## Instalación

Desde esta carpeta:

```powershell
pip install -r requirements.txt
```

La URI vive en `.env` (`MONGO_URI`), no en el código. Si clonas el proyecto sin ese archivo, copia `.env.example` a `.env` y completa la URI.

## Ejecución

```powershell
python main.py
```

Menú:

1. Consultar Catálogo en Vivo. Muestra ID, nombre, precio actual y ganador. Si no hay ganador, aparece `Sin pujas`.
2. Ejecutar una Puja. Pide el ID (por ejemplo `ART-010`), el nombre del alumno y un monto mayor que el precio actual.
3. Salir. Cierra el `MongoClient`.

## Puja atómica

El filtro de la actualización es:

```python
{"articulo_id": id_buscado, "precio_actual": {"$lt": nueva_oferta}}
```

Si nadie más se adelantó y el monto supera el precio guardado, el servidor actualiza `precio_actual`, `ganador_actual` y agrega la puja a `historial_pujas` en la misma operación. Si el artículo no existe, o la oferta no supera el precio, la puja se rechaza y el documento no cambia.

## Estructura

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Arranque, bucle del menú y cierre de la conexión |
| `config.py` | URI, base de datos, colección y timeouts |
| `database.py` | `MongoClient`, ping y `cerrar_conexion()` |
| `auction_repository.py` | `listar_articulos()` y `realizar_puja_atomica()` |
| `console_ui.py` | Menú, validación de entradas y formato de la tabla |

Base de datos: `plataforma_subastas`. Colección: `articulos`.
