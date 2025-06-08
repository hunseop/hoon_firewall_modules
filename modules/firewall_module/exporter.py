import pandas as pd
from .collector_factory import FirewallCollectorFactory

def export_policy_to_excel(
    vendor: str,
    hostname: str,
    username: str,
    password: str,
    export_type: str,
    output_path: str,
    config_type: str = "running"
) -> str:
    """
    방화벽 장비에서 정책, 객체, 사용 로그를 추출하여 Excel로 저장합니다.

    Parameters:
        vendor (str): 장비 유형 (예: 'paloalto', 'mf2', 'ngf')
        hostname (str): 장비 IP 또는 호스트명
        username (str): 장비 로그인 계정
        password (str): 장비 로그인 비밀번호
        export_type (str): 추출할 항목 ('policy', 'address', ..., 'all')
        output_path (str): 저장할 엑셀 파일 경로
        config_type (str): 'running' 또는 'candidate' (paloalto only)

    Returns:
        str: 저장된 엑셀 파일 경로
    """
    if vendor.lower() == "paloalto":
        if config_type not in ("running", "candidate"):
            raise ValueError("PaloAlto 장비는 config_type으로 'running' 또는 'candidate'만 허용됩니다.")
    else:
        config_type = "running"

    collector = FirewallCollectorFactory.get_collector(
        source_type=vendor,
        hostname=hostname,
        username=username,
        password=password
    )

    sheets = {}

    if export_type in ("policy", "all"):
        if vendor.lower() == "paloalto":
            sheets["policy"] = collector.export_security_rules(config_type=config_type)
        else:
            sheets["policy"] = collector.export_security_rules()

    if export_type in ("address", "all"):
        sheets["address"] = collector.export_network_objects()

    if export_type in ("address_group", "all"):
        sheets["address_group"] = collector.export_network_group_objects()

    if export_type in ("service", "all"):
        sheets["service"] = collector.export_service_objects()

    if export_type in ("service_group", "all"):
        df = collector.export_service_group_objects()
        if df is not None and not df.empty:
            sheets["service_group"] = df

    if export_type == "usage":
        df = collector.export_usage_logs()
        if df is not None and not df.empty:
            sheets["usage"] = df

    if not sheets:
        raise ValueError(f"지원하지 않는 export_type 또는 데이터 없음: {export_type}")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)

    return output_path