"""
정책 분석 명령어 모듈
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import pandas as pd

try:
    from fpat.firewall_analyzer import (
        PolicyAnalyzer, RedundancyAnalyzer, ShadowAnalyzer, 
        PolicyFilter, ChangeAnalyzer
    )
except ImportError:
    PolicyAnalyzer = None
    RedundancyAnalyzer = None
    ShadowAnalyzer = None
    PolicyFilter = None
    ChangeAnalyzer = None

from ..utils.config import Config
from ..utils.logger import setup_logger
from ..utils.completion import complete_vendors, complete_search_types, complete_file_extensions

console = Console()
logger = setup_logger()

# 서브앱 생성
app = typer.Typer(
    name="analyze",
    help="📊 정책 분석 명령어 (중복성, Shadow, 필터링 등)"
)


@app.command()
def redundancy(
    policy_file: str = typer.Option(
        ..., "--file", "-f",
        help="분석할 정책 Excel 파일 경로",
        autocompletion=complete_file_extensions
    ),
    vendor: str = typer.Option(
        "paloalto", "--vendor", "-v",
        help="방화벽 벤더 (paloalto/ngf/mf2)",
        autocompletion=complete_vendors
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """정책 중복성을 분석합니다."""
    
    if not RedundancyAnalyzer:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 파일 로딩
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            df = pd.read_excel(policy_file)
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # 중복성 분석
            task2 = progress.add_task("중복성 분석 중...", total=None)
            analyzer = RedundancyAnalyzer()
            results = analyzer.analyze(df, vendor=vendor)
            progress.update(task2, description="✅ 중복성 분석 완료")
            
            # 결과 저장
            if not output_file:
                output_file = f"redundancy_analysis_{vendor}.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
                for sheet_name, data in results.items():
                    if isinstance(data, pd.DataFrame):
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_analysis_summary(results, output_path, "중복성 분석")
        
    except Exception as e:
        logger.error(f"중복성 분석 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def shadow(
    policy_file: str = typer.Option(
        ..., "--file", "-f",
        help="분석할 정책 Excel 파일 경로",
        autocompletion=complete_file_extensions
    ),
    vendor: str = typer.Option(
        "paloalto", "--vendor", "-v", 
        help="방화벽 벤더 (paloalto/ngf/mf2)",
        autocompletion=complete_vendors
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """Shadow 정책을 분석합니다."""
    
    if not ShadowAnalyzer:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 파일 로딩
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            df = pd.read_excel(policy_file)
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # Shadow 분석
            task2 = progress.add_task("Shadow 정책 분석 중...", total=None)
            analyzer = ShadowAnalyzer()
            results = analyzer.analyze(df, vendor=vendor)
            progress.update(task2, description="✅ Shadow 분석 완료")
            
            # 결과 저장
            if not output_file:
                output_file = f"shadow_analysis_{vendor}.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
                for sheet_name, data in results.items():
                    if isinstance(data, pd.DataFrame):
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_analysis_summary(results, output_path, "Shadow 분석")
        
    except Exception as e:
        logger.error(f"Shadow 분석 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def filter(
    policy_file: str = typer.Option(
        ..., "--file", "-f",
        help="필터링할 정책 Excel 파일 경로",
        autocompletion=complete_file_extensions
    ),
    search_address: str = typer.Option(
        ..., "--address", "-a",
        help="검색할 IP 주소 (단일 IP, CIDR, 범위)"
    ),
    search_type: str = typer.Option(
        "both", "--type", "-t",
        help="검색 유형 (source/destination/both)",
        autocompletion=complete_search_types
    ),
    include_any: bool = typer.Option(
        True, "--include-any/--exclude-any",
        help="any 정책 포함 여부"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """IP 주소 기반으로 정책을 필터링합니다."""
    
    if not PolicyFilter:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        raise typer.Exit(1)
    
    valid_types = ["source", "destination", "both"]
    if search_type not in valid_types:
        console.print(f"[red]❌ 잘못된 검색 유형입니다. 사용 가능한 유형: {', '.join(valid_types)}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 파일 로딩
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            df = pd.read_excel(policy_file)
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # 필터링
            task2 = progress.add_task("정책 필터링 중...", total=None)
            filter_obj = PolicyFilter()
            
            if search_type == "source":
                filtered_df = filter_obj.filter_by_source(df, search_address, include_any)
            elif search_type == "destination":
                filtered_df = filter_obj.filter_by_destination(df, search_address, include_any)
            else:  # both
                filtered_df = filter_obj.filter_by_both(df, search_address, include_any)
            
            progress.update(task2, description="✅ 정책 필터링 완료")
            
            # 필터링 요약
            summary = filter_obj.get_filter_summary(
                original_df=df,
                filtered_df=filtered_df,
                search_criteria={
                    'search_type': search_type,
                    'address': search_address,
                    'include_any': include_any
                }
            )
            
            # 결과 저장
            if not output_file:
                safe_address = search_address.replace('/', '_').replace('-', '_')
                output_file = f"filtered_policies_{search_type}_{safe_address}.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
                filtered_df.to_excel(writer, sheet_name="filtered_policies", index=False)
                
                # 요약 정보도 저장
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name="summary", index=False)
            
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_filter_summary(summary, output_path)
        
    except Exception as e:
        logger.error(f"정책 필터링 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


def show_analysis_summary(results: dict, output_path: Path, analysis_type: str):
    """분석 결과 요약을 표시합니다."""
    
    # 결과 테이블 생성
    table = Table(title=f"📊 {analysis_type} 결과 요약", border_style="cyan")
    table.add_column("카테고리", style="bold yellow")
    table.add_column("항목 수", style="green")
    
    for sheet_name, data in results.items():
        if isinstance(data, pd.DataFrame):
            table.add_row(sheet_name, str(len(data)))
        elif isinstance(data, (list, dict)):
            table.add_row(sheet_name, str(len(data)))
    
    console.print(table)
    
    # 성공 메시지
    success_panel = Panel(
        f"[green]✅ {analysis_type}이 완료되었습니다![/green]\n\n"
        f"[bold]저장 위치:[/bold] {output_path}",
        title="🎉 분석 완료",
        border_style="green"
    )
    console.print(success_panel)


def show_filter_summary(summary: dict, output_path: Path):
    """필터링 결과 요약을 표시합니다."""
    
    # 결과 테이블 생성
    table = Table(title="🔍 필터링 결과 요약", border_style="cyan")
    table.add_column("항목", style="bold yellow")
    table.add_column("값", style="green")
    
    table.add_row("전체 정책 수", str(summary.get('total_policies', 0)))
    table.add_row("매치된 정책 수", str(summary.get('matched_policies', 0)))
    table.add_row("매치 비율", f"{summary.get('match_percentage', 0):.1f}%")
    
    console.print(table)
    
    # 성공 메시지
    success_panel = Panel(
        f"[green]✅ 정책 필터링이 완료되었습니다![/green]\n\n"
        f"[bold]저장 위치:[/bold] {output_path}\n"
        f"[bold]검색 조건:[/bold] {summary.get('search_criteria', {})}",
        title="🎉 필터링 완료",
        border_style="green"
    )
    console.print(success_panel)