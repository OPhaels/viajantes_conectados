import sys
import time
from pathlib import Path

from django.core.management.base import BaseCommand

# Garante que scripts/ está no sys.path para importar o bot standalone
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from scripts.bot_code_analysis import (  # noqa: E402
    C,
    CodeAnalysisBot,
    _duration_str,
    _get_env_info,
    _p,
    _print_header,
    _print_info,
    _print_section,
    _print_summary_table,
)


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

    def handle(self, *args, **options):
        bot = CodeAnalysisBot(project_root=_PROJECT_ROOT)
        env = _get_env_info()

        _print_header("  CODE ANALYSIS BOT  ")
        _print_info(f"Projeto  : {_PROJECT_ROOT}")
        _print_info(f"Apps dir : {bot.apps_dir}")
        _print_info(f"Python   : {env['python']}  |  {env['os']}")
        _print_info(f"Branch   : {env['branch']}  |  Commit: {env['commit']}")

        if options["fix"]:
            _print_info("Modo     : FIX - Black ira reformatar arquivos")
        if options["security_only"]:
            _print_info("Escopo   : apenas seguranca (Bandit)")
        if options["lint_only"]:
            _print_info("Escopo   : apenas lint (Black + Flake8)")

        t_start = time.monotonic()
        results, durations = bot.run_analysis(
            fix=options["fix"],
            security_only=options["security_only"],
            lint_only=options["lint_only"],
        )
        total_duration = time.monotonic() - t_start

        tool_results = {
            k: bool(v) for k, v in results.items() if not k.endswith("_output")
        }

        _print_section(f"RESULTADO FINAL  ({_duration_str(total_duration)} total)")

        if not tool_results:
            _print_info("Nenhuma ferramenta foi executada.")
            return

        _print_summary_table(tool_results, durations)

        if all(tool_results.values()):
            _p(
                f"\n  {C.BG_GREEN}{C.BOLD}  OK  TODAS AS VERIFICACOES PASSARAM  {C.RESET}\n"
            )
        else:
            failed = [k.upper() for k, v in tool_results.items() if not v]
            _p(f"\n  {C.BG_RED}{C.BOLD}  FALHA EM: {', '.join(failed)}  {C.RESET}\n")
            sys.exit(1)
