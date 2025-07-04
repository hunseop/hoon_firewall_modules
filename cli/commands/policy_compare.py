"""
정책 비교 명령어 모듈
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

try:
    from fpat.policy_comparator import PolicyComparator, save_results_to_excel
except ImportError:
    PolicyComparator = None
    save_results_to_excel = None

from ..utils.config import Config
from ..utils.logger import setup_logger

console = Console()
logger = setup_logger()

# 서브앱 생성
app = typer.Typer(
    name="compare",
    help="🔍 정책 및 객체 비교 분석 명령어"
)


@app.command()
def policies(
    old_policy: str = typer.Option(
        ..., "--old", "-o",
        help="이전 정책 Excel 파일 경로"
    ),
    new_policy: str = typer.Option(
        ..., "--new", "-n", 
        help="새로운 정책 Excel 파일 경로"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-out",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """정책 변경사항을 비교 분석합니다."""
    
    if not PolicyComparator:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    # 파일 존재 확인
    if not Path(old_policy).exists():
        console.print(f"[red]❌ 이전 정책 파일을 찾을 수 없습니다: {old_policy}[/red]")
        raise typer.Exit(1)
    
    if not Path(new_policy).exists():
        console.print(f"[red]❌ 새로운 정책 파일을 찾을 수 없습니다: {new_policy}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 비교기 초기화
            task1 = progress.add_task("정책 파일 로딩 중...", total=None)
            comparator = PolicyComparator(
                policy_old=old_policy,
                policy_new=new_policy
            )
            progress.update(task1, description="✅ 정책 파일 로딩 완료")
            
            # 정책 비교
            task2 = progress.add_task("정책 변경사항 분석 중...", total=None)
            results = comparator.compare_policies()
            progress.update(task2, description="✅ 정책 비교 완료")
            
            # 결과 저장
            if not output_file:
                output_file = "policy_comparison_result.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            save_results_to_excel(results, str(output_path))
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_comparison_summary(results, output_path)
        
    except Exception as e:
        logger.error(f"정책 비교 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def objects(
    old_objects: str = typer.Option(
        ..., "--old", "-o",
        help="이전 객체 Excel 파일 경로"
    ),
    new_objects: str = typer.Option(
        ..., "--new", "-n",
        help="새로운 객체 Excel 파일 경로"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-out",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """네트워크 객체 변경사항을 비교 분석합니다."""
    
    if not PolicyComparator:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    # 파일 존재 확인
    if not Path(old_objects).exists():
        console.print(f"[red]❌ 이전 객체 파일을 찾을 수 없습니다: {old_objects}[/red]")
        raise typer.Exit(1)
    
    if not Path(new_objects).exists():
        console.print(f"[red]❌ 새로운 객체 파일을 찾을 수 없습니다: {new_objects}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 비교기 초기화
            task1 = progress.add_task("객체 파일 로딩 중...", total=None)
            comparator = PolicyComparator(
                object_old=old_objects,
                object_new=new_objects
            )
            progress.update(task1, description="✅ 객체 파일 로딩 완료")
            
            # 객체 비교
            task2 = progress.add_task("객체 변경사항 분석 중...", total=None)
            results = comparator.compare_all_objects()
            progress.update(task2, description="✅ 객체 비교 완료")
            
            # 결과 저장
            if not output_file:
                output_file = "object_comparison_result.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task3 = progress.add_task("결과 Excel 저장 중...", total=None)
            save_results_to_excel(results, str(output_path))
            progress.update(task3, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_comparison_summary(results, output_path)
        
    except Exception as e:
        logger.error(f"객체 비교 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def full(
    old_policy: str = typer.Option(
        ..., "--old-policy", "-op",
        help="이전 정책 Excel 파일 경로"
    ),
    new_policy: str = typer.Option(
        ..., "--new-policy", "-np",
        help="새로운 정책 Excel 파일 경로"
    ),
    old_objects: str = typer.Option(
        ..., "--old-objects", "-oo",
        help="이전 객체 Excel 파일 경로"
    ),
    new_objects: str = typer.Option(
        ..., "--new-objects", "-no",
        help="새로운 객체 Excel 파일 경로"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-out",
        help="결과 파일명 (기본값: 자동 생성)"
    )
):
    """정책과 객체를 모두 비교 분석합니다."""
    
    if not PolicyComparator:
        console.print("[red]❌ FPAT 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)
    
    # 파일 존재 확인
    files_to_check = [
        (old_policy, "이전 정책"),
        (new_policy, "새로운 정책"), 
        (old_objects, "이전 객체"),
        (new_objects, "새로운 객체")
    ]
    
    for file_path, file_desc in files_to_check:
        if not Path(file_path).exists():
            console.print(f"[red]❌ {file_desc} 파일을 찾을 수 없습니다: {file_path}[/red]")
            raise typer.Exit(1)
    
    config = Config()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 비교기 초기화
            task1 = progress.add_task("모든 파일 로딩 중...", total=None)
            comparator = PolicyComparator(
                policy_old=old_policy,
                policy_new=new_policy,
                object_old=old_objects,
                object_new=new_objects
            )
            progress.update(task1, description="✅ 모든 파일 로딩 완료")
            
            # 전체 비교
            task2 = progress.add_task("정책 변경사항 분석 중...", total=None)
            policy_results = comparator.compare_policies()
            progress.update(task2, description="✅ 정책 비교 완료")
            
            task3 = progress.add_task("객체 변경사항 분석 중...", total=None)
            object_results = comparator.compare_all_objects()
            progress.update(task3, description="✅ 객체 비교 완료")
            
            # 결과 병합
            all_results = {**policy_results, **object_results}
            
            # 결과 저장
            if not output_file:
                output_file = "full_comparison_result.xlsx"
            
            output_path = Path(config.get_output_dir()) / output_file
            task4 = progress.add_task("결과 Excel 저장 중...", total=None)
            save_results_to_excel(all_results, str(output_path))
            progress.update(task4, description="✅ 결과 저장 완료")
        
        # 결과 요약 표시
        show_comparison_summary(all_results, output_path)
        
    except Exception as e:
        logger.error(f"전체 비교 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


def show_comparison_summary(results: dict, output_path: Path):
    """비교 결과 요약을 표시합니다."""
    
    # 결과 테이블 생성
    table = Table(title="📊 비교 결과 요약", border_style="cyan")
    table.add_column("카테고리", style="bold yellow")
    table.add_column("항목 수", style="green")
    table.add_column("설명", style="white")
    
    for sheet_name, df in results.items():
        if hasattr(df, '__len__'):
            table.add_row(
                sheet_name,
                str(len(df)),
                get_sheet_description(sheet_name)
            )
    
    console.print(table)
    
    # 성공 메시지
    success_panel = Panel(
        f"[green]✅ 비교 분석이 완료되었습니다![/green]\n\n"
        f"[bold]저장 위치:[/bold] {output_path}",
        title="🎉 분석 완료",
        border_style="green"
    )
    console.print(success_panel)


def get_sheet_description(sheet_name: str) -> str:
    """시트명에 따른 설명을 반환합니다."""
    descriptions = {
        "added": "새로 추가된 항목",
        "deleted": "삭제된 항목", 
        "modified": "수정된 항목",
        "unchanged": "변경되지 않은 항목",
        "policies_added": "새로 추가된 정책",
        "policies_deleted": "삭제된 정책",
        "policies_modified": "수정된 정책",
        "objects_added": "새로 추가된 객체",
        "objects_deleted": "삭제된 객체",
        "objects_modified": "수정된 객체"
    }
    return descriptions.get(sheet_name, "분석 결과")