from pathlib import Path

import pytest
import yaml

from radar.filtros import classificar_nivel, eh_area_dados, local_aceito, uf_de_texto, eh_brasil, modalidade_de_texto

CFG = yaml.safe_load((Path(__file__).resolve().parent.parent / "config.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("titulo, esperado", [
    ("Analista de Dados Júnior", True),
    ("Analista de BI", True),
    ("Engenheiro(a) de Dados", True),
    ("Data Analyst", True),
    ("Cientista de Dados", True),
    ("Analytics Engineer", True),
    ("Analista de Power BI", True),
    ("Auxiliar de Entrada de Dados", False),
    ("Técnico de Data Center", False),
    ("Analista de Proteção de Dados (LGPD)", False),
    ("Vendedor Externo", False),
    ("Analista Financeiro", False),
    ("Database Administrator", False),
])
def test_area(titulo, esperado):
    assert eh_area_dados(titulo, CFG) is esperado


@pytest.mark.parametrize("titulo, desc, tipo, esperado", [
    ("Analista de Dados Júnior", "", "", "junior"),
    ("Analista de Dados Jr", "", "", "junior"),
    ("Analista de Dados JR.", "", "", "junior"),
    ("Data Analyst I", "", "", "junior"),
    ("Analista de Dados I - Remoto", "", "", "junior"),
    ("Analista de Dados Jr/Pleno", "", "", "junior"),
    ("Estágio em Dados", "", "", "estagio"),
    ("Estagiário(a) de BI", "", "", "estagio"),
    ("Analista de Dados", "", "vacancy_type_internship", "estagio"),
    ("Trainee Analytics", "", "", "trainee"),
    ("Analista de Dados Sênior", "", "", None),
    ("Analista de Dados Sr", "", "", None),
    ("Analista de Dados Pleno", "", "", None),
    ("Analista de Dados PL", "", "", None),
    ("Analista de Dados II", "", "", None),
    ("Head de Dados", "", "", None),
    ("Data Engineering Manager", "", "", None),
    ("Especialista em BI", "", "", None),
    ("Desenvolvedor PL/SQL", "", "", "nao_informado"),
    ("Analista de BI", "", "", "nao_informado"),
    ("Analista de Dados", "Requisitos: 5 anos de experiência com SQL", "", None),
    ("Analista de Dados", "3+ years of experience", "", None),
    ("Analista de Dados", "mínimo de 4 anos com Python", "", None),
    ("Analista de Dados", "Desejável 1 ano de experiência", "", "junior"),
    ("Analista de Dados", "Vaga para início de carreira", "", "junior"),
    ("Analista de Dados", "Buscamos profissional pleno", "", None),
    ("Analista de Business Intelligence (B.I)", "", "", "nao_informado"),
])
def test_nivel(titulo, desc, tipo, esperado):
    nivel, _ = classificar_nivel(titulo, desc, tipo, CFG)
    assert nivel == esperado


def test_local():
    base = dict(CFG, estados=["SP"])
    assert local_aceito({"modalidade": "remoto", "uf": None, "brasil": True}, base)[0]
    assert local_aceito({"modalidade": "hibrido", "uf": "SP", "brasil": True}, base)[0]
    assert not local_aceito({"modalidade": "presencial", "uf": "RJ", "brasil": True}, base)[0]
    assert not local_aceito({"modalidade": "remoto", "uf": None, "brasil": False}, CFG)[0]
    assert local_aceito({"modalidade": "remoto", "uf": None, "brasil": False},
                        dict(CFG, aceitar_remoto_exterior=True))[0]
    assert not local_aceito({"modalidade": "presencial", "uf": "SP", "brasil": True},
                            dict(CFG, modalidades=["remoto"]))[0]


def test_textos_de_local():
    assert uf_de_texto("São Paulo, Brazil") == "SP"
    assert uf_de_texto("Campinas, SP") == "SP"
    assert uf_de_texto("Remote") is None
    assert eh_brasil("Remote - Brazil") and eh_brasil("Curitiba") and not eh_brasil("Mexico City")
    assert modalidade_de_texto("Remote - LATAM") == "remoto"
    assert modalidade_de_texto("São Paulo (Hybrid)") == "hibrido"
