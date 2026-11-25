"""Catálogo de modalidades (sincronizado con rag-kb/data/modalidades.jsonl)."""

MODALIDADES = [
    {"id": "regular", "nombre": "Regular", "match": "Regular"},
    {"id": "segunda_carrera", "nombre": "Segunda Carrera", "match": "Segunda Carrera"},
    {"id": "traslado_externo", "nombre": "Traslado Externo", "match": "Traslado Externo"},
    {"id": "traslado_interno", "nombre": "Traslado Interno", "match": "Traslado Interno"},
    {"id": "primeros_puestos", "nombre": "Primeros Puestos", "match": "Primeros Puestos"},
    {"id": "deportistas_calificados", "nombre": "Deportistas Calificados", "match": "Deportistas"},
    {"id": "personas_con_discapacidad", "nombre": "Personas con Discapacidad", "match": "Discapacidad"},
    {"id": "egresados_institutos", "nombre": "Egresados de Institutos", "match": "Institutos"},
    {"id": "mayores_30", "nombre": "Mayores de 30 años", "match": "Mayores"},
    {"id": "primera_seleccion", "nombre": "Primera Selección", "match": "Primera Selección"},
    {"id": "oficiales_ffaa_ffpp", "nombre": "Oficiales FFAA/FFPP", "match": "Oficiales"},
    {"id": "suboficiales_ffaa_ffpp", "nombre": "Suboficiales FFAA/FFPP", "match": "Suboficiales"},
    {"id": "beca_oportunidad", "nombre": "Beca Oportunidad", "match": "Beca Oportunidad"},
]


def modalidad_by_id(mid: str) -> dict | None:
    return next((m for m in MODALIDADES if m["id"] == mid), None)
