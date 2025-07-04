"""
CLI 자동완성 기능 유틸리티
"""

import typer
from typing import List
from .config import Config


def complete_firewall_names(incomplete: str) -> List[str]:
    """방화벽 이름 자동완성"""
    try:
        config = Config()
        firewall_names = list(config.config.firewalls.keys())
        
        # 부분 매치 필터링
        return [name for name in firewall_names if name.startswith(incomplete)]
    except:
        return []


def complete_vendors(incomplete: str) -> List[str]:
    """벤더 이름 자동완성"""
    vendors = ["paloalto", "ngf", "mf2", "mock"]
    return [vendor for vendor in vendors if vendor.startswith(incomplete)]


def complete_search_types(incomplete: str) -> List[str]:
    """검색 타입 자동완성"""
    search_types = ["source", "destination", "both"]
    return [stype for stype in search_types if stype.startswith(incomplete)]


def complete_file_extensions(incomplete: str) -> List[str]:
    """파일 확장자 자동완성"""
    try:
        import glob
        
        # 현재 디렉토리의 .xlsx 파일들
        xlsx_files = glob.glob("*.xlsx")
        excel_files = glob.glob("*.xls")
        
        all_files = xlsx_files + excel_files
        return [f for f in all_files if f.startswith(incomplete)]
    except:
        return []


def setup_shell_completion():
    """Shell 자동완성 설정 안내"""
    completion_instructions = """
🎯 Shell 자동완성 설정 방법:

1. Bash의 경우:
   eval "$(_FPAT_CLI_COMPLETE=bash_source python3 fpat_cli.py)"
   
   또는 ~/.bashrc에 추가:
   echo 'eval "$(_FPAT_CLI_COMPLETE=bash_source python3 fpat_cli.py)"' >> ~/.bashrc

2. Zsh의 경우:
   eval "$(_FPAT_CLI_COMPLETE=zsh_source python3 fpat_cli.py)"
   
   또는 ~/.zshrc에 추가:
   echo 'eval "$(_FPAT_CLI_COMPLETE=zsh_source python3 fpat_cli.py)"' >> ~/.zshrc

3. Fish의 경우:
   eval (env _FPAT_CLI_COMPLETE=fish_source python3 fpat_cli.py)

설정 후 새 터미널을 열거나 'source ~/.bashrc' 실행하세요.
그러면 Tab 키로 자동완성을 사용할 수 있습니다!
"""
    return completion_instructions