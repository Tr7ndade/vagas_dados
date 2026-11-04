"""Vagas FICTÍCIAS no mesmo formato das APIs reais, para testar sem internet."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .fontes import greenhouse_para_vaga, gupy_para_vaga, lever_para_vaga


def _d(dias: int) -> str:
    return (date.today() - timedelta(days=dias)).isoformat() + "T12:00:00.000Z"


GUPY = [
    (1, "Analista de Dados Júnior", "Cooperativa Horizonte", "São Paulo", "São Paulo", "hybrid", "vacancy_type_effective", 0,
     "<p>Buscamos analista em início de carreira. SQL, Python e Power BI.</p>"),
    (2, "Analista de BI Jr", "Rede Farol Varejo", "Curitiba", "Paraná", "on-site", "vacancy_type_effective", 1,
     "<p>Construção de dashboards em Power BI.</p>"),
    (3, "Analista de Dados", "Grupo Ventura", "", "", "remote", "vacancy_type_effective", 2,
     "<p>Experiência com SQL e Excel avançado. Desejável 1 ano de experiência com análise.</p>"),
    (4, "Engenheiro(a) de Dados Sênior", "Banco Aurora", "São Paulo", "São Paulo", "remote", "vacancy_type_effective", 0,
     "<p>Spark, Airflow.</p>"),
    (5, "Analista de Dados Pleno", "Logística Rota Sul", "Porto Alegre", "Rio Grande do Sul", "hybrid", "vacancy_type_effective", 1, ""),
    (6, "Cientista de Dados", "Saúde Integra", "Belo Horizonte", "Minas Gerais", "hybrid", "vacancy_type_effective", 3,
     "<p>Requisitos: 5 anos de experiência com modelagem estatística.</p>"),
    (7, "Estágio em Dados e Analytics", "Energia Nova", "Rio de Janeiro", "Rio de Janeiro", "hybrid", "vacancy_type_internship", 0,
     "<p>Cursando Estatística, Engenharia ou correlatos.</p>"),
    (8, "Programa Trainee Data & Analytics 2027", "Indústria Atlas", "Campinas", "São Paulo", "on-site", "vacancy_type_trainee", 4, ""),
    (9, "Auxiliar de Entrada de Dados", "Escritório Central", "Recife", "Pernambuco", "on-site", "vacancy_type_effective", 0, ""),
    (10, "Desenvolvedor PL/SQL Júnior", "Sistemas Delta", "", "", "remote", "vacancy_legal_entity", 2, "<p>Oracle, PL/SQL.</p>"),
    (11, "Analista de Inteligência de Mercado", "Agro Campo Verde", "Goiânia", "Goiás", "on-site", "vacancy_type_effective", 5,
     "<p>Vaga para início de carreira em inteligência de mercado.</p>"),
    (12, "Data Analyst I", "Fintech Pix+", "", "", "remote", "vacancy_type_effective", 1, "<p>SQL, Looker.</p>"),
    (13, "Analista de Dados II", "Seguradora Prisma", "São Paulo", "São Paulo", "hybrid", "vacancy_type_effective", 1, ""),
    (14, "Vendedor Externo", "Loja Exemplo", "Salvador", "Bahia", "on-site", "vacancy_type_effective", 0, ""),
    (15, "Analista de Dados Jr - Marketing", "Editora Página", "Florianópolis", "Santa Catarina", "remote", "vacancy_type_effective", 6,
     "<p>GA4, BigQuery.</p>"),
    (16, "Analytics Engineer", "Startup Nimbus", "", "", "remote", "vacancy_type_effective", 2,
     "<p>Atuação com dbt. Perfil pleno para squad de dados.</p>"),
]


def _gupy(cfg):
    out = []
    for (i, nome, emp, cid, est, wp, tipo, dias, desc) in GUPY:
        out.append(gupy_para_vaga({
            "id": 900000 + i, "name": nome, "careerPageName": emp, "city": cid, "state": est,
            "workplaceType": wp, "type": tipo, "publishedDate": _d(dias), "description": desc,
            "jobUrl": f"https://exemplo.gupy.io/job/{900000 + i}",
        }))
    return out, {"brutas": len(out), "erros": 0}


def _greenhouse(cfg):
    jobs = [
        {"id": 1, "title": "Junior Data Analyst", "location": {"name": "São Paulo, Brazil"}, "first_published": _d(1),
         "absolute_url": "https://boards.greenhouse.io/exemplo/jobs/1", "content": "&lt;p&gt;SQL and Python.&lt;/p&gt;"},
        {"id": 2, "title": "Senior Data Engineer", "location": {"name": "Remote - Brazil"}, "first_published": _d(0),
         "absolute_url": "https://boards.greenhouse.io/exemplo/jobs/2", "content": ""},
        {"id": 3, "title": "Data Analyst", "location": {"name": "Remote - Brazil"}, "first_published": _d(2),
         "absolute_url": "https://boards.greenhouse.io/exemplo/jobs/3",
         "content": "&lt;p&gt;1+ years of experience with SQL.&lt;/p&gt;"},
        {"id": 4, "title": "Data Analyst Intern", "location": {"name": "Mexico City"}, "first_published": _d(1),
         "absolute_url": "https://boards.greenhouse.io/exemplo/jobs/4", "content": ""},
    ]
    out = [greenhouse_para_vaga(j, "exemplo", "Fintech Exemplo (Greenhouse)") for j in jobs]
    return out, {"brutas": len(out), "empresas_com_erro": []}


def _lever(cfg):
    ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    jobs = [
        {"id": "a1", "text": "Analista de Dados Júnior", "categories": {"location": "Campinas, SP", "commitment": "Full-time"},
         "workplaceType": "hybrid", "createdAt": ms - 86400000, "hostedUrl": "https://jobs.lever.co/exemplo/a1",
         "descriptionPlain": "Python, SQL e muita vontade de aprender.", "country": "BR"},
        {"id": "a2", "text": "Data Science Lead", "categories": {"location": "Remote"}, "workplaceType": "remote",
         "createdAt": ms, "hostedUrl": "https://jobs.lever.co/exemplo/a2", "descriptionPlain": "", "country": "BR"},
    ]
    out = [lever_para_vaga(j, "exemplo", "Consultoria Exemplo (Lever)") for j in jobs]
    return out, {"brutas": len(out), "empresas_com_erro": []}


FONTES_DEMO = {"gupy": _gupy, "greenhouse": _greenhouse, "lever": _lever}
