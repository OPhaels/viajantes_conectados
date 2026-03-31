import argparse
import json
import os
import subprocess  # nosec B404
import sys
import urllib.request
from pathlib import Path


class GitHubClient:
    """Cliente minimo para a API do GitHub usando apenas stdlib."""

    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token
        self.base = f"https://api.github.com/repos/{repo}"

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
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
            print(f"[GitHub API] {method} {path} -> HTTP {e.code}: {e.read().decode()}")
            return {}

    def list_open_issues(self, label: str) -> list:
        path = f"/issues?state=open&labels={label}&per_page=100"
        result = self._request("GET", path)
        return result if isinstance(result, list) else []

    def create_issue(self, title: str, body: str, labels: list) -> int | None:
        result = self._request(
            "POST",
            "/issues",
            {"title": title, "body": body, "labels": labels},
        )
        return result.get("number")

    def close_issue(self, number: int, comment: str) -> None:
        self._request(
            "POST",
            f"/issues/{number}/comments",
            {"body": comment},
        )
        self._request(
            "PATCH",
            f"/issues/{number}",
            {"state": "closed", "state_reason": "completed"},
        )


class CodeAnalysisBot:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.apps_dir = project_root / "apps"

    def _safe_print(self, message: str) -> None:
        """Evita UnicodeEncodeError no Windows (cp1252)."""
        try:
            print(message)
        except UnicodeEncodeError:
            print(
                message.encode("utf-8", errors="replace").decode(
                    "ascii", errors="replace"
                )
            )

    def _run_tool(self, tool_name: str, args: list) -> tuple[bool, str, str]:
        """Executa uma ferramenta de linha de comando com seguranca."""
        try:
            cmd = [sys.executable, "-m", tool_name] + args
            result = subprocess.run(  # nosec B603
                cmd,
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
        self,
        fix: bool = False,
        security_only: bool = False,
        lint_only: bool = False,
    ) -> dict[str, bool | str]:
        """Executa as ferramentas e retorna resultado por ferramenta."""
        results: dict[str, bool | str] = {}

        # -------------------------
        # BLACK
        # Sempre verifica; aplica correcoes apenas com --fix
        # -------------------------
        if not security_only:
            if fix:
                self._safe_print("[BLACK] Formatando...")
                black_args = [str(self.apps_dir), "--line-length=88"]
            else:
                self._safe_print("[BLACK] Verificando...")
                black_args = [str(self.apps_dir), "--line-length=88", "--check"]

            success, stdout, stderr = self._run_tool("black", black_args)
            results["black"] = success
            results["black_output"] = stdout or stderr

            if success:
                self._safe_print("[OK] Black passou")
            else:
                self._safe_print("[WARN] Black encontrou problemas")
                print(stdout or stderr)

        # -------------------------
        # FLAKE8
        # -------------------------
        if not security_only:
            self._safe_print("[FLAKE8] Executando...")
            success, stdout, stderr = self._run_tool(
                "flake8",
                [
                    str(self.apps_dir),
                    "--max-line-length=200",
                    "--extend-ignore=E203,W503",
                ],
            )
            results["flake8"] = success
            results["flake8_output"] = stdout or stderr

            if success:
                self._safe_print("[OK] Nenhum problema de lint")
            else:
                self._safe_print("[WARN] Problemas de lint encontrados")
                print(stdout or stderr)

        # -------------------------
        # BANDIT
        # -------------------------
        if not lint_only:
            self._safe_print("[BANDIT] Executando...")
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
            # Falha somente se encontrar Medium ou High — ignora Low
            if not ("Severity: Medium" in stdout or "Severity: High" in stdout):
                success = True
            results["bandit"] = success
            results["bandit_output"] = stdout or stderr

            if success:
                self._safe_print("[OK] Nenhum problema de seguranca")
            else:
                self._safe_print("[WARN] Problemas de seguranca encontrados")
                print(stdout or stderr)

        return results


def sync_github_issues(
    gh: GitHubClient,
    tool: str,
    passed: bool,
    output: str,
    run_url: str,
) -> None:
    """Cria issue se falhou, fecha issues abertas se passou."""
    label = tool
    common_labels = ["automated", "code-analysis", label, "needs-attention"]
    title = f"Problemas de {tool.upper()} detectados"
    open_issues = gh.list_open_issues(label)

    if not passed:
        if not open_issues:
            body = (
                f"## Problemas detectados pelo {tool.upper()}\n\n"
                f"**Execucao:** {run_url}\n\n"
                f"```\n{output[:6000]}\n```\n\n"
                f"> Issue criada automaticamente pelo Code Analysis Bot."
            )
            number = gh.create_issue(title, body, common_labels)
            if number:
                print(f"[GitHub] Issue #{number} criada para {tool.upper()}")
        else:
            print(f"[GitHub] Issue aberta para {tool.upper()} ja existe — nenhuma acao")
    else:
        for issue in open_issues:
            number = issue.get("number")
            if number:
                comment = (
                    f"## Problema resolvido\n\n"
                    f"O {tool.upper()} passou sem erros na execucao mais recente.\n\n"
                    f"**Execucao:** {run_url}\n\n"
                    f"> Issue fechada automaticamente pelo Code Analysis Bot."
                )
                gh.close_issue(number, comment)
                print(f"[GitHub] Issue #{number} fechada para {tool.upper()}")


def main():
    parser = argparse.ArgumentParser(
        description="Analise de codigo: lint, formato e seguranca"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Aplica correcoes automaticas com Black"
    )
    parser.add_argument(
        "--security-only", action="store_true", help="Executa apenas Bandit"
    )
    parser.add_argument(
        "--lint-only", action="store_true", help="Executa apenas Flake8 e Black"
    )
    parser.add_argument(
        "--create-issues",
        action="store_true",
        help="Cria/fecha issues no GitHub conforme resultado (usado pelo Actions)",
    )
    parser.add_argument(
        "--github-repo",
        type=str,
        default="",
        help="Repositorio GitHub no formato owner/repo (usado pelo Actions)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    bot = CodeAnalysisBot(project_root=project_root)

    print("\n" + "=" * 40)
    print("Resultado:")

    results = bot.run_analysis(
        fix=args.fix,
        security_only=args.security_only,
        lint_only=args.lint_only,
    )

    # -------------------------
    # INTEGRACAO COM GITHUB
    # -------------------------
    if args.create_issues and args.github_repo:
        token = os.environ.get("GITHUB_TOKEN", "")
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        run_url = f"{server}/{args.github_repo}/actions/runs/{run_id}" if run_id else ""

        if token:
            gh = GitHubClient(repo=args.github_repo, token=token)
            tool_map = {
                "black": ("black", results.get("black_output", "")),
                "flake8": ("flake8", results.get("flake8_output", "")),
                "bandit": ("bandit", results.get("bandit_output", "")),
            }
            for key, (tool, output) in tool_map.items():
                if key in results:
                    sync_github_issues(
                        gh=gh,
                        tool=tool,
                        passed=bool(results[key]),
                        output=str(output),
                        run_url=run_url,
                    )
        else:
            print("[GitHub] GITHUB_TOKEN nao encontrado — integracao ignorada")

    # -------------------------
    # RESULTADO FINAL
    # -------------------------
    print("=" * 40 + "\n")

    tool_results = {k: v for k, v in results.items() if not k.endswith("_output")}
    has_errors = not all(tool_results.values()) if tool_results else False

    if not has_errors:
        print("[SUCCESS] Tudo OK")
        sys.exit(0)
    else:
        print("[FAIL] Ha problemas no codigo")
        sys.exit(1)


if __name__ == "__main__":
    main()
