#!/usr/bin/env python3
"""
FPAT CLI - Firewall Policy Analysis Tool
메인 CLI 애플리케이션 엔트리포인트
"""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from .commands import firewall, policy_compare, analyzer, deletion
from .utils.config import Config
from .utils.logger import setup_logger

# 콘솔 초기화
console = Console()
logger = setup_logger()

# 메인 앱 생성
app = typer.Typer(
    name="fpat",
    help="🔥 Firewall Policy Analysis Tool - 방화벽 정책 분석 및 관리 도구",
    rich_markup_mode="rich",
    add_completion=False,
    no_args_is_help=True
)

# 서브커맨드 추가
app.add_typer(firewall.app, name="firewall", help="🛡️  방화벽 연동 및 데이터 수집")
app.add_typer(policy_compare.app, name="compare", help="🔍 정책 및 객체 비교 분석")
app.add_typer(analyzer.app, name="analyze", help="📊 정책 분석 (중복성, Shadow 등)")
app.add_typer(deletion.app, name="deletion", help="🗑️  정책 삭제 영향도 분석")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", 
        help="상세한 로그 출력"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c",
        help="설정 파일 경로"
    )
):
    """
    🔥 FPAT (Firewall Policy Analysis Tool)
    
    방화벽 정책 분석 및 관리를 위한 통합 CLI 도구입니다.
    """
    # 설정 초기화
    config = Config(config_file)
    
    # 로깅 레벨 설정
    if verbose:
        logger.setLevel("DEBUG")
        logger.debug("Verbose 모드가 활성화되었습니다.")


@app.command()
def version():
    """버전 정보를 표시합니다."""
    from . import __version__, __author__
    
    version_panel = Panel(
        f"[bold blue]FPAT CLI[/bold blue] v{__version__}\n"
        f"[dim]작성자: {__author__}[/dim]\n"
        f"[dim]방화벽 정책 분석 도구[/dim]",
        title="📋 Version Info",
        border_style="blue"
    )
    console.print(version_panel)


@app.command()
def menu():
    """대화형 메뉴를 표시합니다."""
    show_main_menu()


def show_main_menu():
    """메인 메뉴를 표시합니다."""
    console.clear()
    
    # 타이틀 표시
    title = Text("🔥 FPAT CLI - Firewall Policy Analysis Tool", style="bold red")
    console.print(Panel(title, border_style="red"))
    
    # 메뉴 테이블 생성
    table = Table(
        title="📋 사용 가능한 명령어",
        box=box.ROUNDED,
        border_style="cyan"
    )
    
    table.add_column("명령어", style="bold green", min_width=15)
    table.add_column("설명", style="white")
    table.add_column("예시", style="dim")
    
    # 메뉴 항목 추가
    menu_items = [
        ("firewall", "방화벽 연동 및 데이터 수집", "fpat firewall collect --help"),
        ("compare", "정책 및 객체 비교 분석", "fpat compare policies --help"),
        ("analyze", "정책 분석 (중복성, Shadow 등)", "fpat analyze redundancy --help"),
        ("deletion", "정책 삭제 영향도 분석", "fpat deletion analyze --help"),
        ("version", "버전 정보 표시", "fpat version"),
        ("--help", "도움말 표시", "fpat --help")
    ]
    
    for command, description, example in menu_items:
        table.add_row(command, description, example)
    
    console.print(table)
    
    # 사용법 안내
    usage_panel = Panel(
        "[bold]💡 사용법:[/bold]\n"
        "• 각 명령어 뒤에 [cyan]--help[/cyan]를 붙이면 상세한 도움말을 볼 수 있습니다.\n"
        "• 대부분의 결과는 Excel 파일로 저장됩니다.\n"
        "• [cyan]-v[/cyan] 옵션으로 상세한 로그를 확인할 수 있습니다.",
        title="📖 가이드",
        border_style="yellow"
    )
    console.print(usage_panel)


if __name__ == "__main__":
    app()