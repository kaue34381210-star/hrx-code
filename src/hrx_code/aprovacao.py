"""Classificação heurística de risco para comandos."""
import os
import re
import shlex

# Padrões perigosos são avaliados antes destas listas.
SEGUROS = {
    "ls", "dir", "pwd", "cat", "type", "head", "tail", "echo", "printf",
    "whoami", "hostname", "date", "uptime", "cal", "df", "du", "free",
    "ps", "top", "htop", "env", "printenv", "set", "which", "where",
    "whereis", "id", "groups", "uname", "arch", "wc", "nl", "sort", "uniq",
    "cut", "column", "tr", "grep", "egrep", "fgrep", "rg", "file", "stat",
    "tree", "basename", "dirname", "realpath", "readlink", "history",
    "man", "help", "clear", "cd", "test", "true", "false",
    "find", "locate", "less", "more", "diff", "comm", "cmp", "pgrep",
    "md5sum", "sha1sum", "sha256sum", "sha512sum", "b2sum", "cksum",
    "lsblk", "lscpu", "lsusb", "lspci", "lsof", "ss", "netstat",
    "ping", "ping6", "dig", "nslookup", "host", "jobs", "alias",
    "command", "apropos", "getent", "hexdump", "xxd", "strings",
}

LEITURA_POR_SUB = {
    "pip": {"list", "show", "freeze", "search", "index", "check", "--version", "-v"},
    "pip3": {"list", "show", "freeze", "search", "index", "check", "--version", "-v"},
    "npm": {"ls", "list", "view", "outdated", "audit", "root", "config", "help", "--version", "-v"},
    "pnpm": {"ls", "list", "outdated", "why", "--version"},
    "yarn": {"list", "why", "info", "--version"},
    "docker": {"ps", "images", "image", "logs", "inspect", "version", "info",
               "stats", "top", "port", "history", "diff", "search"},
    "podman": {"ps", "images", "image", "logs", "inspect", "version", "info", "stats", "top"},
    "kubectl": {"get", "describe", "logs", "version", "top", "explain",
                "api-resources", "config", "cluster-info"},
    "systemctl": {"status", "list-units", "list-unit-files", "is-active",
                  "is-enabled", "is-failed", "show", "cat", "get-default"},
    "service": {"status"},
    "cargo": {"--version", "tree", "search"},
    "go": {"version", "env", "list", "doc"},
    "apt": {"list", "show", "search", "policy", "--version"},
    "apt-get": {"--version"},
    "dnf": {"list", "info", "search", "repolist"},
    "yum": {"list", "info", "search"},
    "brew": {"list", "info", "search", "outdated", "--version"},
}

VERMELHO = [
    (re.compile(r"(^|\s):\s*\(\s*\)\s*\{"), "fork bomb"),
    (re.compile(r"\brm\b"), "remove arquivos/diretórios"),
    (re.compile(r"\brmdir\b"), "remove diretórios"),
    (re.compile(r"\bunlink\b"), "remove arquivo"),
    (re.compile(r"\bshred\b"), "apaga de forma irrecuperável"),
    (re.compile(r"\bdd\b"), "escrita bruta em disco"),
    (re.compile(r"\bmkfs\b|\bfdisk\b|\bparted\b|\bwipefs\b"), "mexe no particionamento do disco"),
    (re.compile(r"\b(shutdown|reboot|halt|poweroff|init)\b"), "desliga/reinicia a máquina"),
    (re.compile(r"\bsudo\b|\bsu\b|\bdoas\b"), "eleva privilégios"),
    (re.compile(r"\b(chmod|chown|chgrp)\b.*(-\w*[Rr]|--recursive)"), "muda permissões recursivamente"),
    (re.compile(r"\bgit\b.+push.+(-f\b|--force)"), "git push forçado (reescreve histórico remoto)"),
    (re.compile(r"\bgit\b.+(reset\s+--hard|clean\s+-\w*f)"), "descarta alterações locais do git"),
    (re.compile(r"\b(curl|wget)\b.+\|\s*(sudo\s+)?(sh|bash|zsh|python\d?)"), "baixa e executa script da internet"),
    (re.compile(r"\b(kill|killall|pkill)\b"), "encerra processos"),
    (re.compile(r"\btruncate\b"), "trunca arquivos"),
    (re.compile(r"-delete\b|-exec\b|-execdir\b"), "find executando/apagando arquivos"),
    (re.compile(r">\s*/(etc|bin|sbin|usr|var|boot|dev|lib|sys|proc)\b"), "sobrescreve arquivo de sistema"),
    (re.compile(r"\bmv\b.+\s/(etc|bin|sbin|usr|var|boot|lib)\b"), "move para diretório de sistema"),
    (re.compile(r"\b(iptables|nft|ufw)\b"), "altera regras de firewall"),
    (re.compile(r"\bcrontab\b\s+-r"), "apaga todas as tarefas agendadas"),
    (re.compile(r"\b(del|erase)\b"), "remove arquivos no Windows"),
    (re.compile(r"\b(rd|remove-item)\b.+(-r\b|-recurse\b|/s\b)"), "remove diretórios recursivamente"),
    (re.compile(r"\b(format|diskpart)\b"), "mexe no disco no Windows"),
    (re.compile(r"\b(stop-computer|restart-computer)\b"), "desliga/reinicia a máquina"),
]

AMARELO = [
    (re.compile(r"\bsed\b.+-\w*i"), "sed editando arquivo no lugar"),
    (re.compile(r">>?"), "redireciona/sobrescreve saída em arquivo"),
    (re.compile(r"\b(pip\d?|pipx|npm|pnpm|yarn|apt|apt-get|dnf|yum|pacman|brew|cargo|go)\b\s+(install|add|remove|uninstall|update|upgrade|i\b)"), "instala/remove pacotes"),
    (re.compile(r"\bgit\b\s+(add|commit|checkout|switch|merge|rebase|stash|tag|restore|mv|rm|pull|push|apply|cherry-pick|revert)\b"), "altera o repositório git"),
    (re.compile(r"\b(systemctl|service)\b\s+(start|stop|restart|reload|enable|disable)"), "controla serviços do sistema"),
    (re.compile(r"\bdocker\b\s+(run|rm|rmi|stop|kill|build|compose|exec|prune)"), "opera containers Docker"),
]

MUTANTES = {
    "mkdir", "touch", "cp", "mv", "ln", "tee", "install", "make", "cmake",
    "tar", "zip", "unzip", "gzip", "gunzip", "git", "apt", "apt-get", "dnf",
    "yum", "pacman", "brew", "pip", "pip3", "pipx", "npm", "pnpm", "yarn",
    "cargo", "go", "docker", "podman", "kubectl", "systemctl", "service",
    "python", "python3", "node", "bash", "sh", "zsh", "perl", "ruby", "sed",
    "awk", "nmap", "curl", "wget", "ssh", "scp", "rsync", "powershell",
    "pwsh", "cmd", "dash", "ksh", "fish", "php", "deno", "bun",
}

# Flags que permitem a um git de leitura escrever arquivos ou executar código.
GIT_FLAGS_SENSIVEIS = re.compile(
    r"(^|\s)(-c\b|-C\b|--exec-path|--output\b|-O\b|--open-files-in-pager"
    r"|--ext-diff|--upload-pack|--receive-pack|--exec\b|--pager\b)")

NIVEIS = ("verde", "amarelo", "vermelho")

_SEPARADORES = {";", "&&", "||", "|", "&", "(", ")"}
_WRAPPERS = {"command", "env", "nohup"}
_ATRIBUICAO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_PYTHON = re.compile(r"^python(?:\d+(?:\.\d+)*)?$")
_INLINE = {
    "bash": {"-c", "--command"},
    "dash": {"-c"},
    "sh": {"-c"},
    "zsh": {"-c"},
    "ksh": {"-c"},
    "fish": {"-c", "--command"},
    "node": {"-e", "--eval"},
    "deno": {"eval"},
    "bun": {"-e", "--eval"},
    "perl": {"-e"},
    "ruby": {"-e"},
    "php": {"-r"},
    "powershell": {"-c", "-command", "-enc", "-encodedcommand"},
    "pwsh": {"-c", "-command", "-enc", "-encodedcommand"},
    "cmd": {"/c", "/k"},
}


def _tokenizar(comando: str) -> list:
    lexer = shlex.shlex(comando, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _segmentos(tokens: list) -> list:
    segmentos, atual = [], []
    for token in tokens:
        if token in _SEPARADORES:
            if atual:
                segmentos.append(atual)
                atual = []
        else:
            atual.append(token)
    if atual:
        segmentos.append(atual)
    return segmentos


def _comando_do_segmento(tokens: list) -> tuple:
    """Retorna executável e argumentos, atravessando wrappers simples."""
    for indice, token in enumerate(tokens):
        if _ATRIBUICAO.match(token) or token.startswith((">", "<")):
            continue
        exe = os.path.basename(token).lower()
        if exe in _WRAPPERS:
            continue
        if token.startswith("-"):
            continue
        return token, [t.lower() for t in tokens[indice + 1:]]
    return "", []


def _risco_estrutural(tokens: list) -> tuple:
    comandos = []
    for segmento in _segmentos(tokens):
        bruto, args = _comando_do_segmento(segmento)
        if not bruto:
            continue
        if "$" in bruto or "`" in bruto:
            return "vermelho", "executável definido dinamicamente"
        exe = os.path.basename(bruto).lower()
        comandos.append(exe)
        flags = set(args)
        if _PYTHON.match(exe) and "-c" in flags:
            return "vermelho", "executa código Python inline"
        if exe in _INLINE and flags.intersection(_INLINE[exe]):
            return "vermelho", f"executa código inline via {exe}"
        if exe in {"eval", "source", "."}:
            return "vermelho", "executa conteúdo dinâmico no shell"
    return "", comandos


def classificar(comando: str, seguros_extra=()) -> tuple:
    """Devolve (nivel, motivo). nivel ∈ {'verde','amarelo','vermelho'}."""
    c = comando.strip()
    if not c:
        return ("vermelho", "comando vazio")

    try:
        tokens = _tokenizar(c)
    except ValueError:
        return ("vermelho", "sintaxe shell inválida")

    estrutural, detalhe = _risco_estrutural(tokens)
    if estrutural:
        return estrutural, detalhe

    normalizado = " ".join(tokens).lower()
    candidatos = (c.lower(), normalizado)

    for rx, motivo in VERMELHO:
        if any(rx.search(valor) for valor in candidatos):
            return ("vermelho", motivo)

    for rx, motivo in AMARELO:
        if any(rx.search(valor) for valor in candidatos):
            return ("amarelo", motivo)

    comandos = detalhe
    exe = comandos[0] if comandos else ""
    seguros = SEGUROS | set(seguros_extra)

    for encadeado in comandos[1:]:
        if encadeado not in seguros:
            return ("amarelo", f"encadeia comando não seguro ({encadeado})")

    if exe == "git":
        if GIT_FLAGS_SENSIVEIS.search(normalizado):
            return ("amarelo", "git com flag sensível")
        sub = (tokens[1].lower() if len(tokens) > 1 else "")
        if sub in {"status", "diff", "log", "show", "branch", "remote",
                   "fetch", "rev-parse", "describe", "blame", "ls-files",
                   "shortlog", "reflog", "config", "tag", "cat-file", ""}:
            return ("verde", f"git {sub} (leitura)".strip())
        return ("amarelo", "altera o repositório git")

    if exe in LEITURA_POR_SUB:
        sub = tokens[1].lower() if len(tokens) > 1 else ""
        if sub in LEITURA_POR_SUB[exe]:
            return ("verde", f"{exe} {sub} (leitura)")

    if exe in seguros:
        return ("verde", "somente leitura")

    if exe in MUTANTES:
        return ("amarelo", "modifica o sistema")

    return ("amarelo", f"comando não classificado ({exe})")
