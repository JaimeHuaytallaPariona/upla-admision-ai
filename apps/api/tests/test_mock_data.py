"""Tests de los catálogos mock."""
from app.mock.catalogo_carreras import CARRERAS_BY_CANAL, canal_de_carrera, todas_las_carreras
from app.mock.catalogo_modalidades import MODALIDADES
from app.mock.resultados import consultar_resultado


def test_todos_los_canales_existen():
    assert set(CARRERAS_BY_CANAL.keys()) == {"I", "II", "III", "IV", "V"}


def test_total_carreras():
    assert len(todas_las_carreras()) == 23  # cuenta esperada


def test_canal_de_carrera():
    assert canal_de_carrera("Medicina Humana") == "V"
    assert canal_de_carrera("Derecho") == "IV"
    assert canal_de_carrera("Enfermería") == "III"
    assert canal_de_carrera("Ingeniería de Sistemas y Computación") == "II"
    assert canal_de_carrera("Carrera Inexistente") is None


def test_13_modalidades():
    assert len(MODALIDADES) == 13


def test_resultado_dni_conocido():
    r = consultar_resultado("71234567")
    assert r is not None
    assert r["estado"] == "ingreso"
    assert r["carrera"] == "Enfermería"


def test_resultado_dni_desconocido_es_determinista():
    r1 = consultar_resultado("99999999")
    r2 = consultar_resultado("99999999")
    assert r1 == r2
