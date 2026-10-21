"""Acceso a datos del catálogo y pujas atómicas. No imprime ni lee la consola."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection


@dataclass(frozen=True)
class Articulo:
    articulo_id: str
    nombre: str
    precio_actual: float | None
    ganador_actual: str | None


@dataclass(frozen=True)
class ResultadoPuja:
    """Resultado de una puja ya decidida por el servidor."""

    aceptada: bool
    articulo_inexistente: bool
    precio_actual: float | None = None
    ganador_actual: str | None = None


class AuctionRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def listar_articulos(self) -> list[Articulo]:
        """Lee el catálogo en vivo. No incluye el historial, que puede crecer mucho."""
        proyeccion = {
            "articulo_id": 1,
            "nombre": 1,
            "titulo": 1,
            "descripcion": 1,
            "precio_actual": 1,
            "ganador_actual": 1,
        }
        cursor = self._collection.find({}, proyeccion).sort("articulo_id", 1)
        return [_a_articulo(documento) for documento in cursor]

    def realizar_puja_atomica(
        self,
        articulo_id: str,
        nombre_alumno: str,
        nueva_oferta: float,
    ) -> ResultadoPuja:
        """Acepta la puja solo si el servidor ve precio_actual estrictamente menor.

        La comparación ocurre dentro del filtro de update_one. Así dos alumnos
        pueden pujar a la vez y solo una escritura modifica el documento: la
        oferta que todavía supera el precio guardado. No se descarga el
        documento para decidir el ganador en Python.
        """
        # Condición atómica: el documento solo coincide si la oferta es mayor.
        filtro = {
            "articulo_id": articulo_id,
            "precio_actual": {"$lt": nueva_oferta},
        }
        # El clúster ya guarda la hora de la puja en el campo "fecha".
        ahora = datetime.now(timezone.utc)
        actualizacion = {
            "$set": {
                "precio_actual": nueva_oferta,
                "ganador_actual": nombre_alumno,
            },
            "$push": {
                "historial_pujas": {
                    "alumno": nombre_alumno,
                    "monto": nueva_oferta,
                    "fecha": ahora,
                }
            },
        }

        resultado = self._collection.update_one(filtro, actualizacion)
        if resultado.modified_count > 0:
            return ResultadoPuja(aceptada=True, articulo_inexistente=False)

        # Esta lectura no decide la puja. Solo explica un rechazo ya ocurrido.
        # Si hay varios documentos con el mismo ID, se informa el precio más bajo.
        existente = self._collection.find_one(
            {"articulo_id": articulo_id},
            {"precio_actual": 1, "ganador_actual": 1},
            sort=[("precio_actual", 1)],
        )
        if existente is None:
            return ResultadoPuja(aceptada=False, articulo_inexistente=True)

        return ResultadoPuja(
            aceptada=False,
            articulo_inexistente=False,
            precio_actual=_a_float(existente.get("precio_actual")),
            ganador_actual=_a_texto_o_none(existente.get("ganador_actual")),
        )


def _a_articulo(documento: dict[str, Any]) -> Articulo:
    articulo_id = documento.get("articulo_id")
    if articulo_id is None or str(articulo_id).strip() == "":
        articulo_id = documento.get("_id")

    nombre = None
    for campo in ("nombre", "titulo", "descripcion"):
        valor = documento.get(campo)
        if valor is not None and str(valor).strip() != "":
            nombre = str(valor)
            break

    return Articulo(
        articulo_id=str(articulo_id),
        nombre=nombre or "(sin nombre)",
        precio_actual=_a_float(documento.get("precio_actual")),
        ganador_actual=_a_texto_o_none(documento.get("ganador_actual")),
    )


def _a_float(valor: Any) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _a_texto_o_none(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None
