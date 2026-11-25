"""Datos ficticios de postulantes y resultados para la demo."""
import hashlib

# Base de postulantes ficticios indexados por DNI
POSTULANTES_DEMO = {
    "71234567": {
        "codigo": "UPLA-2026-A4F2E1",
        "nombres": "María Alejandra",
        "apellidos": "Quispe Yauri",
        "carrera": "Enfermería",
        "canal": "III",
        "estado": "ingreso",
        "puntaje": 78.5,
        "puesto": 12,
        "fecha_resultados": "9 de marzo de 2027",
    },
    "72345678": {
        "codigo": "UPLA-2026-B7C3D9",
        "nombres": "Carlos Daniel",
        "apellidos": "Huamán Aliaga",
        "carrera": "Medicina Humana",
        "canal": "V",
        "estado": "no_ingreso",
        "puntaje": 62.0,
        "puesto": 145,
        "fecha_resultados": "9 de marzo de 2027",
    },
    "73456789": {
        "codigo": "UPLA-2026-C9E4F2",
        "nombres": "Rosa Milagros",
        "apellidos": "Chávez Poma",
        "carrera": "Ingeniería de Sistemas y Computación",
        "canal": "II",
        "estado": "ingreso",
        "puntaje": 85.2,
        "puesto": 3,
        "fecha_resultados": "9 de marzo de 2027",
    },
    "74567890": {
        "codigo": "UPLA-2026-D1A8B6",
        "nombres": "Javier Antonio",
        "apellidos": "Rojas Mendoza",
        "carrera": "Derecho",
        "canal": "IV",
        "estado": "en_proceso",
        "puntaje": None,
        "puesto": None,
        "fecha_resultados": "9 de marzo de 2027",
    },
    "75678901": {
        "codigo": "UPLA-2026-E5F2A3",
        "nombres": "Luz Angélica",
        "apellidos": "Pariona Castro",
        "carrera": "Psicología",
        "canal": "III",
        "estado": "en_proceso",
        "puntaje": None,
        "puesto": None,
        "fecha_resultados": "9 de marzo de 2027",
    },
}


def consultar_resultado(dni: str) -> dict | None:
    """Retorna el resultado para un DNI. Para la demo, cualquier DNI válido retorna un resultado determinístico."""
    if dni in POSTULANTES_DEMO:
        return POSTULANTES_DEMO[dni]
    # Para DNIs no cargados, generamos un resultado determinístico por hash para que la demo sea reproducible.
    h = int(hashlib.md5(dni.encode()).hexdigest(), 16)
    if h % 10 < 1:  # 10% en_proceso
        estado = "en_proceso"
        puntaje = None
    elif h % 10 < 6:  # 50% ingreso
        estado = "ingreso"
        puntaje = round(70 + (h % 200) / 10, 1)
    else:
        estado = "no_ingreso"
        puntaje = round(40 + (h % 250) / 10, 1)

    return {
        "codigo": f"UPLA-2026-{hex(h)[2:8].upper()}",
        "nombres": "Postulante",
        "apellidos": "Demo",
        "carrera": "Ingeniería de Sistemas y Computación",
        "canal": "II",
        "estado": estado,
        "puntaje": puntaje,
        "puesto": (h % 500) + 1 if puntaje else None,
        "fecha_resultados": "9 de marzo de 2027",
    }
