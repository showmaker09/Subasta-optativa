"""Gestión del cliente MongoDB: abrir, validar y cerrar la conexión."""

from __future__ import annotations

import sys

from pymongo import MongoClient
from pymongo.collection import Collection

from config import (
    COLLECTION_NAME,
    CONNECT_TIMEOUT_MS,
    DB_NAME,
    MONGO_URI,
    SERVER_SELECTION_TIMEOUT_MS,
    SOCKET_TIMEOUT_MS,
)


def conectar() -> tuple[MongoClient, Collection]:
    """Crea el cliente, hace ping y devuelve el cliente junto con la colección."""
    if not MONGO_URI:
        print(
            "❌ Error de conexión: define MONGO_URI en el archivo .env "
            "o en las variables de entorno."
        )
        sys.exit(1)

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
        connectTimeoutMS=CONNECT_TIMEOUT_MS,
        socketTimeoutMS=SOCKET_TIMEOUT_MS,
    )

    try:
        client.admin.command("ping")
        print("✅ Conexión a MongoDB Atlas establecida correctamente.")
    except Exception as error:
        print(f"❌ Error de conexión: {error}")
        client.close()
        sys.exit(1)

    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return client, collection


def cerrar_conexion(client: MongoClient | None) -> None:
    """Cierra el cliente para no dejar sockets abiertos."""
    if client is not None:
        client.close()
