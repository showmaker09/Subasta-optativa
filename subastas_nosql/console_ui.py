"""Menú, lectura de datos y formato de salida. No contiene operaciones de MongoDB."""

from __future__ import annotations

from auction_repository import Articulo, AuctionRepository, ResultadoPuja


def mostrar_menu() -> None:
    print()
    print("=== Casa de Subastas NoSQL ===")
    print("1. Consultar Catálogo en Vivo")
    print("2. Ejecutar una Puja")
    print("3. Salir")


def leer_opcion() -> str:
    return input("Seleccione una opción: ").strip()


def mostrar_catalogo(articulos: list[Articulo]) -> None:
    if not articulos:
        print("No hay artículos en el catálogo.")
        return

    filas = [
        (
            articulo.articulo_id,
            _formatear_precio(articulo.precio_actual),
            _formatear_ganador(articulo.ganador_actual),
            articulo.nombre,
        )
        for articulo in articulos
    ]
    encabezados = ("ID", "Precio actual", "Ganador actual", "Artículo")
    anchos = [
        max(len(encabezados[indice]), *(len(fila[indice]) for fila in filas))
        for indice in range(3)
    ]

    print()
    print(_linea_tabla(encabezados, anchos))
    print(_linea_tabla(("-" * anchos[0], "-" * anchos[1], "-" * anchos[2], "-" * 12), anchos))
    for fila in filas:
        print(_linea_tabla(fila, anchos))
    print(f"\n{len(filas)} artículo(s) en subasta.")


def solicitar_datos_puja() -> tuple[str, str, float] | None:
    """Pide ID, alumno y monto. Devuelve None si algún dato no es válido."""
    articulo_id = input("ID del artículo (ej. ART-001): ").strip()
    if not articulo_id:
        print("❌ El ID del artículo no puede estar vacío.")
        return None

    nombre_alumno = input("Nombre del alumno: ").strip()
    if not nombre_alumno:
        print("❌ El nombre del alumno no puede estar vacío.")
        return None

    texto_monto = input("Monto de la oferta: ").strip().replace(",", ".")
    try:
        monto = float(texto_monto)
    except ValueError:
        print("❌ El monto debe ser un número. Ejemplo: 250.50")
        return None

    if monto <= 0 or monto != monto or monto == float("inf"):
        print("❌ El monto debe ser un número positivo.")
        return None

    return articulo_id, nombre_alumno, monto


def mostrar_resultado_puja(articulo_id: str, monto: float, resultado: ResultadoPuja) -> None:
    if resultado.aceptada:
        print("✅ ¡Felicidades! Vas ganando la subasta en tiempo real.")
        print(f"   Artículo {articulo_id} actualizado a {_formatear_precio(monto)}.")
        return

    if resultado.articulo_inexistente:
        print(f"❌ No existe un artículo con el ID '{articulo_id}'.")
        return

    print("❌ Oferta rechazada. El monto es insuficiente o alguien pujó antes.")
    if resultado.precio_actual is not None:
        ganador = _formatear_ganador(resultado.ganador_actual)
        print(
            f"   Precio que debes superar: {_formatear_precio(resultado.precio_actual)} "
            f"(ganador actual: {ganador})."
        )


def ejecutar_opcion(opcion: str, repositorio: AuctionRepository) -> bool:
    """Ejecuta la opción elegida. Devuelve False cuando el usuario pide salir."""
    if opcion == "1":
        _consultar_catalogo(repositorio)
    elif opcion == "2":
        _ejecutar_puja(repositorio)
    elif opcion == "3":
        print("Gracias por participar. Hasta pronto.")
        return False
    else:
        print("❌ Opción no válida. Elija 1, 2 o 3.")
    return True


def _consultar_catalogo(repositorio: AuctionRepository) -> None:
    try:
        articulos = repositorio.listar_articulos()
    except Exception as error:
        print(f"❌ No se pudo consultar el catálogo: {error}")
        return
    mostrar_catalogo(articulos)


def _ejecutar_puja(repositorio: AuctionRepository) -> None:
    try:
        datos = solicitar_datos_puja()
    except EOFError:
        print("\n❌ Entrada cancelada.")
        return

    if datos is None:
        return

    articulo_id, nombre_alumno, monto = datos
    try:
        resultado = repositorio.realizar_puja_atomica(articulo_id, nombre_alumno, monto)
    except Exception as error:
        print(f"❌ No se pudo registrar la puja: {error}")
        return
    mostrar_resultado_puja(articulo_id, monto, resultado)


def _formatear_precio(precio: float | None) -> str:
    if precio is None:
        return "N/D"
    return f"{precio:,.2f}"


def _formatear_ganador(ganador: str | None) -> str:
    if ganador is None or ganador.strip() == "":
        return "Sin pujas"
    return ganador


def _linea_tabla(columnas: tuple[str, str, str, str], anchos: list[int]) -> str:
    id_articulo, precio, ganador, nombre = columnas
    return (
        f"{id_articulo:<{anchos[0]}}  "
        f"{precio:>{anchos[1]}}  "
        f"{ganador:<{anchos[2]}}  "
        f"{nombre}"
    )
