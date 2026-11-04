"""Coleta de vagas nas fontes públicas. Cada função devolve (vagas, relatorio)."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import requests

from .filtros import eh_brasil, limpar_html, modalidade_de_texto, uf_de_texto, NOME_PARA_UF, norm

log = logging.getLogger("radar")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; radar-vagas-dados/1.0)", "Accept": "application/json"}
TIMEOUT = 40


class FonteQuebrada(Exception):
    """A fonte inteira falhou (ex.: endereço mudou). Gera alerta."""


def _get_json(url: str, params: dict | None = None, tentativas: int = 3):
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 404:
                raise FileNotFoundError(f"404 em {r.url}")
            r.raise_for_status()
            if "json" not in r.headers.get("Content-Type", ""):
                raise ValueError(f"resposta não-JSON de {r.url}")
            return r.json()
        except FileNotFoundError:
            raise
        except Exception as e:  # noqa: BLE001
            ultimo = e
            time.sleep(2 * (i + 1))
    raise ultimo  # type: ignore[misc]


def _vaga(**kw) -> dict:
    base = dict(id="", fonte="", titulo="", empresa="", local="", uf=None, brasil=True,
                modalidade="presencial", contrato="", publicada_em=None, link="", descricao="")
    base.update(kw)
    base["descricao"] = (base["descricao"] or "")[:5000]
    return base


# ------------------------------------------------------------------ Gupy
GUPY_URL = "https://portal.gupy.io/api/job-search/jobs"
GUPY_MOD = {"remote": "remoto", "hybrid": "hibrido", "on-site": "presencial", "onsite": "presencial"}
GUPY_CONTRATO = {
    "vacancy_type_effective": "CLT", "vacancy_legal_entity": "PJ", "vacancy_type_internship": "Estágio",
    "vacancy_type_trainee": "Trainee", "vacancy_type_apprentice": "Aprendiz",
    "vacancy_type_temporary": "Temporário", "vacancy_type_associate": "Associado",
    "vacancy_type_talent_pool": "Banco de talentos", "vacancy_type_lecturer": "Docente",
    "vacancy_type_freelancer": "Freelancer", "vacancy_type_autonomous": "Autônomo",
}


def gupy_para_vaga(j: dict) -> dict:
    cidade, estado = (j.get("city") or "").strip(), (j.get("state") or "").strip()
    mod = GUPY_MOD.get((j.get("workplaceType") or "").lower(), "presencial")
    if j.get("isRemoteWork"):
        mod = "remoto"
    tipo = j.get("type") or ""
    return _vaga(
        id=f"gupy:{j.get('id')}",
        fonte="Gupy",
        titulo=(j.get("name") or "").strip(),
        empresa=(j.get("careerPageName") or "Empresa confidencial").strip(),
        local=", ".join(p for p in (cidade, estado) if p) or ("Remoto" if mod == "remoto" else ""),
        uf=NOME_PARA_UF.get(norm(estado)) or uf_de_texto(estado),
        brasil=True,
        modalidade=mod,
        contrato=GUPY_CONTRATO.get(tipo, tipo.replace("vacancy_type_", "")),
        tipo_bruto=tipo,
        publicada_em=(j.get("publishedDate") or "")[:10] or None,
        link=(j.get("jobUrl") or j.get("url") or "").split("?")[0],
        descricao=limpar_html(j.get("description")),
    )


def coletar_gupy(cfg: dict) -> tuple[list[dict], dict]:
    c = cfg.get("gupy", {})
    brutas: dict[str, dict] = {}
    erros = 0
    chamadas = 0
    for termo in c.get("termos", []):
        for pagina in range(int(c.get("max_paginas_por_termo", 10))):
            chamadas += 1
            try:
                resp = _get_json(GUPY_URL, {"jobName": termo, "limit": 50, "offset": pagina * 50})
            except Exception as e:  # noqa: BLE001
                erros += 1
                log.warning("Gupy '%s' pág %d: %s", termo, pagina, e)
                break
            dados = resp.get("data", []) if isinstance(resp, dict) else []
            for j in dados:
                if j.get("id") is not None:
                    brutas[str(j["id"])] = j
            if len(dados) < 50:
                break
            time.sleep(0.7)
    if chamadas and erros == len(c.get("termos", [])):
        raise FonteQuebrada(
            "Todas as buscas na Gupy falharam. O endereço da API pode ter mudado "
            f"(atual: {GUPY_URL})."
        )
    vagas = [gupy_para_vaga(j) for j in brutas.values()]
    return vagas, {"brutas": len(brutas), "erros": erros}


# ------------------------------------------------------------------ Greenhouse
def greenhouse_para_vaga(j: dict, token: str, nome: str) -> dict:
    local = (j.get("location") or {}).get("name") or ""
    texto_local = local + " " + " ".join(o.get("name", "") for o in j.get("offices") or [])
    return _vaga(
        id=f"greenhouse:{token}:{j.get('id')}",
        fonte="Greenhouse",
        titulo=(j.get("title") or "").strip(),
        empresa=nome,
        local=local,
        uf=uf_de_texto(texto_local),
        brasil=eh_brasil(texto_local),
        modalidade=modalidade_de_texto(texto_local + " " + (j.get("title") or "")),
        publicada_em=(j.get("first_published") or j.get("updated_at") or "")[:10] or None,
        link=j.get("absolute_url") or "",
        descricao=limpar_html(j.get("content")),
    )


def coletar_greenhouse(cfg: dict) -> tuple[list[dict], dict]:
    empresas = (cfg.get("greenhouse") or {}).get("empresas") or {}
    vagas, falhas = [], []
    for token, nome in empresas.items():
        try:
            resp = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", {"content": "true"})
            vagas += [greenhouse_para_vaga(j, token, nome) for j in resp.get("jobs", [])]
        except Exception as e:  # noqa: BLE001
            falhas.append(f"{token}: {e}")
            log.warning("Greenhouse %s: %s", token, e)
        time.sleep(0.5)
    if empresas and len(falhas) == len(empresas):
        raise FonteQuebrada("Nenhuma empresa do Greenhouse respondeu. " + "; ".join(falhas[:3]))
    return vagas, {"brutas": len(vagas), "empresas_com_erro": falhas}


# ------------------------------------------------------------------ Lever
def lever_para_vaga(j: dict, slug: str, nome: str) -> dict:
    cat = j.get("categories") or {}
    locais = [cat.get("location") or ""] + list(cat.get("allLocations") or [])
    texto_local = " ".join(l for l in locais if l) + " " + (j.get("country") or "")
    wp = (j.get("workplaceType") or "").lower()
    mod = {"remote": "remoto", "hybrid": "hibrido", "onsite": "presencial", "on-site": "presencial"}.get(wp) \
        or modalidade_de_texto(texto_local)
    criado = j.get("createdAt")
    data = datetime.fromtimestamp(criado / 1000, tz=timezone.utc).date().isoformat() if criado else None
    return _vaga(
        id=f"lever:{slug}:{j.get('id')}",
        fonte="Lever",
        titulo=(j.get("text") or "").strip(),
        empresa=nome,
        local=cat.get("location") or "",
        uf=uf_de_texto(texto_local),
        brasil=eh_brasil(texto_local) or (j.get("country") or "").upper() == "BR",
        modalidade=mod,
        contrato=cat.get("commitment") or "",
        publicada_em=data,
        link=j.get("hostedUrl") or "",
        descricao=j.get("descriptionPlain") or limpar_html(j.get("description")),
    )


def coletar_lever(cfg: dict) -> tuple[list[dict], dict]:
    empresas = (cfg.get("lever") or {}).get("empresas") or {}
    vagas, falhas = [], []
    for slug, nome in empresas.items():
        resp = None
        for host in ("https://api.lever.co", "https://api.eu.lever.co"):
            try:
                resp = _get_json(f"{host}/v0/postings/{slug}", {"mode": "json"})
                break
            except FileNotFoundError:
                continue
            except Exception as e:  # noqa: BLE001
                falhas.append(f"{slug}: {e}")
                break
        if resp is None:
            if not any(f.startswith(slug + ":") for f in falhas):
                falhas.append(f"{slug}: não encontrado")
        else:
            vagas += [lever_para_vaga(j, slug, nome) for j in resp]
        time.sleep(1.0)  # o robots.txt do Lever pede 1s entre requisições
    if empresas and len(falhas) == len(empresas):
        raise FonteQuebrada("Nenhuma empresa do Lever respondeu. " + "; ".join(falhas[:3]))
    return vagas, {"brutas": len(vagas), "empresas_com_erro": falhas}


FONTES = {"gupy": coletar_gupy, "greenhouse": coletar_greenhouse, "lever": coletar_lever}
