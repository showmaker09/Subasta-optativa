# Instrucciones para Agente AI: Implementación del Sistema de Subastas NoSQL

**Actividad 6 – Sistema de Subastas NoSQL**

Este documento contiene instrucciones detalladas, estructuradas por arquitectura y separación de responsabilidades, para que un agente de IA (Antigravity, Grok Build, Cursor, Claude, etc.) implemente desde cero la aplicación de consola en Python.

El agente debe generar código limpio, modular, con buenas prácticas, manejo de errores y comentarios claros. **No hardcodear la URI en el código fuente** si es posible; preferir variables de entorno o un archivo `.env` / `config.py` que pueda ser ignorado.

---

## 1. Objetivo General

Desarrollar una aplicación de consola interactiva en **Python** utilizando el driver oficial `pymongo` que simula una **Casa de Subastas de Arte y Objetos Coleccionables en Tiempo Real**.

La aplicación se conecta a un clúster de **MongoDB Atlas** y permite a múltiples usuarios (alumnos) consultar el catálogo y realizar pujas de forma concurrente y atómica, sin descargar documentos para comparar precios localmente.

---

## 2. Credenciales y Parámetros de Conexión (Obligatorios)

| Parámetro              | Valor                                                                 |
|------------------------|-----------------------------------------------------------------------|
| Base de Datos          | `plataforma_subastas`                                                 |
| Colección              | `articulos`                                                           |
| URI de Conexión        | `mongodb+srv://alumno_subastas:Subasta2026@ricardoperez.bpyrczt.mongodb.net/` |
| IP Whitelist           | `0.0.0.0/0` (acceso global)                                           |

**Recomendación de seguridad**:  
Almacenar la URI en una variable de entorno (`MONGO_URI`) o en un archivo `config.py` / `.env`. Nunca dejarla hardcodeada en el repositorio final si se va a compartir.

---

## 3. Arquitectura Recomendada (Separación de Responsabilidades)

Se recomienda la siguiente estructura modular (puedes usar un solo archivo si el agente lo considera más simple para el nivel de la actividad, pero la versión modular es preferible):

```
subastas_nosql/
├── main.py                 # Punto de entrada y orquestación del menú
├── config.py               # Constantes y carga de configuración
├── database.py             # Gestión del cliente MongoClient y conexión
├── auction_repository.py   # Operaciones de acceso a datos (CRUD + atómicas)
├── console_ui.py           # Interfaz de usuario (menú e inputs)
└── requirements.txt        # pymongo
```

### Responsabilidades por capa

| Capa / Archivo              | Responsabilidad Principal                                                                 | No debe hacer                          |
|-----------------------------|-------------------------------------------------------------------------------------------|----------------------------------------|
| `config.py`                 | URI, nombre de DB, colección, timeouts                                                    | Lógica de negocio o conexión           |
| `database.py`               | Crear/cerrar `MongoClient`, ping de validación, obtener colección                        | Actualizaciones o consultas de negocio |
| `auction_repository.py`     | `listar_articulos()`, `realizar_puja_atomica()`                                           | Imprimir en consola o pedir inputs     |
| `console_ui.py`             | Mostrar menú, leer inputs, formatear salidas, llamar a repository                        | Contener lógica de MongoDB             |
| `main.py`                   | Inicializar conexión, bucle principal, cierre limpio                                      | Operaciones de datos directas          |

---

## 4. Módulo A: Inicialización y Conexión Segura

**Ubicación recomendada**: `database.py` + llamada desde `main.py`

### Requisitos obligatorios

1. Crear un `MongoClient` con timeouts adecuados:
   ```python
   client = MongoClient(
       uri,
       serverSelectionTimeoutMS=5000,
       connectTimeoutMS=10000,
       socketTimeoutMS=10000
   )
   ```

2. Validar la conexión con un comando administrativo:
   ```python
   try:
       client.admin.command('ping')
       print("✅ Conexión a MongoDB Atlas establecida correctamente.")
   except Exception as e:
       print(f"❌ Error de conexión: {e}")
       sys.exit(1)
   ```

3. Obtener la colección:
   ```python
   db = client["plataforma_subastas"]
   collection = db["articulos"]
   ```

4. Implementar un método `cerrar_conexion()` que llame a `client.close()`.

---

## 5. Módulo B: Interfaz de Consola Interactiva

El programa debe permanecer en un bucle `while True` hasta que el usuario elija salir.

### Opciones del menú

```
=== Casa de Subastas NoSQL ===
1. Consultar Catálogo en Vivo
2. Ejecutar una Puja
3. Salir
Seleccione una opción: 
```

---

### Opción 1 – Consultar Catálogo en Vivo

- Realizar un `find()` sobre la colección `articulos`.
- Mostrar de forma formateada (tabla o columnas alineadas):
  - `articulo_id` (o `_id` si no existe el campo)
  - Nombre del artículo (campo probable: `nombre`, `titulo` o `descripcion`)
  - `precio_actual`
  - `ganador_actual` (mostrar "Sin pujas" si es `None` o vacío)

**Nota**: El agente debe inspeccionar un documento de ejemplo si es posible, o asumir los nombres de campo más comunes (`articulo_id`, `nombre`, `precio_actual`, `ganador_actual`).

---

### Opción 2 – Ejecutar una Puja (Lógica Transaccional Atómica) — **CRÍTICA**

**Flujo**:

1. Solicitar:
   - ID del artículo (ej: `ART-001`)
   - Nombre del alumno
   - Monto de la oferta (float)

2. **NO descargar el documento para comparar el precio en Python**.  
   La validación debe hacerse **únicamente en el servidor** mediante un filtro condicional.

3. Usar la siguiente estructura de actualización atómica (o equivalente):

```python
filtro = {
    "articulo_id": id_buscado,
    "precio_actual": {"$lt": nueva_oferta}
}

actualizacion = {
    "$set": {
        "precio_actual": nueva_oferta,
        "ganador_actual": nombre_alumno
    },
    "$push": {
        "historial_pujas": {
            "alumno": nombre_alumno,
            "monto": nueva_oferta,
            "timestamp": datetime.utcnow()  # recomendado
        }
    }
}

resultado = collection.update_one(filtro, actualizacion)

if resultado.modified_count > 0:
    print("✅ ¡Felicidades! Vas ganando la subasta en tiempo real.")
else:
    print("❌ Oferta rechazada. El monto es insuficiente o alguien pujó antes.")
```

**Requisitos de la puja**:
- Solo se acepta si `nueva_oferta > precio_actual` (operador `$lt` en el filtro).
- Actualizar `precio_actual` y `ganador_actual`.
- Insertar la puja en el arreglo `historial_pujas` de forma atómica.
- Manejar el caso de que el artículo no exista o la puja sea insuficiente.

---

### Opción 3 – Finalizar Programa

- Romper el bucle.
- Cerrar limpiamente el `MongoClient` (`client.close()`).
- Mostrar mensaje de despedida.

---

## 6. Buenas Prácticas Obligatorias

- Manejo de excepciones (`try/except`) en conexión, lecturas y actualizaciones.
- Validación básica de inputs (que el monto sea numérico y positivo).
- Uso de `datetime` para timestamps en el historial (recomendado).
- Código legible, con funciones pequeñas y nombres descriptivos.
- Comentarios en español explicando las partes críticas (especialmente la actualización atómica).
- `requirements.txt` con `pymongo`.

---

## 7. Criterios de Aceptación

El agente habrá cumplido la actividad cuando:

1. El programa se conecta exitosamente al clúster y hace ping.
2. La Opción 1 muestra el catálogo actualizado en tiempo real.
3. La Opción 2 realiza pujas **atómicas** (dos alumnos pueden pujar simultáneamente y solo gana el mayor).
4. El historial de pujas se va acumulando correctamente en el documento.
5. El programa se cierra limpiamente sin dejar sockets abiertos.
6. El código está organizado por responsabilidades (o claramente comentado si es un solo archivo).

---

## 8. Instrucciones Finales para el Agente AI

- Genera el código completo y funcional.
- Prioriza la **actualización atómica condicionada** (es el punto más importante de la actividad).
- Si el esquema de los documentos no coincide exactamente, adapta los nombres de campo manteniendo la lógica.
- Entrega los archivos listos para ejecutarse con `python main.py` (o el nombre que elijas).
- Incluye un pequeño `README.md` con instrucciones de instalación y ejecución.

**¡Implementa ahora el Sistema de Subastas NoSQL siguiendo estrictamente esta arquitectura y requisitos!**
