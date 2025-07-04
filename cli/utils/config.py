"""
CLI 설정 관리 모듈
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel


class FirewallConfig(BaseModel):
    """방화벽 설정"""
    hostname: str
    username: str
    password: str
    vendor: str  # paloalto, ngf, mf2


class CLIConfig(BaseModel):
    """CLI 설정"""
    output_dir: str = "./outputs"
    log_level: str = "INFO"
    excel_format: str = "xlsx"
    firewalls: Dict[str, FirewallConfig] = {}


class Config:
    """설정 관리자"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로를 반환합니다."""
        home = Path.home()
        return str(home / ".fpat_config.json")
    
    def _load_config(self) -> CLIConfig:
        """설정 파일을 로드합니다."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return CLIConfig(**data)
            except Exception:
                pass
        
        # 기본 설정 반환
        return CLIConfig()
    
    def save_config(self):
        """설정을 파일에 저장합니다."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config.model_dump(), f, indent=2, ensure_ascii=False)
    
    def get_output_dir(self) -> str:
        """출력 디렉토리를 반환합니다."""
        output_dir = self.config.output_dir
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def add_firewall(self, name: str, config: FirewallConfig):
        """방화벽 설정을 추가합니다."""
        self.config.firewalls[name] = config
        self.save_config()
    
    def get_firewall(self, name: str) -> Optional[FirewallConfig]:
        """방화벽 설정을 가져옵니다."""
        return self.config.firewalls.get(name)