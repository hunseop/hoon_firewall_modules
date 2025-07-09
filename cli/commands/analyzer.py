"""
정책 분석 명령어 모듈
"""

import typer
from typing import Optional, Dict, Tuple
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import pandas as pd
from datetime import datetime

try:
    from fpat.firewall_analyzer import (
        PolicyAnalyzer, RedundancyAnalyzer, ShadowAnalyzer, 
        PolicyFilter, ChangeAnalyzer, PolicyResolver
    )
except ImportError:
    PolicyAnalyzer = None
    RedundancyAnalyzer = None
    ShadowAnalyzer = None
    PolicyFilter = None
    ChangeAnalyzer = None
    PolicyResolver = None

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

def load_and_resolve_policy(policy_file: Path, vendor: str) -> Tuple[pd.DataFrame, bool]:
    """
    정책 파일을 로드하고 객체 정보가 있다면 resolve합니다.
    
    Args:
        policy_file: 정책 Excel 파일 경로
        vendor: 방화벽 벤더
        
    Returns:
        Tuple[pd.DataFrame, bool]: (resolved된 정책 DataFrame, resolve 성공 여부)
    """
    try:
        # Excel 파일의 시트 목록 확인
        xl = pd.ExcelFile(policy_file)
        sheets = xl.sheet_names
        
        # 정책 데이터 로드
        df = pd.read_excel(policy_file, sheet_name="policy")
        
        # 필요한 객체 시트가 모두 있는지 확인
        required_sheets = {"address", "address_group", "service", "service_group"}
        has_all_sheets = all(sheet in sheets for sheet in required_sheets)
        
        if has_all_sheets:
            try:
                # 객체 데이터 로드
                network_objects = pd.read_excel(policy_file, sheet_name="address")
                network_group_objects = pd.read_excel(policy_file, sheet_name="address_group")
                service_objects = pd.read_excel(policy_file, sheet_name="service")
                service_group_objects = pd.read_excel(policy_file, sheet_name="service_group")
                
                # PolicyResolver를 사용하여 객체 resolve
                resolver = PolicyResolver()
                resolved_df = resolver.resolve(
                    rules_df=df,
                    network_object_df=network_objects,
                    network_group_object_df=network_group_objects,
                    service_object_df=service_objects,
                    service_group_object_df=service_group_objects
                )
                
                console.print("[green]✅ 객체 정보를 성공적으로 resolve했습니다.[/green]")
                return resolved_df, True
                
            except Exception as e:
                logger.warning(f"객체 resolve 중 오류 발생: {e}")
                console.print("[yellow]⚠️ 객체 resolve에 실패하여 객체명 기반으로 분석을 진행합니다.[/yellow]")
                return df, False
        else:
            console.print("[yellow]⚠️ 일부 객체 정보가 없어 객체명 기반으로 분석을 진행합니다.[/yellow]")
            return df, False
            
    except Exception as e:
        logger.error(f"정책 파일 로드 중 오류 발생: {e}")
        raise typer.Exit(1)


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
            
            # 파일 로딩 및 객체 resolve
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            df, is_resolved = load_and_resolve_policy(Path(policy_file), vendor)
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # 중복성 분석
            task2 = progress.add_task("중복성 분석 중...", total=None)
            analyzer = RedundancyAnalyzer()
            
            # Resolved 컬럼이 있는 경우 해당 컬럼 사용
            if is_resolved:
                analyzer.extracted_columns[vendor] = [
                    col.replace('Source', 'Extracted Source')
                       .replace('Destination', 'Extracted Destination')
                       .replace('Service', 'Extracted Service')
                    for col in analyzer.vendor_columns[vendor]
                ]
            
            results = analyzer.analyze(df, vendor=vendor)
            progress.update(task2, description="✅ 중복성 분석 완료")
            
            # 결과 저장
            if not output_file:
                today = datetime.now().strftime("%Y-%m-%d")
                output_file = f"{today}_redundancy_analysis_{vendor}.xlsx"
            
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
            
            # 파일 로딩 및 객체 resolve
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            df, is_resolved = load_and_resolve_policy(Path(policy_file), vendor)
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # Shadow 분석
            task2 = progress.add_task("Shadow 정책 분석 중...", total=None)
            analyzer = ShadowAnalyzer()
            
            # Resolved 컬럼이 있는 경우 해당 컬럼 사용
            if is_resolved:
                analyzer.vendor_columns[vendor] = [
                    col.replace('Source', 'Extracted Source')
                       .replace('Destination', 'Extracted Destination')
                       .replace('Service', 'Extracted Service')
                    for col in analyzer.vendor_columns[vendor]
                ]
            
            results = analyzer.analyze(df, vendor=vendor)
            progress.update(task2, description="✅ Shadow 분석 완료")
            
            # 결과 저장
            if not output_file:
                today = datetime.now().strftime("%Y-%m-%d")
                output_file = f"{today}_shadow_analysis_{vendor}.xlsx"
            
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
            
            # 파일 로딩 및 객체 resolve
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            df, is_resolved = load_and_resolve_policy(Path(policy_file), "paloalto")  # 벤더는 필터링에 영향 없음
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # 필터링
            task2 = progress.add_task("정책 필터링 중...", total=None)
            filter_obj = PolicyFilter()
            
            # Resolved 컬럼 사용 여부 설정
            use_extracted = is_resolved
            
            if search_type == "source":
                filtered_df = filter_obj.filter_by_source(df, search_address, include_any, use_extracted)
            elif search_type == "destination":
                filtered_df = filter_obj.filter_by_destination(df, search_address, include_any, use_extracted)
            else:  # both
                filtered_df = filter_obj.filter_by_both(df, search_address, include_any, use_extracted)
            
            progress.update(task2, description="✅ 정책 필터링 완료")
            
            # 필터링 요약
            summary = filter_obj.get_filter_summary(
                original_df=df,
                filtered_df=filtered_df,
                search_criteria={
                    'search_type': search_type,
                    'address': search_address,
                    'include_any': include_any,
                    'use_extracted': use_extracted
                }
            )
            
            # 결과 저장
            if not output_file:
                today = datetime.now().strftime("%Y-%m-%d")
                safe_address = search_address.replace('/', '_').replace('-', '_')
                output_file = f"{today}_filtered_policies_{search_type}_{safe_address}.xlsx"
            
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
    
    has_data = False
    for sheet_name, data in results.items():
        if isinstance(data, pd.DataFrame):
            table.add_row(sheet_name, str(len(data)))
            if len(data) > 0:
                has_data = True
        elif isinstance(data, (list, dict)):
            table.add_row(sheet_name, str(len(data)))
            if len(data) > 0:
                has_data = True
    
    console.print(table)
    
    # 분석 결과가 없는 경우 메시지 표시
    if not has_data:
        no_result_panel = Panel(
            f"[yellow]ℹ️ {analysis_type} 결과가 없습니다.[/yellow]\n\n"
            f"[bold]저장 위치:[/bold] {output_path}\n"
            f"[dim]분석 조건에 맞는 정책이 발견되지 않았습니다.[/dim]",
            title="📋 분석 결과",
            border_style="yellow"
        )
        console.print(no_result_panel)
    else:
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


# Interactive 모드용 헬퍼 함수들
def execute_redundancy_analysis(policy_file: str, vendor: str = "paloalto", output_file: Optional[str] = None):
    """Interactive 모드용 중복성 분석 함수"""
    
    if not RedundancyAnalyzer:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        return False
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        return False
    
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
                today = datetime.now().strftime("%Y-%m-%d")
                final_output_file = f"{today}_redundancy_analysis_{vendor}.xlsx"
            else:
                final_output_file = output_file
            output_path = Path(config.get_output_dir()) / final_output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
                for sheet_name, data in results.items():
                    if isinstance(data, pd.DataFrame):
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_analysis_summary(results, output_path, "중복성 분석")
        return True
        
    except Exception as e:
        logger.error(f"중복성 분석 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        return False


def execute_shadow_analysis(policy_file: str, vendor: str = "paloalto", output_file: Optional[str] = None):
    """Interactive 모드용 Shadow 분석 함수"""
    
    if not ShadowAnalyzer:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        return False
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        return False
    
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
                today = datetime.now().strftime("%Y-%m-%d")
                final_output_file = f"{today}_shadow_analysis_{vendor}.xlsx"
            else:
                final_output_file = output_file
            output_path = Path(config.get_output_dir()) / final_output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
                for sheet_name, data in results.items():
                    if isinstance(data, pd.DataFrame):
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_analysis_summary(results, output_path, "Shadow 분석")
        return True
        
    except Exception as e:
        logger.error(f"Shadow 분석 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        return False


def execute_policy_filter(policy_file: str, search_address: str, search_type: str = "both", 
                         include_any: bool = True, output_file: Optional[str] = None):
    """Interactive 모드용 정책 필터링 함수"""
    
    if not PolicyFilter:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        return False
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        return False
    
    valid_types = ["source", "destination", "both"]
    if search_type not in valid_types:
        console.print(f"[red]❌ 잘못된 검색 유형입니다. 사용 가능한 유형: {', '.join(valid_types)}[/red]")
        return False
    
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
                today = datetime.now().strftime("%Y-%m-%d")
                safe_address = search_address.replace('/', '_').replace('-', '_')
                output_file = f"{today}_filtered_policies_{search_type}_{safe_address}.xlsx"
            
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
        return True
        
    except Exception as e:
        logger.error(f"정책 필터링 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        return False