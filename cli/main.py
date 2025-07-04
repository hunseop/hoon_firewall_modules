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
from .utils.completion import setup_shell_completion

# interactive 모듈은 조건부 import
try:
    from .utils.interactive import (
        interactive_main_menu, show_success_message, show_error_message,
        interactive_firewall_submenu, interactive_analyze_submenu, 
        interactive_compare_submenu, interactive_firewall_add,
        interactive_firewall_selector, interactive_vendor_selector,
        interactive_file_selector, interactive_search_type_selector,
        confirm_action, show_info_message
    )
    HAS_INTERACTIVE = True
except ImportError:
    HAS_INTERACTIVE = False
    
    # 대체 함수들
    def show_error_message(message): console.print(f"[red]{message}[/red]")
    def show_success_message(message): console.print(f"[green]{message}[/green]")

# 콘솔 초기화
console = Console()
logger = setup_logger()

# 메인 앱 생성
app = typer.Typer(
    name="fpat",
    help="🔥 Firewall Policy Analysis Tool - 방화벽 정책 분석 및 관리 도구",
    rich_markup_mode="rich",
    add_completion=True,  # 자동완성 활성화
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


@app.command()
def completion():
    """Shell 자동완성 설정 방법을 표시합니다."""
    instructions = setup_shell_completion()
    console.print(Panel(instructions, title="⚡ 자동완성 설정", border_style="yellow"))


@app.command()
def interactive():
    """대화형 모드로 CLI를 실행합니다."""
    if not HAS_INTERACTIVE:
        console.print("[red]❌ 대화형 모드를 사용하려면 questionary 패키지가 필요합니다.[/red]")
        console.print("[yellow]💡 설치: pip install questionary prompt-toolkit[/yellow]")
        raise typer.Exit(1)
    
    try:
        run_interactive_mode()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 대화형 모드를 종료합니다.[/yellow]")
    except Exception as e:
        show_error_message(f"오류가 발생했습니다: {e}")


def run_interactive_mode():
    """대화형 모드 실행"""
    console.clear()
    
    while True:
        choice = interactive_main_menu()
        
        if not choice or choice == "exit":
            console.print("[green]👋 FPAT CLI를 종료합니다. 안녕히 가세요![/green]")
            break
        
        if choice == "firewall":
            run_interactive_firewall()
        elif choice == "compare":
            run_interactive_compare()
        elif choice == "analyze":
            run_interactive_analyze()
        elif choice == "deletion":
            run_interactive_deletion()
        elif choice == "completion":
            instructions = setup_shell_completion()
            console.print(Panel(instructions, title="⚡ 자동완성 설정", border_style="yellow"))
        elif choice == "version":
            from . import __version__, __author__
            version_panel = Panel(
                f"[bold blue]FPAT CLI[/bold blue] v{__version__}\n"
                f"[dim]작성자: {__author__}[/dim]\n"
                f"[dim]방화벽 정책 분석 도구[/dim]",
                title="📋 Version Info",
                border_style="blue"
            )
            console.print(version_panel)
        
        # 계속 진행할지 확인
        if not confirm_action("계속 진행하시겠습니까?"):
            break


def run_interactive_firewall():
    """대화형 방화벽 기능"""
    while True:
        choice = interactive_firewall_submenu()
        
        if not choice or choice == "back":
            break
        
        if choice == "add":
            fw_data = interactive_firewall_add()
            if fw_data:
                try:
                    config = Config()
                    from .utils.config import FirewallConfig
                    fw_config = FirewallConfig(**{k: v for k, v in fw_data.items() if k != "name"})
                    config.add_firewall(fw_data["name"], fw_config)
                    show_success_message(f"방화벽 '{fw_data['name']}'이 추가되었습니다!")
                except Exception as e:
                    show_error_message(f"방화벽 추가 중 오류: {e}")
        
        elif choice == "list":
            config = Config()
            firewalls = config.config.firewalls
            if not firewalls:
                show_info_message("저장된 방화벽이 없습니다.")
            else:
                table = Table(title="🛡️ 저장된 방화벽 목록", border_style="cyan")
                table.add_column("이름", style="bold green")
                table.add_column("호스트", style="cyan")
                table.add_column("벤더", style="magenta")
                
                for name, fw_config in firewalls.items():
                    table.add_row(name, fw_config.hostname, fw_config.vendor)
                console.print(table)
        
        elif choice == "collect":
            fw_name = interactive_firewall_selector()
            if fw_name:
                show_info_message(f"'{fw_name}' 방화벽에서 데이터를 수집합니다...")
                # 실제 수집 로직은 기존 firewall.collect 함수 활용
                show_info_message("데이터 수집 기능은 개발 중입니다.")


def run_interactive_compare():
    """대화형 비교 기능"""
    while True:
        choice = interactive_compare_submenu()
        
        if not choice or choice == "back":
            break
        
        if choice == "policies":
            old_file = interactive_file_selector("이전 정책 파일을 선택하세요")
            if old_file:
                new_file = interactive_file_selector("새로운 정책 파일을 선택하세요")
                if new_file:
                    show_info_message(f"정책 비교: {old_file} vs {new_file}")
                    show_info_message("정책 비교 기능은 개발 중입니다.")
        
        elif choice == "objects":
            old_file = interactive_file_selector("이전 객체 파일을 선택하세요")
            if old_file:
                new_file = interactive_file_selector("새로운 객체 파일을 선택하세요")
                if new_file:
                    show_info_message(f"객체 비교: {old_file} vs {new_file}")
                    show_info_message("객체 비교 기능은 개발 중입니다.")
        
        elif choice == "full":
            show_info_message("전체 비교 기능을 실행합니다...")
            show_info_message("전체 비교 기능은 개발 중입니다.")


def run_interactive_analyze():
    """대화형 분석 기능"""
    while True:
        choice = interactive_analyze_submenu()
        
        if not choice or choice == "back":
            break
        
        if choice == "redundancy":
            policy_file = interactive_file_selector("분석할 정책 파일을 선택하세요")
            if policy_file:
                vendor = interactive_vendor_selector()
                if vendor:
                    show_info_message(f"중복성 분석: {policy_file} ({vendor})")
                    show_info_message("중복성 분석 기능은 개발 중입니다.")
        
        elif choice == "shadow":
            policy_file = interactive_file_selector("분석할 정책 파일을 선택하세요")
            if policy_file:
                vendor = interactive_vendor_selector()
                if vendor:
                    show_info_message(f"Shadow 분석: {policy_file} ({vendor})")
                    show_info_message("Shadow 분석 기능은 개발 중입니다.")
        
        elif choice == "filter":
            policy_file = interactive_file_selector("필터링할 정책 파일을 선택하세요")
            if policy_file:
                import questionary
                address = questionary.text("검색할 IP 주소를 입력하세요:").ask()
                if address:
                    search_type = interactive_search_type_selector()
                    if search_type:
                        show_info_message(f"IP 필터링: {policy_file}, {address} ({search_type})")
                        show_info_message("IP 필터링 기능은 개발 중입니다.")


def run_interactive_deletion():
    """대화형 삭제 영향도 분석"""
    policy_file = interactive_file_selector("분석할 정책 파일을 선택하세요")
    if policy_file:
        import questionary
        policies = questionary.text("삭제할 정책명들을 입력하세요 (쉼표로 구분):").ask()
        if policies:
            show_info_message(f"삭제 영향도 분석: {policy_file}")
            show_info_message(f"대상 정책: {policies}")
            show_info_message("삭제 영향도 분석 기능은 개발 중입니다.")


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
        ("interactive", "🎯 대화형 모드 (추천)", "fpat interactive"),
        ("firewall", "방화벽 연동 및 데이터 수집", "fpat firewall collect --help"),
        ("compare", "정책 및 객체 비교 분석", "fpat compare policies --help"),
        ("analyze", "정책 분석 (중복성, Shadow 등)", "fpat analyze redundancy --help"),
        ("deletion", "정책 삭제 영향도 분석", "fpat deletion analyze --help"),
        ("completion", "자동완성 설정 방법", "fpat completion"),
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