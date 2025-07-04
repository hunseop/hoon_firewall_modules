"""
방화벽 연동 명령어 모듈
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

try:
    from fpat.firewall_module import FirewallCollectorFactory, export_policy_to_excel
except ImportError:
    # 개발 환경에서는 모듈이 없을 수 있음
    FirewallCollectorFactory = None
    export_policy_to_excel = None

from ..utils.config import Config, FirewallConfig
from ..utils.logger import setup_logger
from ..utils.completion import complete_firewall_names, complete_vendors

console = Console()
logger = setup_logger()

# 서브앱 생성
app = typer.Typer(
    name="firewall",
    help="🛡️ 방화벽 연동 및 데이터 수집 명령어"
)


@app.command()
def collect(
    firewall_name: str = typer.Option(
        ..., "--name", "-n",
        help="방화벽 설정 이름",
        autocompletion=complete_firewall_names
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="출력 파일명 (기본값: 자동 생성)"
    ),
    collect_policies: bool = typer.Option(
        True, "--policies/--no-policies",
        help="보안 정책 수집 여부"
    ),
    collect_objects: bool = typer.Option(
        True, "--objects/--no-objects", 
        help="네트워크 객체 수집 여부"
    )
):
    """방화벽에서 정책과 객체 데이터를 수집합니다."""
    
    if not FirewallCollectorFactory:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다. 먼저 FPAT를 설치하세요.[/red]")
        raise typer.Exit(1)
    
    config = Config()
    firewall_config = config.get_firewall(firewall_name)
    
    if not firewall_config:
        console.print(f"[red]❌ '{firewall_name}' 방화벽 설정을 찾을 수 없습니다.[/red]")
        console.print("[yellow]💡 'fpat firewall add' 명령어로 방화벽을 추가하세요.[/yellow]")
        raise typer.Exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 방화벽 연결
            task1 = progress.add_task("방화벽에 연결 중...", total=None)
            collector = FirewallCollectorFactory.get_collector(
                source_type=firewall_config.vendor,
                hostname=firewall_config.hostname,
                username=firewall_config.username,
                password=firewall_config.password
            )
            progress.update(task1, description="✅ 방화벽 연결 완료")
            
            data = {}
            
            # 정책 수집
            if collect_policies:
                task2 = progress.add_task("보안 정책 수집 중...", total=None)
                data['policies'] = collector.export_security_rules()
                progress.update(task2, description="✅ 보안 정책 수집 완료")
            
            # 객체 수집
            if collect_objects:
                task3 = progress.add_task("네트워크 객체 수집 중...", total=None)
                data['objects'] = collector.export_network_objects()
                progress.update(task3, description="✅ 네트워크 객체 수집 완료")
            
            # Excel 저장
            if not output_file:
                output_file = f"{firewall_name}_collected_data.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task4 = progress.add_task("Excel 파일 저장 중...", total=None)
            
            # 데이터를 Excel로 저장
            export_policy_to_excel(data, str(output_path))
            progress.update(task4, description="✅ Excel 파일 저장 완료")
        
        # 성공 메시지
        success_panel = Panel(
            f"[green]✅ 데이터 수집이 완료되었습니다![/green]\n\n"
            f"[bold]저장 위치:[/bold] {output_path}\n"
            f"[bold]방화벽:[/bold] {firewall_name} ({firewall_config.vendor})\n"
            f"[bold]수집 항목:[/bold] "
            f"{'정책 ' if collect_policies else ''}"
            f"{'객체 ' if collect_objects else ''}",
            title="🎉 수집 완료",
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        logger.error(f"데이터 수집 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add(
    name: str = typer.Option(..., "--name", "-n", help="방화벽 설정 이름"),
    hostname: str = typer.Option(..., "--hostname", "-h", help="방화벽 호스트명 또는 IP"),
    username: str = typer.Option(..., "--username", "-u", help="사용자명"),
    password: str = typer.Option(..., "--password", "-p", help="비밀번호"),
    vendor: str = typer.Option(
        ..., "--vendor", "-v",
        help="방화벽 벤더 (paloalto/ngf/mf2)",
        autocompletion=complete_vendors
    )
):
    """새로운 방화벽 설정을 추가합니다."""
    
    # 벤더 검증
    valid_vendors = ["paloalto", "ngf", "mf2", "mock"]
    if vendor not in valid_vendors:
        console.print(f"[red]❌ 지원하지 않는 벤더입니다. 사용 가능한 벤더: {', '.join(valid_vendors)}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    firewall_config = FirewallConfig(
        hostname=hostname,
        username=username,
        password=password,
        vendor=vendor
    )
    
    config.add_firewall(name, firewall_config)
    
    success_panel = Panel(
        f"[green]✅ 방화벽 설정이 추가되었습니다![/green]\n\n"
        f"[bold]이름:[/bold] {name}\n"
        f"[bold]호스트:[/bold] {hostname}\n"
        f"[bold]벤더:[/bold] {vendor}",
        title="🛡️ 방화벽 추가",
        border_style="green"
    )
    console.print(success_panel)


@app.command()
def list():
    """저장된 방화벽 설정 목록을 표시합니다."""
    
    config = Config()
    firewalls = config.config.firewalls
    
    if not firewalls:
        console.print("[yellow]⚠️ 저장된 방화벽 설정이 없습니다.[/yellow]")
        console.print("[dim]💡 'fpat firewall add' 명령어로 방화벽을 추가하세요.[/dim]")
        return
    
    table = Table(title="🛡️ 저장된 방화벽 설정", border_style="cyan")
    table.add_column("이름", style="bold green")
    table.add_column("호스트", style="cyan")
    table.add_column("사용자명", style="yellow")
    table.add_column("벤더", style="magenta")
    
    for name, fw_config in firewalls.items():
        table.add_row(
            name,
            fw_config.hostname,
            fw_config.username,
            fw_config.vendor
        )
    
    console.print(table)