"""Punto de entrada: conecta, muestra el menú y cierra el cliente al salir."""

from __future__ import annotations

import sys

from auction_repository import AuctionRepository
from console_ui import ejecutar_opcion, mostrar_menu, leer_opcion
from database import cerrar_conexion, conectar


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    client = None
    try:
        client, collection = conectar()
        repositorio = AuctionRepository(collection)

        while True:
            mostrar_menu()
            try:
                opcion = leer_opcion()
            except EOFError:
                print("\nGracias por participar. Hasta pronto.")
                break

            if not ejecutar_opcion(opcion, repositorio):
                break
    except KeyboardInterrupt:
        print("\nInterrupción recibida. Cerrando el programa.")
    finally:
        cerrar_conexion(client)


if __name__ == "__main__":
    main()
