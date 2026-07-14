"""Motor Gemini com pool de chaves e failover automático.

Ideia central: várias chaves grátis. Quando uma estoura o limite (HTTP 429
RESOURCE_EXHAUSTED), ela entra em "castigo" (cooldown) pelo tempo que o
próprio Gemini informa, e o agente já usa a próxima chave. Assim uma cobre a
outra sem intervenção.
"""
import os
import sys
import time

import requests

import config

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


# ---------------------------------------------------------------------------
# Carregamento de chaves (arquivo local ou variáveis de ambiente — nunca no código)
# ---------------------------------------------------------------------------
def carregar_chaves() -> list:
    chaves = []
    if os.path.exists(config.ARQ_CHAVES):
        with open(config.ARQ_CHAVES, "r", encoding="utf-8") as f:
            for linha in f:
                v = linha.strip()
                if v and not v.startswith("#"):
                    chaves.append(v)
    for var in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4"):
        v = os.environ.get(var)
        if v and v not in chaves:
            chaves.append(v)
    return chaves


# ---------------------------------------------------------------------------
# Pool com cooldown por chave
# ---------------------------------------------------------------------------
class PoolChaves:
    def __init__(self, chaves: list):
        if not chaves:
            raise RuntimeError("Nenhuma chave carregada.")
        self.chaves = chaves
        self.i = 0
        self.cooldown = [0.0] * len(chaves)   # timestamp até quando cada chave está de castigo

    @property
    def n(self) -> int:
        return len(self.chaves)

    def proxima_disponivel(self):
        """Retorna (indice, chave) da próxima chave livre; se todas em cooldown,
        devolve a que libera primeiro."""
        agora = time.time()
        for _ in range(self.n):
            if self.cooldown[self.i] <= agora:
                return self.i, self.chaves[self.i]
            self.i = (self.i + 1) % self.n
        i = min(range(self.n), key=lambda k: self.cooldown[k])
        self.i = i
        return i, self.chaves[i]

    def penalizar(self, idx: int, segundos: float) -> None:
        self.cooldown[idx] = time.time() + segundos
        self.i = (idx + 1) % self.n   # já aponta pra próxima

    def status(self) -> list:
        agora = time.time()
        return [max(0, int(self.cooldown[k] - agora)) for k in range(self.n)]


# ---------------------------------------------------------------------------
# Conversão de mensagens (formato interno -> formato Gemini)
# ---------------------------------------------------------------------------
def _para_gemini(mensagens: list) -> dict:
    system = None
    contents = []
    for m in mensagens:
        if m["role"] == "system":
            system = m["content"]
            continue
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    body = {"contents": contents,
            "generationConfig": {"temperature": config.TEMPERATURA}}
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}
    return body


def _retry_after(resp) -> float:
    """Extrai o tempo de espera sugerido pelo Gemini no erro 429."""
    try:
        for d in resp.json().get("error", {}).get("details", []):
            if str(d.get("@type", "")).endswith("RetryInfo"):
                s = str(d.get("retryDelay", ""))
                if s.endswith("s"):
                    return float(s[:-1] or 0) or 30.0
    except Exception:  # noqa: BLE001
        pass
    return 45.0


def _extrair_texto(data: dict) -> str:
    cands = data.get("candidates", [])
    if not cands:
        fb = data.get("promptFeedback", {})
        return f"[sem resposta — bloqueado: {fb.get('blockReason', 'desconhecido')}]"
    parts = cands[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


# ---------------------------------------------------------------------------
# Chamada com failover
# ---------------------------------------------------------------------------
def chamar(pool: PoolChaves, mensagens: list, on_rotacao=None):
    """Chama o Gemini rotacionando chaves em caso de limite. Retorna (texto, idx_chave)."""
    body = _para_gemini(mensagens)
    url = URL.format(modelo=config.MODELO)
    ultimo_erro = None

    for _ in range(pool.n + 1):
        idx, chave = pool.proxima_disponivel()
        try:
            r = requests.post(url, params={"key": chave}, json=body, timeout=config.TIMEOUT)
        except requests.RequestException as e:
            ultimo_erro = f"rede: {e}"
            continue

        if r.status_code == 200:
            return _extrair_texto(r.json()), idx

        if r.status_code == 429:                      # limite estourado -> troca de chave
            espera = _retry_after(r)
            pool.penalizar(idx, espera)
            if on_rotacao:
                on_rotacao(idx, espera)
            ultimo_erro = f"429 (limite) na chave #{idx + 1}"
            continue

        if r.status_code in (500, 502, 503):          # servidor ocupado -> tenta outra rapidinho
            pool.penalizar(idx, 15)
            ultimo_erro = f"{r.status_code} (servidor) na chave #{idx + 1}"
            continue

        # 400/401/403/404: chave inválida ou modelo indisponível p/ ela -> castiga e tenta outra
        pool.penalizar(idx, 1800)
        ultimo_erro = f"{r.status_code} na chave #{idx + 1}: {r.text[:200]}"
        continue

    raise RuntimeError(f"Todas as chaves falharam. Último erro: {ultimo_erro}")
