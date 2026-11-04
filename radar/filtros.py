"""Regras que decidem se uma vaga é de dados, qual o nível e se o local serve."""
from __future__ import annotations

import html
import re
import unicodedata

UFS = {
    "AC": "acre", "AL": "alagoas", "AP": "amapa", "AM": "amazonas", "BA": "bahia",
    "CE": "ceara", "DF": "distrito federal", "ES": "espirito santo", "GO": "goias",
    "MA": "maranhao", "MT": "mato grosso", "MS": "mato grosso do sul", "MG": "minas gerais",
    "PA": "para", "PB": "paraiba", "PR": "parana", "PE": "pernambuco", "PI": "piaui",
    "RJ": "rio de janeiro", "RN": "rio grande do norte", "RS": "rio grande do sul",
    "RO": "rondonia", "RR": "roraima", "SC": "santa catarina", "SP": "sao paulo",
    "SE": "sergipe", "TO": "tocantins",
}
NOME_PARA_UF = {v: k for k, v in UFS.items()}

CIDADES_BR = [
    "sao paulo", "rio de janeiro", "belo horizonte", "curitiba", "porto alegre",
    "florianopolis", "recife", "salvador", "fortaleza", "brasilia", "campinas",
    "goiania", "manaus", "belem", "vitoria", "joinville", "blumenau", "sao jose dos campos",
    "ribeirao preto", "uberlandia", "barueri", "osasco", "santos", "londrina", "maringa",
]


def norm(s: str | None) -> str:
    """minúsculas, sem acentos, espaços simples."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def limpar_html(s: str | None) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"[ \t\xa0]+", " ", re.sub(r"\n\s*\n+", "\n", s)).strip()


def _tem(texto_norm: str, termos: list[str]) -> str | None:
    """Devolve o primeiro termo encontrado como palavra inteira."""
    for t in termos:
        tn = norm(t)
        if tn and re.search(r"(?<![\w/])" + re.escape(tn) + r"(?![\w/])", texto_norm):
            return t
    return None


# --------------------------------------------------------------------- área
def eh_area_dados(titulo: str, cfg: dict) -> bool:
    t = norm(titulo)
    if _tem(t, cfg.get("excluir_area", [])):
        return False
    return _tem(t, cfg.get("palavras_area", [])) is not None


# --------------------------------------------------------------------- nível
RE_ESTAGIO = re.compile(r"\b(estagio|estagiari[oa]s?|intern|internship)\b")
RE_TRAINEE = re.compile(r"\b(trainee|aprendiz|jovem aprendiz|programa de formacao)\b")
RE_JUNIOR = re.compile(
    r"\b(junior|jr|entry[ -]level|nivel (1|i)|graduate|recem[ -]formad[oa])\b"
    r"|(?<![\w/.])i(?=\s*(?:$|[-–|(,]))"   # "Analista de Dados I" (I romano no fim)
)
RE_ANOS = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:a\s*\d{1,2}\s*)?(?:anos?|years?)\s*(?:\+\s*)?"
    r"(?:de\s+|of\s+)?(?:experiencia|experience|atuacao|vivencia)"
)
RE_ANOS_MIN = re.compile(r"(?:minimo|pelo menos|at least|no minimo)\s+(?:de\s+)?(\d{1,2})\s*(?:anos?|years?)")
RE_DESC_SENIOR = re.compile(
    r"\b(nivel|perfil|vaga|profissional|posicao|atuacao|cargo)\s+(?:de\s+)?(senior|pleno|especialista)\b"
)
RE_DESC_JUNIOR = re.compile(r"\b(junior|jr|inicio de carreira|primeiro emprego|entry[ -]level)\b")


def _limpar_titulo(t: str) -> str:
    # "PL/SQL" não é "pleno"; "Power BI" etc. já passam.
    return re.sub(r"\bpl\s*/\s*sql\b", "plsql", t)


def anos_pedidos(descricao_norm: str) -> int | None:
    achados = [int(m) for m in RE_ANOS.findall(descricao_norm)]
    achados += [int(m) for m in RE_ANOS_MIN.findall(descricao_norm)]
    achados = [a for a in achados if 0 < a < 30]
    return min(achados) if achados else None


def classificar_nivel(titulo: str, descricao: str = "", tipo: str = "",
                      cfg: dict | None = None) -> tuple[str | None, str]:
    """Retorna (nivel, motivo). nivel None = descartar.

    nivel ∈ {"estagio", "trainee", "junior", "nao_informado"}
    """
    cfg = cfg or {}
    t = _limpar_titulo(norm(titulo))
    d = norm(descricao)
    tipo = (tipo or "").lower()
    max_anos = int(cfg.get("max_anos_experiencia", 3))

    if RE_ESTAGIO.search(t) or "internship" in tipo:
        return "estagio", "título/contrato de estágio"
    if RE_TRAINEE.search(t) or "trainee" in tipo or "apprentice" in tipo:
        return "trainee", "título/contrato de trainee ou aprendiz"
    if RE_JUNIOR.search(t):
        return "junior", "título diz júnior"

    acima = _tem(t, cfg.get("excluir_senioridade", []))
    if acima:
        return None, f'título indica nível acima ("{acima}")'

    anos = anos_pedidos(d)
    if anos is not None and anos >= max_anos:
        return None, f"descrição pede {anos}+ anos de experiência"
    m = RE_DESC_SENIOR.search(d)
    if m:
        return None, f'descrição indica nível {m.group(2)}'
    if RE_DESC_JUNIOR.search(d):
        return "junior", "descrição menciona júnior/início de carreira"
    if anos is not None:
        return "junior", f"pede só {anos} ano(s) de experiência"
    return "nao_informado", "sem nível no título nem sinais de sênior/pleno"


# --------------------------------------------------------------------- local
def modalidade_de_texto(texto: str) -> str:
    t = norm(texto)
    if re.search(r"\b(hibrid[oa]|hybrid)\b", t):
        return "hibrido"
    if re.search(r"\b(remot[oa]|remote|home ?office|anywhere|teletrabalho)\b", t):
        return "remoto"
    return "presencial"


def uf_de_texto(texto: str) -> str | None:
    t = norm(texto)
    for nome, uf in sorted(NOME_PARA_UF.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(nome) + r"\b", t):
            return uf
    m = re.search(r"(?:^|[\s,\-/(])([a-z]{2})(?:$|[\s,\-/)])", t)
    if m and m.group(1).upper() in UFS:
        return m.group(1).upper()
    return None


def eh_brasil(texto: str) -> bool:
    t = norm(texto)
    if re.search(r"\b(brasil|brazil|latam|latin america|america latina|south america)\b", t):
        return True
    return any(re.search(r"\b" + c + r"\b", t) for c in CIDADES_BR)


def local_aceito(vaga: dict, cfg: dict) -> tuple[bool, str]:
    mod = vaga.get("modalidade", "presencial")
    if mod not in cfg.get("modalidades", ["remoto", "hibrido", "presencial"]):
        return False, f"modalidade {mod} fora da lista"
    if not vaga.get("brasil", True):
        if mod == "remoto" and cfg.get("aceitar_remoto_exterior", False):
            return True, "remoto exterior aceito"
        return False, "fora do Brasil"
    estados = [e.upper() for e in cfg.get("estados", []) or []]
    if mod != "remoto" and estados and vaga.get("uf") not in estados:
        return False, f"estado {vaga.get('uf') or '?'} fora da lista"
    return True, "ok"


def empresa_bloqueada(empresa: str, cfg: dict) -> bool:
    e = norm(empresa)
    return any(norm(b) and norm(b) in e for b in cfg.get("empresas_bloqueadas", []) or [])
