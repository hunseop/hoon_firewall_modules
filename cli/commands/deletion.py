"""
정책 삭제 영향도 분석 명령어 모듈
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
    from fpat.policy_deletion_processor.core import config_manager
    from fpat.policy_deletion_processor.processors import policy_usage_processor
    from fpat.policy_deletion_processor.utils import excel_manager
except ImportError:
    config_manager = None
    policy_usage_processor = None
    excel_manager = None

from ..utils.config import Config
from ..utils.logger import setup_logger
from ..utils.completion import complete_file_extensions

console = Console()
logger = setup_logger()

# 서브앱 생성
app = typer.Typer(
    name="deletion",
    help="🗑️ 정책 삭제 영향도 분석 명령어"
)


@app.command()
def analyze(
    policy_file: str = typer.Option(
        ..., "--file", "-f",
        help="분석할 정책 Excel 파일 경로",
        autocompletion=complete_file_extensions
    ),
    policy_names: str = typer.Option(
        ..., "--policies", "-p",
        help="삭제할 정책명 (쉼표로 구분)"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """정책 삭제 영향도를 분석합니다."""
    
    if not policy_usage_processor:
        console.print("[red]❌ FPAT 삭제 프로세서 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    policy_list = [name.strip() for name in policy_names.split(',')]
    
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
            
            # 삭제 영향도 분석
            task2 = progress.add_task("삭제 영향도 분석 중...", total=None)
            results = policy_usage_processor.analyze_deletion_impact(df, policy_list)
            progress.update(task2, description="✅ 삭제 영향도 분석 완료")
            
            # 결과 저장
            if not output_file:
                output_file = "deletion_impact_analysis.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            excel_manager.save_deletion_results(results, str(output_path))
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_deletion_summary(results, output_path, policy_list)
        
    except Exception as e:
        logger.error(f"삭제 영향도 분석 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


def show_deletion_summary(results: dict, output_path: Path, policy_list: list):
    """삭제 영향도 분석 결과 요약을 표시합니다."""
    
    # 정책 목록 표시
    policy_table = Table(title="🗑️ 삭제 대상 정책", border_style="red")
    policy_table.add_column("번호", style="dim")
    policy_table.add_column("정책명", style="bold red")
    
    for i, policy_name in enumerate(policy_list, 1):
        policy_table.add_row(str(i), policy_name)
    
    console.print(policy_table)
    
    # 영향도 결과 표시
    impact_table = Table(title="📊 영향도 분석 결과", border_style="yellow")
    impact_table.add_column("항목", style="bold yellow")
    impact_table.add_column("수량", style="green")
    impact_table.add_column("설명", style="white")
    
    if isinstance(results, dict):
        for key, value in results.items():
            if isinstance(value, (list, pd.DataFrame)):
                count = len(value)
                description = get_impact_description(key)
                impact_table.add_row(key, str(count), description)
    
    console.print(impact_table)
    
    # 성공 메시지
    success_panel = Panel(
        f"[green]✅ 삭제 영향도 분석이 완료되었습니다![/green]\n\n"
        f"[bold]저장 위치:[/bold] {output_path}\n"
        f"[bold]분석 정책 수:[/bold] {len(policy_list)}개",
        title="🎉 분석 완료",
        border_style="green"
    )
    console.print(success_panel)


def get_impact_description(key: str) -> str:
    """영향도 항목별 설명을 반환합니다."""
    descriptions = {
        "dependent_policies": "의존성 있는 정책",
        "affected_objects": "영향받는 객체",
        "usage_analysis": "사용량 분석",
        "risk_assessment": "위험도 평가",
        "recommendations": "권장사항"
    }
    return descriptions.get(key, "분석 결과")


# Interactive 모드용 헬퍼 함수들
def execute_deletion_analysis(policy_file: str, policy_names: str, output_file: Optional[str] = None):
    """Interactive 모드용 삭제 영향도 분석 함수"""
    
    if not policy_usage_processor:
        console.print("[red]❌ FPAT 삭제 프로세서 모듈을 찾을 수 없습니다.[/red]")
        return False
    
    if not Path(policy_file).exists():
        console.print(f"[red]❌ 정책 파일을 찾을 수 없습니다: {policy_file}[/red]")
        return False
    
    config = Config()
    policy_list = [name.strip() for name in policy_names.split(',')]
    
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
            
            # 삭제 영향도 분석
            task2 = progress.add_task("삭제 영향도 분석 중...", total=None)
            results = policy_usage_processor.analyze_deletion_impact(df, policy_list)
            progress.update(task2, description="✅ 삭제 영향도 분석 완료")
            
            # 결과 저장
            final_output_file = output_file or "deletion_impact_analysis.xlsx"
            output_path = Path(config.get_output_dir()) / final_output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            
            excel_manager.save_deletion_results(results, str(output_path))
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_deletion_summary(results, output_path, policy_list)
        return True
        
    except Exception as e:
        logger.error(f"삭제 영향도 분석 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        return False