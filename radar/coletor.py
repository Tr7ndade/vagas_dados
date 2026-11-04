"""Roda a coleta: busca nas fontes, filtra, junta com o histórico e grava o painel.

Uso:  python -m radar            (coleta de verdade)
      python -m radar --demo     (gera o painel com vagas de exemplo, sem internet)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from .filtros import classificar_nivel, eh_area_dados, empresa_bloqueada, local_aceito
from .fontes import FONTES, FonteQuebrada

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
log = logging.getLogger("radar")


def carregar_config(caminho: Path = RAIZ / "config.yaml") -> dict:
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def filtrar(vagas: list[dict], cfg: dict, hoje: date) -> tuple[list[dict], dict]:
    niveis = set(cfg.get("niveis", ["junior", "trainee", "nao_informado"]))
    corte = (hoje - timedelta(days=int(cfg.get("janela_dias", 14)))).isoformat()
    motivos: dict[str, int] = {}
    aceitas = []

    def descarta(m):
        motivos[m] = motivos.get(m, 0) + 1

    for v in vagas:
        if not eh_area_dados(v["titulo"], cfg):
            descarta("não é de dados"); continue
        if v.get("publicada_em") and v["publicada_em"] < corte:
            descarta("antiga"); continue
        if empresa_bloqueada(v["empresa"], cfg):
            descarta("empresa bloqueada"); continue
        nivel, motivo = classificar_nivel(v["titulo"], v.get("descricao", ""), v.get("tipo_bruto", ""), cfg)
        if nivel is None:
            descarta("nível acima de júnior"); continue
        if nivel not in niveis:
            descarta(f"nível {nivel} desativado"); continue
        ok, mot_local = local_aceito(v, cfg)
        if not ok:
            descarta("local/modalidade"); continue
        v = {k: val for k, val in v.items() if k != "tipo_bruto"}
        v["nivel"], v["motivo_nivel"] = nivel, motivo
        aceitas.append(v)
    return aceitas, motivos


def mesclar(historico: list[dict], novas: list[dict], agora: str, manter_dias: int,
            fontes_ok: set[str]) -> tuple[list[dict], list[dict]]:
    por_id = {v["id"]: v for v in historico}
    recem = []
    for v in novas:
        antigo = por_id.get(v["id"])
        if antigo:
            v["primeira_vez"] = antigo.get("primeira_vez", agora)
        else:
            v["primeira_vez"] = agora
            recem.append(v)
        v["ultima_vez"] = agora
        v["ativa"] = True
        por_id[v["id"]] = v
    limite = (datetime.fromisoformat(agora) - timedelta(days=manter_dias)).isoformat()
    vistos = {v["id"] for v in novas}
    resultado = []
    for v in por_id.values():
        if v["id"] not in vistos:
            # só marca como encerrada se a fonte dela funcionou nesta rodada
            if v["fonte"].lower() in fontes_ok:
                v["ativa"] = False
            if v.get("ultima_vez", agora) < limite:
                continue
        resultado.append(v)
    resultado.sort(key=lambda v: (v.get("primeira_vez", ""), v.get("publicada_em") or ""), reverse=True)
    return resultado, recem


def gravar(vagas: list[dict], meta: dict, recem: list[dict]) -> None:
    DOCS.mkdir(exist_ok=True)
    pacote = {"meta": meta, "vagas": vagas}
    (DOCS / "vagas.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    # vagas.js permite abrir o painel direto do computador (sem servidor)
    (DOCS / "vagas.js").write_text("window.RADAR = " + json.dumps(pacote, ensure_ascii=False) + ";\n",
                                   encoding="utf-8")
    linhas = [f"# {len(recem)} vagas novas — {meta['atualizado_em'][:10]}", ""]
    for v in recem[:60]:
        linhas.append(f"- **{v['titulo']}** · {v['empresa']} · {v['local'] or v['modalidade']} "
                      f"· `{v['nivel']}` — [abrir]({v['link']})")
    if len(recem) > 60:
        linhas.append(f"\n…e mais {len(recem) - 60} no painel.")
    (RAIZ / "novas_hoje.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def rodar(cfg: dict, coletar=None, hoje: date | None = None) -> int:
    hoje = hoje or date.today()
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    coletar = coletar or FONTES
    brutas, relatorio, fontes_ok, quebradas = [], {}, set(), []

    for nome, fn in coletar.items():
        if not (cfg.get(nome) or {}).get("ativo", True):
            continue
        try:
            vagas, info = fn(cfg)
            brutas += vagas
            fontes_ok.add(nome)
            relatorio[nome] = {"ok": True, **info}
            log.info("%s: %d vagas brutas", nome, info.get("brutas", len(vagas)))
        except FonteQuebrada as e:
            quebradas.append(nome)
            relatorio[nome] = {"ok": False, "erro": str(e)}
            log.error("FONTE QUEBRADA %s: %s", nome, e)
        except Exception as e:  # noqa: BLE001
            quebradas.append(nome)
            relatorio[nome] = {"ok": False, "erro": repr(e)}
            log.exception("erro inesperado em %s", nome)

    aceitas, motivos = filtrar(brutas, cfg, hoje)
    caminho = DOCS / "vagas.json"
    historico = json.loads(caminho.read_text(encoding="utf-8"))["vagas"] if caminho.exists() else []
    if historico and historico[0].get("demo"):
        historico = []  # descarta dados de exemplo na primeira coleta real
    todas, recem = mesclar(historico, aceitas, agora, int(cfg.get("manter_dias", 30)), fontes_ok)

    meta = {"atualizado_em": agora, "fontes": relatorio, "brutas": len(brutas),
            "aceitas_hoje": len(aceitas), "novas_hoje": len(recem), "descartes": motivos}
    gravar(todas, meta, recem)
    log.info("brutas=%d aceitas=%d novas=%d total no painel=%d", len(brutas), len(aceitas), len(recem), len(todas))
    if quebradas:
        log.error("Fontes com problema: %s — veja o README, seção 'Quando algo quebra'", ", ".join(quebradas))
        return 1
    return 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="gera painel com vagas de exemplo")
    args = ap.parse_args()
    cfg = carregar_config()
    if args.demo:
        from .demo import FONTES_DEMO
        code = rodar(cfg, FONTES_DEMO)
        p = DOCS / "vagas.json"
        pacote = json.loads(p.read_text(encoding="utf-8"))
        for v in pacote["vagas"]:
            v["demo"] = True
        pacote["meta"]["demo"] = True
        gravar(pacote["vagas"], pacote["meta"], [])
        sys.exit(code)
    sys.exit(rodar(cfg))
