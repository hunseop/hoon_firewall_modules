"""
CLI 로깅 설정 모듈
"""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console


def setup_logger(name: str = "fpat_cli", level: str = "INFO") -> logging.Logger:
    """Rich 기반 로거를 설정합니다."""
    
    # 로거 생성
    logger = logging.getLogger(name)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Rich 핸들러 추가
    console = Console(stderr=True)
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True
    )
    
    # 포맷터 설정
    formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(formatter)
    
    # 로거 설정
    logger.addHandler(rich_handler)
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False
    
    return logger