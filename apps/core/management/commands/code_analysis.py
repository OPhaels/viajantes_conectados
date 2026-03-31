import subprocess  # nosec B404
import sys
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Executa analise de codigo: linting, formatacao e seguranca"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Aplica correcoes automaticas com Black",
        )
        parser.add_argument(
            "--security-only",
            action="store_true",
            help="Executa apenas Bandit",
        )
        parser.add_argument(
            "--lint-only",
            action="store_true",
            help="Executa apenas Flake8 e Black",
        )

    def _safe_print(self, message: str) -> None:
        """Evita UnicodeEncodeError no Windows (cp1252)."""
        try:
            self.stdout.write(message)
        except UnicodeEncodeError:
            self.stdout.write(
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
                cwd=Path.cwd(),
                check=False,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def handle(self, *args, **options):
        project_root = Path(__file__).resolve().parents[4]
        apps_dir = project_root / "apps"

        self._safe_print("\n[START] Code Analysis\n")

        has_errors = False

        # -------------------------
        # BLACK
        # -------------------------
        if options["fix"] and not options["security_only"]:
            self._safe_print("[BLACK] Formatando...")

            success, stdout, stderr = self._run_tool(
                "black", [str(apps_dir), "--line-length=88"]
            )

            if success:
                self._safe_print("[OK] Black passou")
            else:
                self._safe_print("[WARN] Black encontrou problemas")
                self.stdout.write(stdout or stderr)
                has_errors = True

        # -------------------------
        # FLAKE8
        # -------------------------
        if not options["security_only"]:
            self._safe_print("[FLAKE8] Executando...")

            success, stdout, stderr = self._run_tool(
                "flake8",
                [
                    str(apps_dir),
                    "--max-line-length=200",
                    "--extend-ignore=E203,W503",
                ],
            )

            if success:
                self._safe_print("[OK] Nenhum problema de lint")
            else:
                self._safe_print("[WARN] Problemas de lint encontrados")
                self.stdout.write(stdout or stderr)
                has_errors = True

        # -------------------------
        # BANDIT
        # -------------------------
        if not options["lint_only"]:
            self._safe_print("[BANDIT] Executando...")

            success, stdout, stderr = self._run_tool(
                "bandit",
                [
                    "-r",
                    str(apps_dir),
                    "-f",
                    "txt",
                    "--exclude",
                    "*/migrations/*,*/__pycache__/*",
                ],
            )

            # Falha somente se encontrar Medium ou High — ignora Low
            if not ("Severity: Medium" in stdout or "Severity: High" in stdout):
                success = True

            if success:
                self._safe_print("[OK] Nenhum problema de seguranca")
            else:
                self._safe_print("[WARN] Problemas de seguranca encontrados")
                self.stdout.write(stdout or stderr)
                has_errors = True

        # -------------------------
        # RESULTADO FINAL
        # -------------------------
        self.stdout.write("\n" + "=" * 40)

        if has_errors:
            self.stdout.write("[FAIL] Ha problemas no codigo")
            sys.exit(1)
        else:
            self.stdout.write("[SUCCESS] Tudo OK")
