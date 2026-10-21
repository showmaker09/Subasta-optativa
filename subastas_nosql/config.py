"""Constantes de conexión. La URI se lee del entorno o de un archivo .env."""

from __future__ import annotations

import os
from pathlib import Path


def _cargar_env(ruta: Path) -> None:
    """Carga pares CLAVE=valor sin pisar variables que ya existan en el entorno."""
    if not ruta.is_file():
        return

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(Path(__file__).resolve().parent / ".env")

# Nunca dejar la URI escrita en este módulo: viene de MONGO_URI.
MONGO_URI = os.environ.get("MONGO_URI", "").strip()
DB_NAME = os.environ.get("MONGO_DB", "plataforma_subastas").strip() or "plataforma_subastas"
COLLECTION_NAME = os.environ.get("MONGO_COLLECTION", "articulos").strip() or "articulos"

# Timeouts exigidos por la actividad (milisegundos).
SERVER_SELECTION_TIMEOUT_MS = 5000
CONNECT_TIMEOUT_MS = 10000
SOCKET_TIMEOUT_MS = 10000
