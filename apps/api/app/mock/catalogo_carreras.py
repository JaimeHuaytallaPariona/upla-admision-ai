"""Catálogo oficial de carreras UPLA agrupadas por canal."""

CARRERAS_BY_CANAL = {
    "I": [
        "Administración y Sistemas",
        "Contabilidad y Finanzas",
        "Administración y Negocios Internacionales",
        "Turismo, Hotelería y Gastronomía",
    ],
    "II": [
        "Ingeniería de Sistemas y Computación",
        "Ingeniería Civil",
        "Ingeniería Ambiental",
        "Ingeniería Industrial",
        "Arquitectura",
    ],
    "III": [
        "Enfermería",
        "Farmacia y Bioquímica",
        "Obstetricia",
        "Tecnología Médica",
        "Nutrición Humana",
        "Psicología",
    ],
    "IV": [
        "Derecho",
        "Educación Inicial",
        "Educación Primaria",
        "Educación Secundaria",
        "Ciencias de la Comunicación",
        "Idiomas",
    ],
    "V": [
        "Medicina Humana",
        "Odontología",
    ],
}


def canal_de_carrera(carrera: str) -> str | None:
    for canal, carreras in CARRERAS_BY_CANAL.items():
        if carrera in carreras:
            return canal
    # Match insensible a mayúsculas
    cl = carrera.lower()
    for canal, carreras in CARRERAS_BY_CANAL.items():
        for c in carreras:
            if c.lower() == cl:
                return canal
    return None


def todas_las_carreras() -> list[str]:
    return [c for carreras in CARRERAS_BY_CANAL.values() for c in carreras]
