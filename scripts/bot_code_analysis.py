import argparse
import datetime
import json
import os
import platform
import subprocess  # nosec B404
import sys
import time
import urllib.request
from pathlib import Path


def _load_env() -> None:
    """Carrega o .env quando rodado fora do Django."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:  # não sobrescreve o Actions
                os.environ[key] = value


_load_env()


# ──────────────────────────────────────────────────────────────────────────────
#  TERMINAL
# ──────────────────────────────────────────────────────────────────────────────


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("GITHUB_ACTIONS"):
        return True
    stream = getattr(sys, "stdout", None)
    return bool(stream and hasattr(stream, "isatty") and stream.isatty())


def _supports_unicode() -> bool:
    try:
        encoding = (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "")
        return encoding in ("utf8", "utf16", "utf32")
    except Exception:
        return False


USE_COLOR = _supports_color()
USE_UNICODE = _supports_unicode()


class C:
    RESET = "\033[0m" if USE_COLOR else ""
    BOLD = "\033[1m" if USE_COLOR else ""
    DIM = "\033[2m" if USE_COLOR else ""
    RED = "\033[31m" if USE_COLOR else ""
    GREEN = "\033[32m" if USE_COLOR else ""
    YELLOW = "\033[33m" if USE_COLOR else ""
    BLUE = "\033[34m" if USE_COLOR else ""
    CYAN = "\033[36m" if USE_COLOR else ""
    BG_RED = "\033[41m" if USE_COLOR else ""
    BG_GREEN = "\033[42m" if USE_COLOR else ""


_U = {
    "tl": "┌" if USE_UNICODE else "+",
    "tr": "┐" if USE_UNICODE else "+",
    "bl": "└" if USE_UNICODE else "+",
    "br": "┘" if USE_UNICODE else "+",
    "h": "─" if USE_UNICODE else "-",
    "v": "│" if USE_UNICODE else "|",
    "ok": "✔" if USE_UNICODE else "OK",
    "er": "✘" if USE_UNICODE else "!!",
    "in": "i",
    "dt": "." if not USE_UNICODE else "·",
}


def _p(message: str) -> None:
    """Print com flush imediato e fallback de encoding."""
    try:
        print(message, flush=True)
    except UnicodeEncodeError:
        print(
            message.encode("utf-8", errors="replace").decode("ascii", errors="replace"),
            flush=True,
        )


def _print_header(title: str, width: int = 62) -> None:
    bar = _U["h"] * width
    _p(f"\n{C.BOLD}{C.CYAN}{_U['tl']}{bar}{_U['tr']}{C.RESET}")
    pad = width - len(title)
    _p(
        f"{C.BOLD}{C.CYAN}{_U['v']}{' ' * (pad // 2)}{title}{' ' * (pad - pad // 2)}{_U['v']}{C.RESET}"
    )
    _p(f"{C.BOLD}{C.CYAN}{_U['bl']}{bar}{_U['br']}{C.RESET}")


def _print_section(title: str, width: int = 62) -> None:
    bar = _U["h"] * max(0, width - len(title) - 4)
    _p(f"\n{C.BOLD}{C.BLUE}-- {title} {bar}{C.RESET}")


def _print_step(icon: str, label: str, detail: str = "") -> None:
    det = f"  {C.DIM}{detail}{C.RESET}" if detail else ""
    _p(f"  {icon}  {C.BOLD}{label}{C.RESET}{det}")


def _print_ok(msg: str) -> None:
    _p(f"  {C.GREEN}{_U['ok']}{C.RESET}  {msg}")


def _print_warn(msg: str) -> None:
    _p(f"  {C.YELLOW}{_U['er']}{C.RESET}  {C.YELLOW}{msg}{C.RESET}")


def _print_info(msg: str) -> None:
    _p(f"  {C.CYAN}{_U['in']}{C.RESET}  {C.DIM}{msg}{C.RESET}")


def _print_output_block(output: str, max_lines: int = 40) -> None:
    lines = output.strip().splitlines()
    if not lines:
        _print_info("(sem output)")
        return
    sep = f"  {C.DIM}{_U['dt'] * 58}{C.RESET}"
    _p(sep)
    for line in lines[:max_lines]:
        _p(f"  {C.DIM}{_U['v']}{C.RESET} {line}")
    if len(lines) > max_lines:
        _p(f"  {C.DIM}{_U['v']} ... +{len(lines) - max_lines} linhas omitidas{C.RESET}")
    _p(sep)


def _duration_str(s: float) -> str:
    return f"{s * 1000:.0f}ms" if s < 1 else f"{s:.1f}s"


def _print_summary_table(tool_results: dict, durations: dict) -> None:
    _p(f"\n  {C.BOLD}{'Ferramenta':<14} {'Status':<14} {'Duracao'}{C.RESET}")
    _p(f"  {_U['h'] * 40}")
    for tool, passed in tool_results.items():
        dur = _duration_str(durations.get(tool, 0))
        status = f"{C.GREEN}PASSOU{C.RESET}" if passed else f"{C.RED}FALHOU{C.RESET}"
        _p(f"  {C.BOLD}{tool.upper():<14}{C.RESET} {status:<22} {C.DIM}{dur}{C.RESET}")
    _p(f"  {_U['h'] * 40}")


# ──────────────────────────────────────────────────────────────────────────────
#  GITHUB CLIENT
# ──────────────────────────────────────────────────────────────────────────────


class GitHubClient:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token
        self.base = f"https://api.github.com/repos/{repo}"

    def _request(self, method: str, path: str, body: dict | None = None) -> dict | list:
        url = f"{self.base}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:  # nosec B310
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            _print_warn(
                f"[GitHub API] {method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')}"
            )
            return {}

    def list_open_issues(self, label: str) -> list:
        r = self._request("GET", f"/issues?state=open&labels={label}&per_page=100")
        return r if isinstance(r, list) else []

    def create_issue(self, title: str, body: str, labels: list) -> int | None:
        r = self._request(
            "POST", "/issues", {"title": title, "body": body, "labels": labels}
        )
        return r.get("number") if isinstance(r, dict) else None

    def close_issue(self, number: int, comment: str) -> None:
        self._request("POST", f"/issues/{number}/comments", {"body": comment})
        self._request(
            "PATCH",
            f"/issues/{number}",
            {"state": "closed", "state_reason": "completed"},
        )


# ──────────────────────────────────────────────────────────────────────────────
#  PARSERS DE OUTPUT
# ──────────────────────────────────────────────────────────────────────────────


def _parse_flake8_output(output: str) -> dict:
    lines = [l for l in output.strip().splitlines() if l.strip()]
    error_codes: dict[str, int] = {}
    affected_files: set[str] = set()
    for line in lines:
        parts = line.split(":")
        if len(parts) >= 4:
            try:
                affected_files.add(Path(parts[0].strip()).name)
                code = parts[3].strip().split()[0] if parts[3].strip() else "?"
                error_codes[code] = error_codes.get(code, 0) + 1
            except Exception:
                pass
    return {
        "total": len(lines),
        "error_codes": error_codes,
        "affected_files": sorted(affected_files),
    }


def _parse_bandit_output(output: str) -> dict:
    return {
        "high": output.count("Severity: High"),
        "medium": output.count("Severity: Medium"),
        "low": output.count("Severity: Low"),
    }


def _parse_black_output(output: str) -> dict:
    # Captura nomes dos arquivos reformatados
    reformatted = [
        line.split("reformatted ")[-1].strip()
        for line in output.splitlines()
        if "reformatted " in line
    ]
    return {
        "would_reformat": output.count("would reformat"),
        "reformatted": reformatted,
        "unchanged": output.count("left unchanged"),
    }


def _get_env_info() -> dict:
    return {
        "python": platform.python_version(),
        "os": platform.system(),
        "branch": os.environ.get("GITHUB_REF_NAME", "N/A"),
        "commit": (os.environ.get("GITHUB_SHA", "") or "N/A")[:8],
        "actor": os.environ.get("GITHUB_ACTOR", "N/A"),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "N/A"),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
#  ISSUE BODIES
# ──────────────────────────────────────────────────────────────────────────────

_TOOL_META = {
    "black": {"icon": "[BLACK]", "label": "Formatacao de Codigo (Black)"},
    "flake8": {"icon": "[FLAKE8]", "label": "Analise de Lint e Estilo (Flake8)"},
    "bandit": {"icon": "[BANDIT]", "label": "Analise de Seguranca (Bandit)"},
}

_FLAKE8_DESCRIPTIONS = {
    "E1": "Indentacao",
    "E2": "Espacamento",
    "E3": "Linha em branco",
    "E4": "Importacoes",
    "E5": "Comprimento de linha",
    "E7": "Declaracao",
    "W": "Aviso geral",
    "F4": "Importacao nao usada",
    "F8": "Nome nao definido",
}

_FIX_GUIDES = {
    "black": (
        "## Como Corrigir\n\n" "```bash\npython -m black apps/ --line-length=88\n```\n"
    ),
    "flake8": (
        "## Como Corrigir\n\n"
        "```bash\npython -m flake8 apps/ --max-line-length=200 --extend-ignore=E203,W503\n```\n"
    ),
    "bandit": (
        "## Como Corrigir\n\n"
        "```bash\npython -m bandit -r apps/ -f txt\n```\n"
        "Para falsos positivos justificados:\n"
        "```python\nresult = subprocess.run(cmd)  # nosec B603\n```\n"
    ),
}


def _build_issue_body(tool: str, output: str, run_url: str, env: dict) -> str:
    meta = _TOOL_META.get(tool, {"icon": "[??]", "label": tool.upper()})
    run_link = f"[Ver execucao]({run_url})" if run_url != "N/A" else "N/A"
    lines = [
        f"# {meta['icon']} {meta['label']} - Problemas Detectados",
        "",
        "> Issue criada automaticamente pelo **Code Analysis Bot**.",
        "",
        "## Contexto da Execucao",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| Workflow | `{env['workflow']}` |",
        f"| Branch   | `{env['branch']}` |",
        f"| Commit   | `{env['commit']}` |",
        f"| Autor    | `{env['actor']}` |",
        f"| Python   | `{env['python']}` |",
        f"| Data     | `{env['timestamp']}` |",
        f"| Execucao | {run_link} |",
        "",
    ]

    if tool == "flake8":
        stats = _parse_flake8_output(output)
        lines += [
            "## Resumo",
            "",
            f"- Total de ocorrencias: `{stats['total']}`",
            f"- Arquivos afetados: `{len(stats['affected_files'])}`",
        ]
        if stats["affected_files"]:
            lines.append(
                "- Arquivos: "
                + " ".join(f"`{f}`" for f in stats["affected_files"][:10])
            )
        if stats["error_codes"]:
            lines += ["", "| Codigo | Ocorrencias | Categoria |", "|---|---|---|"]
            for code, count in sorted(
                stats["error_codes"].items(), key=lambda x: -x[1]
            ):
                prefix = code[:2] if len(code) >= 2 else code[:1]
                desc = _FLAKE8_DESCRIPTIONS.get(
                    prefix, _FLAKE8_DESCRIPTIONS.get(code[:1], "-")
                )
                lines.append(f"| `{code}` | {count} | {desc} |")
        lines.append("")

    elif tool == "bandit":
        stats = _parse_bandit_output(output)
        lines += [
            "## Resumo de Vulnerabilidades",
            "",
            "| Severidade | Ocorrencias | Acao |",
            "|---|---|---|",
            f"| High   | **{stats['high']}**   | Corrigir imediatamente |",
            f"| Medium | **{stats['medium']}** | Corrigir |",
            f"| Low    | {stats['low']}        | Ignorado pela politica |",
            f"| **Total bloqueante** | **{stats['high'] + stats['medium']}** | - |",
            "",
        ]

    elif tool == "black":
        stats = _parse_black_output(output)
        lines += [
            "## Resumo de Formatacao",
            "",
            f"- Arquivos que precisam de reformatacao: `{stats['would_reformat']}`",
            f"- Arquivos ja formatados: `{stats['unchanged']}`",
            "",
        ]

    lines.append(_FIX_GUIDES.get(tool, ""))
    lines += [
        "## Output Completo",
        "",
        "```",
        output.strip()[:8000],
        "```",
        "",
        "---",
        "_Issue gerenciada automaticamente pelo **Code Analysis Bot**._  ",
        "_Nao renomeie esta issue - o titulo e usado para deduplicacao._",
    ]
    return "\n".join(lines)


def _build_close_comment(tool: str, run_url: str, env: dict) -> str:
    run_link = f"[Ver execucao]({run_url})" if run_url != "N/A" else "N/A"
    return "\n".join(
        [
            f"## {tool.upper()} - Problema Resolvido",
            "",
            f"> O **{tool.upper()}** passou sem erros na execucao mais recente.",
            "",
            "| Campo | Valor |",
            "|---|---|",
            f"| Branch   | `{env['branch']}` |",
            f"| Commit   | `{env['commit']}` |",
            f"| Autor    | `{env['actor']}` |",
            f"| Data     | `{env['timestamp']}` |",
            f"| Execucao | {run_link} |",
            "",
            "_Issue fechada automaticamente pelo **Code Analysis Bot**._",
        ]
    )


# ──────────────────────────────────────────────────────────────────────────────
#  SYNC DE ISSUES
# ──────────────────────────────────────────────────────────────────────────────


def sync_github_issues(gh, tool, passed, output, run_url, env) -> None:
    title = f"[{tool.upper()}] Problemas de qualidade de codigo detectados"
    open_issues = gh.list_open_issues(tool)

    if not passed:
        if not open_issues:
            body = _build_issue_body(tool, output, run_url, env)
            number = gh.create_issue(
                title, body, ["automated", "code-analysis", tool, "needs-attention"]
            )
            if number:
                _print_ok(f"Issue #{number} criada -> {tool.upper()}")
            else:
                _print_warn(f"Falha ao criar issue para {tool.upper()}")
        else:
            _print_info(
                f"Issue #{open_issues[0].get('number', '?')} ja existe para {tool.upper()} - nenhuma acao"
            )
    else:
        if open_issues:
            for issue in open_issues:
                number = issue.get("number")
                if number:
                    gh.close_issue(number, _build_close_comment(tool, run_url, env))
                    _print_ok(f"Issue #{number} fechada -> {tool.upper()} resolvido")
        else:
            _print_info(f"{tool.upper()} passou e nenhuma issue aberta - OK")


# ──────────────────────────────────────────────────────────────────────────────
#  CODE ANALYSIS BOT
# ──────────────────────────────────────────────────────────────────────────────


class CodeAnalysisBot:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.apps_dir = project_root / "apps"

    def _run_tool(self, tool_name: str, args: list) -> tuple[bool, str, str]:
        try:
            result = subprocess.run(  # nosec B603
                [sys.executable, "-m", tool_name] + args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.project_root,
                check=False,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def run_analysis(
        self, fix=False, security_only=False, lint_only=False
    ) -> tuple[dict, dict]:
        results: dict = {}
        durations: dict = {}

        # ── BLACK ──────────────────────────────────────────────────────────────
        if not security_only:
            mode = (
                "Aplicando correcoes automaticas" if fix else "Verificando formatacao"
            )
            _print_section("BLACK")
            _print_step("*", f"Black - {mode}", "linha max: 88")

            black_args = [str(self.apps_dir), "--line-length=88"]
            if not fix:
                black_args.append("--check")

            t0 = time.monotonic()
            success, stdout, stderr = self._run_tool("black", black_args)
            durations["black"] = time.monotonic() - t0

            output = stdout or stderr
            results["black"] = success
            results["black_output"] = output

            if success:
                stats = _parse_black_output(output)
                _print_ok(
                    f"Formatacao OK - {stats['unchanged']} arquivo(s) sem alteracoes"
                )
                if fix and stats["reformatted"]:
                    _print_info(f"Reformatados: {len(stats['reformatted'])} arquivo(s)")
                    for f in stats["reformatted"]:
                        _print_info(f"  -> {f}")
            else:
                stats = _parse_black_output(output)
                _print_warn(
                    f"{stats['would_reformat']} arquivo(s) precisam de reformatacao"
                )
                _print_output_block(output)

        # ── FLAKE8 ─────────────────────────────────────────────────────────────
        if not security_only:
            _print_section("FLAKE8")
            _print_step("*", "Flake8 - Analise de lint e estilo", "max: 200 cols")

            t0 = time.monotonic()
            success, stdout, stderr = self._run_tool(
                "flake8",
                [
                    str(self.apps_dir),
                    "--max-line-length=200",
                    "--extend-ignore=E203,W503",
                ],
            )
            durations["flake8"] = time.monotonic() - t0

            output = stdout or stderr
            results["flake8"] = success
            results["flake8_output"] = output

            if success:
                _print_ok("Nenhum problema de lint encontrado")
            else:
                stats = _parse_flake8_output(output)
                _print_warn(
                    f"{stats['total']} ocorrencia(s) em {len(stats['affected_files'])} arquivo(s)"
                )
                if stats["error_codes"]:
                    codes_str = ", ".join(
                        f"{c}x{n}"
                        for c, n in sorted(
                            stats["error_codes"].items(), key=lambda x: -x[1]
                        )[:6]
                    )
                    _print_info(f"Codigos mais frequentes: {codes_str}")
                _print_output_block(output)

        # ── BANDIT ─────────────────────────────────────────────────────────────
        if not lint_only:
            _print_section("BANDIT")
            _print_step(
                "*", "Bandit - Analise de seguranca", "excluindo migrations e cache"
            )

            t0 = time.monotonic()
            success, stdout, stderr = self._run_tool(
                "bandit",
                [
                    "-r",
                    str(self.apps_dir),
                    "-f",
                    "txt",
                    "--exclude",
                    "*/migrations/*,*/__pycache__/*",
                ],
            )
            durations["bandit"] = time.monotonic() - t0

            output = stdout or stderr
            has_issues = "Severity: Medium" in output or "Severity: High" in output

            results["bandit"] = not has_issues
            results["bandit_output"] = output

            if results["bandit"]:
                stats = _parse_bandit_output(output)
                low_note = f" ({stats['low']} low ignorado)" if stats["low"] else ""
                _print_ok(f"Nenhuma vulnerabilidade Medium/High{low_note}")
            else:
                stats = _parse_bandit_output(output)
                _print_warn(
                    f"{stats['high']} High  |  {stats['medium']} Medium  |  {stats['low']} Low (ignorado)"
                )
                _print_output_block(output)

        return results, durations


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Analise de codigo: lint, formatacao e seguranca"
    )
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--security-only", action="store_true")
    parser.add_argument("--lint-only", action="store_true")
    parser.add_argument("--create-issues", action="store_true")
    parser.add_argument("--github-repo", type=str, default="")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    bot = CodeAnalysisBot(project_root=project_root)
    env = _get_env_info()

    _print_header("  CODE ANALYSIS BOT  ")
    _print_info(f"Projeto  : {project_root}")
    _print_info(f"Apps dir : {bot.apps_dir}")
    _print_info(f"Python   : {env['python']}  |  {env['os']}")
    _print_info(f"Branch   : {env['branch']}  |  Commit: {env['commit']}")
    if args.fix:
        _print_info("Modo     : FIX - Black ira reformatar arquivos")
    if args.security_only:
        _print_info("Escopo   : apenas seguranca (Bandit)")
    if args.lint_only:
        _print_info("Escopo   : apenas lint (Black + Flake8)")

    t_start = time.monotonic()
    results, durations = bot.run_analysis(
        fix=args.fix,
        security_only=args.security_only,
        lint_only=args.lint_only,
    )
    total_duration = time.monotonic() - t_start

    # ── GITHUB ISSUES ──────────────────────────────────────────────────────────
    if args.create_issues and args.github_repo:
        _print_section("GITHUB ISSUES")
        token = os.environ.get("GITHUB_TOKEN", "")
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        run_url = (
            f"{server}/{args.github_repo}/actions/runs/{run_id}" if run_id else "N/A"
        )

        if token:
            gh = GitHubClient(repo=args.github_repo, token=token)
            for key in ("black", "flake8", "bandit"):
                if key in results:
                    sync_github_issues(
                        gh=gh,
                        tool=key,
                        passed=bool(results[key]),
                        output=str(results.get(f"{key}_output", "")),
                        run_url=run_url,
                        env=env,
                    )
        else:
            _print_warn("GITHUB_TOKEN nao encontrado - integracao com issues ignorada")

    # ── RESULTADO FINAL ────────────────────────────────────────────────────────
    tool_results = {k: bool(v) for k, v in results.items() if not k.endswith("_output")}

    _print_section(f"RESULTADO FINAL  ({_duration_str(total_duration)} total)")

    if not tool_results:
        _print_info("Nenhuma ferramenta foi executada.")
        sys.exit(0)

    _print_summary_table(tool_results, durations)

    if all(tool_results.values()):
        _p(f"\n  {C.BG_GREEN}{C.BOLD}  OK  TODAS AS VERIFICACOES PASSARAM  {C.RESET}\n")
        sys.exit(0)
    else:
        failed = [k.upper() for k, v in tool_results.items() if not v]
        _p(f"\n  {C.BG_RED}{C.BOLD}  FALHA EM: {', '.join(failed)}  {C.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
