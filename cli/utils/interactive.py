"""
대화형 CLI 기능 모듈
"""

import questionary
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .config import Config

console = Console()


def interactive_firewall_selector() -> Optional[str]:
    """대화형 방화벽 선택"""
    config = Config()
    firewalls = config.config.firewalls
    
    if not firewalls:
        console.print("[yellow]⚠️ 저장된 방화벽이 없습니다.[/yellow]")
        return None
    
    choices = [
        questionary.Choice(
            title=f"{name} ({fw.vendor} - {fw.hostname})",
            value=name
        )
        for name, fw in firewalls.items()
    ]
    
    return questionary.select(
        "🛡️ 방화벽을 선택하세요:",
        choices=choices,
        use_shortcuts=True,
        style=questionary.Style([
            ('question', 'fg:#ff0066 bold'),
            ('answer', 'fg:#44ff00 bold'),
            ('pointer', 'fg:#ff0066 bold'),
            ('highlighted', 'fg:#ff0066 bold'),
            ('selected', 'fg:#cc5454'),
            ('separator', 'fg:#cc5454'),
            ('instruction', ''),
            ('text', ''),
            ('disabled', 'fg:#858585 italic')
        ])
    ).ask()


def interactive_vendor_selector() -> Optional[str]:
    """대화형 벤더 선택"""
    vendors = [
        questionary.Choice("🔥 PaloAlto Networks", "paloalto"),
        questionary.Choice("🛡️ SECUI NGF", "ngf"),
        questionary.Choice("⚡ SECUI MF2", "mf2"),
        questionary.Choice("🧪 Mock (테스트)", "mock")
    ]
    
    return questionary.select(
        "🏢 방화벽 벤더를 선택하세요:",
        choices=vendors,
        use_shortcuts=True
    ).ask()


def interactive_file_selector(description: str = "파일을 선택하세요") -> Optional[str]:
    """대화형 파일 선택"""
    import glob
    import os
    
    # Excel 파일 찾기
    xlsx_files = glob.glob("*.xlsx")
    xls_files = glob.glob("*.xls")
    all_files = xlsx_files + xls_files
    
    if not all_files:
        console.print("[yellow]⚠️ 현재 디렉토리에 Excel 파일이 없습니다.[/yellow]")
        return questionary.text(f"📄 {description}:").ask()
    
    choices = [questionary.Choice(f"📊 {file}", file) for file in all_files]
    choices.append(questionary.Choice("✏️ 직접 입력", "custom"))
    
    result = questionary.select(
        f"📄 {description}:",
        choices=choices,
        use_shortcuts=True
    ).ask()
    
    if result == "custom":
        return questionary.text("파일 경로를 입력하세요:").ask()
    
    return result


def interactive_search_type_selector() -> Optional[str]:
    """대화형 검색 타입 선택"""
    choices = [
        questionary.Choice("🎯 Source 주소로 검색", "source"),
        questionary.Choice("🏠 Destination 주소로 검색", "destination"),
        questionary.Choice("🔄 양방향 검색", "both")
    ]
    
    return questionary.select(
        "🔍 검색 타입을 선택하세요:",
        choices=choices,
        use_shortcuts=True
    ).ask()


def interactive_main_menu() -> Optional[str]:
    """대화형 메인 메뉴"""
    choices = [
        questionary.Choice("🛡️  방화벽 연동 및 데이터 수집", "firewall"),
        questionary.Choice("🔍 정책 및 객체 비교 분석", "compare"),
        questionary.Choice("📊 정책 분석 (중복성, Shadow 등)", "analyze"),
        questionary.Choice("🗑️  정책 삭제 영향도 분석", "deletion"),
        questionary.Choice("⚡ 자동완성 설정", "completion"),
        questionary.Choice("📋 버전 정보", "version"),
        questionary.Choice("❌ 종료", "exit")
    ]
    
    return questionary.select(
        "🔥 FPAT CLI - 원하는 기능을 선택하세요:",
        choices=choices,
        use_shortcuts=True,
        style=questionary.Style([
            ('question', 'fg:#ff0066 bold'),
            ('answer', 'fg:#44ff00 bold'),
            ('pointer', 'fg:#ff0066 bold'),
            ('highlighted', 'fg:#ff0066 bold'),
            ('selected', 'fg:#cc5454'),
            ('separator', 'fg:#cc5454'),
            ('instruction', ''),
            ('text', ''),
            ('disabled', 'fg:#858585 italic')
        ])
    ).ask()


def interactive_firewall_submenu() -> Optional[str]:
    """대화형 방화벽 서브메뉴"""
    choices = [
        questionary.Choice("➕ 새 방화벽 추가", "add"),
        questionary.Choice("📋 방화벽 목록 보기", "list"),
        questionary.Choice("📥 데이터 수집", "collect"),
        questionary.Choice("⬅️  메인 메뉴로", "back")
    ]
    
    return questionary.select(
        "🛡️ 방화벽 기능을 선택하세요:",
        choices=choices,
        use_shortcuts=True
    ).ask()


def interactive_analyze_submenu() -> Optional[str]:
    """대화형 분석 서브메뉴"""
    choices = [
        questionary.Choice("🔄 중복성 분석", "redundancy"),
        questionary.Choice("👻 Shadow 정책 분석", "shadow"),
        questionary.Choice("🔍 IP 필터링", "filter"),
        questionary.Choice("⬅️  메인 메뉴로", "back")
    ]
    
    return questionary.select(
        "📊 분석 기능을 선택하세요:",
        choices=choices,
        use_shortcuts=True
    ).ask()


def interactive_compare_submenu() -> Optional[str]:
    """대화형 비교 서브메뉴"""
    choices = [
        questionary.Choice("📋 정책 비교", "policies"),
        questionary.Choice("🔧 객체 비교", "objects"),
        questionary.Choice("🔍 전체 비교", "full"),
        questionary.Choice("⬅️  메인 메뉴로", "back")
    ]
    
    return questionary.select(
        "🔍 비교 기능을 선택하세요:",
        choices=choices,
        use_shortcuts=True
    ).ask()


def interactive_firewall_add() -> Optional[Dict[str, str]]:
    """대화형 방화벽 추가"""
    console.print(Panel("🛡️ 새 방화벽 추가", border_style="cyan"))
    
    name = questionary.text("방화벽 이름:").ask()
    if not name:
        return None
    
    hostname = questionary.text("호스트명 또는 IP:").ask()
    if not hostname:
        return None
    
    username = questionary.text("사용자명:").ask()
    if not username:
        return None
    
    password = questionary.password("비밀번호:").ask()
    if not password:
        return None
    
    vendor = interactive_vendor_selector()
    if not vendor:
        return None
    
    return {
        "name": name,
        "hostname": hostname,
        "username": username,
        "password": password,
        "vendor": vendor
    }


def confirm_action(message: str) -> bool:
    """확인 대화상자"""
    return questionary.confirm(f"❓ {message}").ask() or False


def show_success_message(message: str):
    """성공 메시지 표시"""
    console.print(Panel(f"✅ {message}", border_style="green"))


def show_error_message(message: str):
    """에러 메시지 표시"""
    console.print(Panel(f"❌ {message}", border_style="red"))


def show_info_message(message: str):
    """정보 메시지 표시"""
    console.print(Panel(f"ℹ️ {message}", border_style="blue"))