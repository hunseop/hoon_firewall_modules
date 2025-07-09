"""
정책 삭제 프로세서 CLI 명령어 모듈
"""

import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

try:
    from fpat.policy_deletion_processor.core.config_manager import ConfigManager
    from fpat.policy_deletion_processor.utils.file_manager import FileManager
    from fpat.policy_deletion_processor.utils.excel_manager import ExcelManager
    from fpat.policy_deletion_processor.processors import (
        RequestParser, RequestExtractor, MisIdAdder, ApplicationAggregator,
        RequestInfoAdder, ExceptionHandler, DuplicatePolicyClassifier,
        MergeHitcount, PolicyUsageProcessor, NotificationClassifier
    )
    FPAT_AVAILABLE = True
except ImportError:
    FPAT_AVAILABLE = False
    ConfigManager = None
    FileManager = None
    ExcelManager = None

from ..utils.config import Config
from ..utils.logger import setup_logger
from ..utils.completion import complete_file_extensions

console = Console()
logger = setup_logger()

# 서브앱 생성
app = typer.Typer(
    name="deletion",
    help="🗑️ 정책 삭제 프로세서 명령어"
)


def check_fpat_availability():
    """FPAT 모듈 가용성 확인"""
    if not FPAT_AVAILABLE:
        console.print("[red]❌ FPAT 삭제 프로세서 모듈을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)


def create_processors():
    """프로세서 인스턴스들을 생성"""
    if not FPAT_AVAILABLE:
        raise RuntimeError("FPAT 모듈을 사용할 수 없습니다")
    
    config_manager = ConfigManager()
    file_manager = FileManager(config_manager)
    excel_manager = ExcelManager(config_manager)
    
    processors = {
        'request_parser': RequestParser(config_manager),
        'request_extractor': RequestExtractor(config_manager),
        'mis_id_adder': MisIdAdder(config_manager),
        'application_aggregator': ApplicationAggregator(config_manager),
        'request_info_adder': RequestInfoAdder(config_manager),
        'exception_handler': ExceptionHandler(config_manager),
        'duplicate_policy_classifier': DuplicatePolicyClassifier(config_manager),
        'merge_hitcount': MergeHitcount(config_manager),
        'policy_usage_processor': PolicyUsageProcessor(config_manager),
        'notification_classifier': NotificationClassifier(config_manager)
    }
    
    return processors, file_manager, excel_manager


@app.command()
def parse_request(
    file_path: Optional[str] = typer.Option(
        None, "--file", "-f",
        help="정책 파일 경로",
        autocompletion=complete_file_extensions
    )
):
    """신청 정보를 파싱합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("신청 정보 파싱 중...", total=None)
            
            success = processors['request_parser'].parse_request_type(file_manager)
            
            if success:
                progress.update(task, description="✅ 신청 정보 파싱 완료")
                console.print("[green]✅ 신청 정보 파싱이 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 신청 정보 파싱 실패")
                console.print("[red]❌ 신청 정보 파싱에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"신청 정보 파싱 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def extract_request():
    """신청 ID를 추출합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("신청 ID 추출 중...", total=None)
            
            success = processors['request_extractor'].extract_request_id(file_manager)
            
            if success:
                progress.update(task, description="✅ 신청 ID 추출 완료")
                console.print("[green]✅ 신청 ID 추출이 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 신청 ID 추출 실패")
                console.print("[red]❌ 신청 ID 추출에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"신청 ID 추출 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_mis_id():
    """MIS ID를 추가합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("MIS ID 추가 중...", total=None)
            
            success = processors['mis_id_adder'].add_mis_id(file_manager)
            
            if success:
                progress.update(task, description="✅ MIS ID 추가 완료")
                console.print("[green]✅ MIS ID 추가가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ MIS ID 추가 실패")
                console.print("[red]❌ MIS ID 추가에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"MIS ID 추가 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def collect_applications():
    """신청 정보를 취합합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("신청 정보 취합 중...", total=None)
            
            success = processors['application_aggregator'].collect_applications(file_manager)
            
            if success:
                progress.update(task, description="✅ 신청 정보 취합 완료")
                console.print("[green]✅ 신청 정보 취합이 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 신청 정보 취합 실패")
                console.print("[red]❌ 신청 정보 취합에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"신청 정보 취합 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_request_info():
    """신청 정보를 추가합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("신청 정보 추가 중...", total=None)
            
            success = processors['request_info_adder'].add_request_info(file_manager)
            
            if success:
                progress.update(task, description="✅ 신청 정보 추가 완료")
                console.print("[green]✅ 신청 정보 추가가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 신청 정보 추가 실패")
                console.print("[red]❌ 신청 정보 추가에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"신청 정보 추가 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def handle_exception(
    vendor: str = typer.Option(
        "paloalto", "--vendor", "-v",
        help="방화벽 벤더 (paloalto, secui)"
    )
):
    """예외처리를 수행합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"{vendor} 예외처리 중...", total=None)
            
            if vendor.lower() == "paloalto":
                success = processors['exception_handler'].paloalto_exception(file_manager)
            elif vendor.lower() == "secui":
                success = processors['exception_handler'].secui_exception(file_manager)
            else:
                console.print(f"[red]❌ 지원하지 않는 벤더입니다: {vendor}[/red]")
                raise typer.Exit(1)
            
            if success:
                progress.update(task, description="✅ 예외처리 완료")
                console.print("[green]✅ 예외처리가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 예외처리 실패")
                console.print("[red]❌ 예외처리에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"예외처리 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def classify_duplicates():
    """중복정책을 분류합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("중복정책 분류 중...", total=None)
            
            success = processors['duplicate_policy_classifier'].organize_redundant_file(file_manager)
            
            if success:
                progress.update(task, description="✅ 중복정책 분류 완료")
                console.print("[green]✅ 중복정책 분류가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 중복정책 분류 실패")
                console.print("[red]❌ 중복정책 분류에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"중복정책 분류 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_duplicate_status():
    """중복정책 상태를 추가합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("중복정책 상태 추가 중...", total=None)
            
            success = processors['duplicate_policy_classifier'].add_duplicate_status(file_manager)
            
            if success:
                progress.update(task, description="✅ 중복정책 상태 추가 완료")
                console.print("[green]✅ 중복정책 상태 추가가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 중복정책 상태 추가 실패")
                console.print("[red]❌ 중복정책 상태 추가에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"중복정책 상태 추가 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def merge_hitcount():
    """히트카운트를 병합합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("히트카운트 병합 중...", total=None)
            
            success = processors['merge_hitcount'].mergehitcounts(file_manager)
            
            if success:
                progress.update(task, description="✅ 히트카운트 병합 완료")
                console.print("[green]✅ 히트카운트 병합이 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 히트카운트 병합 실패")
                console.print("[red]❌ 히트카운트 병합에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"히트카운트 병합 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add_usage_status():
    """미사용 정책 정보를 추가합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("미사용 정책 정보 추가 중...", total=None)
            
            success = processors['policy_usage_processor'].add_usage_status(file_manager)
            
            if success:
                progress.update(task, description="✅ 미사용 정책 정보 추가 완료")
                console.print("[green]✅ 미사용 정책 정보 추가가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 미사용 정책 정보 추가 실패")
                console.print("[red]❌ 미사용 정책 정보 추가에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"미사용 정책 정보 추가 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update_excepted_usage():
    """미사용 예외 정책을 업데이트합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("미사용 예외 정책 업데이트 중...", total=None)
            
            success = processors['policy_usage_processor'].update_excepted_usage(file_manager)
            
            if success:
                progress.update(task, description="✅ 미사용 예외 정책 업데이트 완료")
                console.print("[green]✅ 미사용 예외 정책 업데이트가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 미사용 예외 정책 업데이트 실패")
                console.print("[red]❌ 미사용 예외 정책 업데이트에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"미사용 예외 정책 업데이트 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def classify_notifications():
    """공지파일을 분류합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("공지파일 분류 중...", total=None)
            
            success = processors['notification_classifier'].classify_notifications(file_manager, excel_manager)
            
            if success:
                progress.update(task, description="✅ 공지파일 분류 완료")
                console.print("[green]✅ 공지파일 분류가 완료되었습니다.[/green]")
            else:
                progress.update(task, description="❌ 공지파일 분류 실패")
                console.print("[red]❌ 공지파일 분류에 실패했습니다.[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        logger.error(f"공지파일 분류 중 오류 발생: {e}")
        console.print(f"[red]❌ 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def run_full_process(
    vendor: str = typer.Option(
        "paloalto", "--vendor", "-v",
        help="방화벽 벤더 (paloalto, secui)"
    ),
    skip_steps: List[str] = typer.Option(
        [], "--skip", "-s",
        help="건너뛸 단계들 (예: parse_request,extract_request)"
    )
):
    """전체 프로세스를 순차적으로 실행합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    # 전체 프로세스 단계 정의
    steps = [
        ("parse_request", "신청 정보 파싱", lambda: processors['request_parser'].parse_request_type(file_manager)),
        ("extract_request", "신청 ID 추출", lambda: processors['request_extractor'].extract_request_id(file_manager)),
        ("add_mis_id", "MIS ID 추가", lambda: processors['mis_id_adder'].add_mis_id(file_manager)),
        ("collect_applications", "신청 정보 취합", lambda: processors['application_aggregator'].collect_applications(file_manager)),
        ("add_request_info", "신청 정보 추가", lambda: processors['request_info_adder'].add_request_info(file_manager)),
        ("handle_exception", f"{vendor} 예외처리", lambda: processors['exception_handler'].paloalto_exception(file_manager) if vendor.lower() == "paloalto" else processors['exception_handler'].secui_exception(file_manager)),
        ("classify_duplicates", "중복정책 분류", lambda: processors['duplicate_policy_classifier'].organize_redundant_file(file_manager)),
        ("add_duplicate_status", "중복정책 상태 추가", lambda: processors['duplicate_policy_classifier'].add_duplicate_status(file_manager)),
        ("merge_hitcount", "히트카운트 병합", lambda: processors['merge_hitcount'].mergehitcounts(file_manager)),
        ("add_usage_status", "미사용 정책 정보 추가", lambda: processors['policy_usage_processor'].add_usage_status(file_manager)),
        ("update_excepted_usage", "미사용 예외 정책 업데이트", lambda: processors['policy_usage_processor'].update_excepted_usage(file_manager)),
        ("classify_notifications", "공지파일 분류", lambda: processors['notification_classifier'].classify_notifications(file_manager, excel_manager))
    ]
    
    # 건너뛸 단계들 제외
    if skip_steps:
        steps = [step for step in steps if step[0] not in skip_steps]
    
    console.print(f"\n[bold blue]🚀 정책 삭제 프로세스 전체 실행 ({vendor})[/bold blue]")
    console.print(f"[dim]총 {len(steps)}개 단계를 실행합니다.[/dim]\n")
    
    failed_steps = []
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            main_task = progress.add_task("전체 프로세스 진행", total=len(steps))
            
            for i, (step_name, step_desc, step_func) in enumerate(steps, 1):
                current_task = progress.add_task(f"{step_desc} 중...", total=None)
                
                try:
                    success = step_func()
                    
                    if success:
                        progress.update(current_task, description=f"✅ {step_desc} 완료")
                        console.print(f"[green]✅ {i}/{len(steps)} {step_desc} 완료[/green]")
                    else:
                        progress.update(current_task, description=f"❌ {step_desc} 실패")
                        console.print(f"[red]❌ {i}/{len(steps)} {step_desc} 실패[/red]")
                        failed_steps.append((step_name, step_desc))
                        
                except Exception as e:
                    progress.update(current_task, description=f"❌ {step_desc} 오류")
                    console.print(f"[red]❌ {i}/{len(steps)} {step_desc} 오류: {e}[/red]")
                    failed_steps.append((step_name, step_desc))
                    logger.error(f"{step_desc} 중 오류 발생: {e}")
                
                progress.update(main_task, advance=1)
                progress.remove_task(current_task)
        
        # 결과 요약
        console.print("\n" + "="*50)
        if failed_steps:
            console.print(f"[yellow]⚠️  일부 단계에서 오류가 발생했습니다.[/yellow]")
            console.print(f"[green]성공: {len(steps) - len(failed_steps)}/{len(steps)} 단계[/green]")
            console.print(f"[red]실패: {len(failed_steps)}/{len(steps)} 단계[/red]")
            
            console.print("\n[red]실패한 단계들:[/red]")
            for step_name, step_desc in failed_steps:
                console.print(f"  - {step_desc} ({step_name})")
        else:
            console.print(f"[green]🎉 전체 프로세스가 성공적으로 완료되었습니다![/green]")
            console.print(f"[green]완료: {len(steps)}/{len(steps)} 단계[/green]")
            
    except Exception as e:
        logger.error(f"전체 프로세스 실행 중 오류 발생: {e}")
        console.print(f"[red]❌ 전체 프로세스 실행 중 오류: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive():
    """대화형 모드로 프로세서를 실행합니다."""
    check_fpat_availability()
    
    processors, file_manager, excel_manager = create_processors()
    
    # 메뉴 정의
    menu_options = {
        "1": ("parse_request", "신청 정보 파싱", lambda: processors['request_parser'].parse_request_type(file_manager)),
        "2": ("extract_request", "신청 ID 추출", lambda: processors['request_extractor'].extract_request_id(file_manager)),
        "3": ("add_mis_id", "MIS ID 추가", lambda: processors['mis_id_adder'].add_mis_id(file_manager)),
        "4": ("collect_applications", "신청 정보 취합", lambda: processors['application_aggregator'].collect_applications(file_manager)),
        "5": ("add_request_info", "신청 정보 추가", lambda: processors['request_info_adder'].add_request_info(file_manager)),
        "6": ("handle_exception_paloalto", "팔로알토 예외처리", lambda: processors['exception_handler'].paloalto_exception(file_manager)),
        "7": ("handle_exception_secui", "시큐아이 예외처리", lambda: processors['exception_handler'].secui_exception(file_manager)),
        "8": ("classify_duplicates", "중복정책 분류", lambda: processors['duplicate_policy_classifier'].organize_redundant_file(file_manager)),
        "9": ("add_duplicate_status", "중복정책 상태 추가", lambda: processors['duplicate_policy_classifier'].add_duplicate_status(file_manager)),
        "10": ("merge_hitcount", "히트카운트 병합", lambda: processors['merge_hitcount'].mergehitcounts(file_manager)),
        "11": ("add_usage_status", "미사용 정책 정보 추가", lambda: processors['policy_usage_processor'].add_usage_status(file_manager)),
        "12": ("update_excepted_usage", "미사용 예외 정책 업데이트", lambda: processors['policy_usage_processor'].update_excepted_usage(file_manager)),
        "13": ("classify_notifications", "공지파일 분류", lambda: processors['notification_classifier'].classify_notifications(file_manager, excel_manager)),
        "99": ("run_full_paloalto", "전체 프로세스 실행 (팔로알토)", lambda: run_full_process_internal(processors, file_manager, excel_manager, "paloalto")),
        "98": ("run_full_secui", "전체 프로세스 실행 (시큐아이)", lambda: run_full_process_internal(processors, file_manager, excel_manager, "secui")),
    }
    
    while True:
        console.clear()
        
        # 메뉴 표시
        table = Table(title="🗑️ 정책 삭제 프로세서 대화형 모드", border_style="blue")
        table.add_column("번호", style="dim", width=4)
        table.add_column("작업", style="magenta", width=30)
        table.add_column("설명", style="cyan")
        
        for key, (_, desc, _) in menu_options.items():
            if key in ["99", "98"]:
                table.add_row(key, desc, "전체 프로세스를 순차적으로 실행", style="bold green")
            else:
                table.add_row(key, desc, "개별 프로세서 실행")
        
        table.add_row("0", "종료", "대화형 모드 종료", style="bold red")
        
        console.print(table)
        
        # 사용자 입력 받기
        choice = Prompt.ask(
            "\n[bold yellow]실행할 작업을 선택하세요[/bold yellow]",
            choices=list(menu_options.keys()) + ["0"],
            default="0"
        )
        
        if choice == "0":
            console.print("[green]대화형 모드를 종료합니다.[/green]")
            break
        
        if choice in menu_options:
            _, desc, func = menu_options[choice]
            console.print(f"\n[blue]📋 {desc} 실행 중...[/blue]")
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"{desc} 중...", total=None)
                    
                    success = func()
                    
                    if success:
                        progress.update(task, description=f"✅ {desc} 완료")
                        console.print(f"[green]✅ {desc}가 완료되었습니다.[/green]")
                    else:
                        progress.update(task, description=f"❌ {desc} 실패")
                        console.print(f"[red]❌ {desc}에 실패했습니다.[/red]")
                        
            except Exception as e:
                logger.error(f"{desc} 중 오류 발생: {e}")
                console.print(f"[red]❌ 오류: {e}[/red]")
            
            # 계속 진행할지 묻기
            if not Confirm.ask("\n계속 진행하시겠습니까?", default=True):
                break
        
        console.print("\n[dim]아무 키나 누르면 메뉴로 돌아갑니다...[/dim]")
        input()


def run_full_process_internal(processors, file_manager, excel_manager, vendor):
    """내부적으로 전체 프로세스를 실행하는 함수"""
    # 전체 프로세스 단계 정의
    steps = [
        ("parse_request", "신청 정보 파싱", lambda: processors['request_parser'].parse_request_type(file_manager)),
        ("extract_request", "신청 ID 추출", lambda: processors['request_extractor'].extract_request_id(file_manager)),
        ("add_mis_id", "MIS ID 추가", lambda: processors['mis_id_adder'].add_mis_id(file_manager)),
        ("collect_applications", "신청 정보 취합", lambda: processors['application_aggregator'].collect_applications(file_manager)),
        ("add_request_info", "신청 정보 추가", lambda: processors['request_info_adder'].add_request_info(file_manager)),
        ("handle_exception", f"{vendor} 예외처리", lambda: processors['exception_handler'].paloalto_exception(file_manager) if vendor.lower() == "paloalto" else processors['exception_handler'].secui_exception(file_manager)),
        ("classify_duplicates", "중복정책 분류", lambda: processors['duplicate_policy_classifier'].organize_redundant_file(file_manager)),
        ("add_duplicate_status", "중복정책 상태 추가", lambda: processors['duplicate_policy_classifier'].add_duplicate_status(file_manager)),
        ("merge_hitcount", "히트카운트 병합", lambda: processors['merge_hitcount'].mergehitcounts(file_manager)),
        ("add_usage_status", "미사용 정책 정보 추가", lambda: processors['policy_usage_processor'].add_usage_status(file_manager)),
        ("update_excepted_usage", "미사용 예외 정책 업데이트", lambda: processors['policy_usage_processor'].update_excepted_usage(file_manager)),
        ("classify_notifications", "공지파일 분류", lambda: processors['notification_classifier'].classify_notifications(file_manager, excel_manager))
    ]
    
    failed_steps = []
    
    for i, (step_name, step_desc, step_func) in enumerate(steps, 1):
        console.print(f"\n[blue]📋 {i}/{len(steps)} {step_desc} 실행 중...[/blue]")
        
        try:
            success = step_func()
            
            if success:
                console.print(f"[green]✅ {step_desc} 완료[/green]")
            else:
                console.print(f"[red]❌ {step_desc} 실패[/red]")
                failed_steps.append((step_name, step_desc))
                
        except Exception as e:
            console.print(f"[red]❌ {step_desc} 오류: {e}[/red]")
            failed_steps.append((step_name, step_desc))
            logger.error(f"{step_desc} 중 오류 발생: {e}")
    
    # 결과 요약
    console.print("\n" + "="*50)
    if failed_steps:
        console.print(f"[yellow]⚠️  일부 단계에서 오류가 발생했습니다.[/yellow]")
        console.print(f"[green]성공: {len(steps) - len(failed_steps)}/{len(steps)} 단계[/green]")
        console.print(f"[red]실패: {len(failed_steps)}/{len(steps)} 단계[/red]")
        
        console.print("\n[red]실패한 단계들:[/red]")
        for step_name, step_desc in failed_steps:
            console.print(f"  - {step_desc} ({step_name})")
        return False
    else:
        console.print(f"[green]🎉 전체 프로세스가 성공적으로 완료되었습니다![/green]")
        console.print(f"[green]완료: {len(steps)}/{len(steps)} 단계[/green]")
        return True


@app.command()
def list_processors():
    """사용 가능한 프로세서 목록을 표시합니다."""
    check_fpat_availability()
    
    processors_info = [
        ("RequestParser", "신청 정보 파싱", "규칙 이름과 설명에서 신청 정보를 파싱합니다"),
        ("RequestExtractor", "신청 ID 추출", "파일에서 신청 ID를 추출합니다"),
        ("MisIdAdder", "MIS ID 추가", "파일에 MIS ID를 추가합니다"),
        ("ApplicationAggregator", "신청 정보 취합", "GSAMS에서 전달받은 신청 정보를 취합합니다"),
        ("RequestInfoAdder", "신청 정보 추가", "파일에 신청 정보를 추가합니다"),
        ("ExceptionHandler", "예외처리", "팔로알토/시큐아이 정책에서 예외처리를 수행합니다"),
        ("DuplicatePolicyClassifier", "중복정책 분류", "중복정책을 분류하고 유지/삭제를 결정합니다"),
        ("MergeHitcount", "히트카운트 병합", "FPAT으로 추출된 Hit 정보 2개를 병합합니다"),
        ("PolicyUsageProcessor", "미사용 정책 처리", "미사용 정책 정보를 정책 파일에 추가합니다"),
        ("NotificationClassifier", "공지파일 분류", "정리대상별 공지파일을 분류합니다")
    ]
    
    table = Table(title="📋 정책 삭제 프로세서 목록", border_style="green")
    table.add_column("프로세서", style="magenta", width=25)
    table.add_column("기능", style="cyan", width=20)
    table.add_column("설명", style="white")
    
    for processor, function, description in processors_info:
        table.add_row(processor, function, description)
    
    console.print(table)


if __name__ == "__main__":
    app()