#!/usr/bin/env python3
"""
ShadowAnalyzer 테스트 스크립트
"""

import pandas as pd
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from modules.firewall_analyzer import ShadowAnalyzer
    print("✅ ShadowAnalyzer import 성공")
except ImportError as e:
    print(f"❌ ShadowAnalyzer import 실패: {e}")
    sys.exit(1)

def test_shadow_analyzer():
    """ShadowAnalyzer 기본 기능 테스트"""
    
    print("\n=== ShadowAnalyzer 테스트 시작 ===")
    
    # 테스트 데이터 생성
    test_data = [
        {
            'Rule Name': 'Rule_1',
            'Enable': 'Y',
            'Action': 'allow',
            'Extracted Source': '192.168.1.0/24',
            'Extracted Destination': '10.0.0.0/8',
            'Extracted Service': 'TCP/80,TCP/443',
            'Application': 'web-browsing',
            'User': 'any'
        },
        {
            'Rule Name': 'Rule_2',
            'Enable': 'Y',
            'Action': 'allow',
            'Extracted Source': '192.168.1.100/32',  # Rule_1의 부분집합
            'Extracted Destination': '10.1.1.1/32',   # Rule_1의 부분집합
            'Extracted Service': 'TCP/80',             # Rule_1의 부분집합
            'Application': 'web-browsing',
            'User': 'any'
        },
        {
            'Rule Name': 'Rule_3',
            'Enable': 'Y',
            'Action': 'allow',
            'Extracted Source': '172.16.0.0/16',      # 다른 범위
            'Extracted Destination': '10.2.2.2/32',
            'Extracted Service': 'TCP/22',
            'Application': 'ssh',
            'User': 'any'
        }
    ]
    
    df = pd.DataFrame(test_data)
    print(f"테스트 데이터: {len(df)}개 정책")
    
    # ShadowAnalyzer 인스턴스 생성
    analyzer = ShadowAnalyzer()
    
    try:
        # Shadow 분석 실행
        results = analyzer.analyze(df, vendor='default')
        
        print(f"\n분석 결과: {len(results)}개의 shadow 정책 발견")
        
        if not results.empty:
            print("\n=== Shadow 정책 상세 결과 ===")
            for idx, row in results.iterrows():
                print(f"Shadow 정책: {row.get('Rule Name', 'Unknown')}")
                print(f"  - Shadow By: {row.get('Shadow_By_Rule', 'Unknown')}")
                print(f"  - Reason: {row.get('Shadow_Reason', 'Unknown')}")
                print()
        
        # 요약 정보 출력
        summary = analyzer.get_shadow_summary(results)
        print("\n=== Shadow 분석 요약 ===")
        print(f"총 Shadow 정책 수: {summary['total_shadow_policies']}")
        print(f"Action별 Shadow 정책: {summary['shadow_by_action']}")
        print(f"가장 많이 가리는 정책들: {summary['most_shadowing_rules']}")
        
        print("\n✅ ShadowAnalyzer 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ ShadowAnalyzer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_all():
    """모든 firewall_analyzer 클래스 import 테스트"""
    
    print("\n=== Analysis Module Import 테스트 ===")
    
    try:
        from modules.firewall_analyzer import (
            PolicyAnalyzer, 
            RedundancyAnalyzer, 
            ChangeAnalyzer, 
            PolicyResolver, 
            ShadowAnalyzer
        )
        
        print("✅ PolicyAnalyzer import 성공")
        print("✅ RedundancyAnalyzer import 성공")
        print("✅ ChangeAnalyzer import 성공")
        print("✅ PolicyResolver import 성공")
        print("✅ ShadowAnalyzer import 성공")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False

if __name__ == "__main__":
    print("ShadowAnalyzer 테스트 실행 중...")
    
    # Import 테스트
    import_success = test_import_all()
    
    if import_success:
        # 기능 테스트
        test_success = test_shadow_analyzer()
        
        if test_success:
            print("\n🎉 모든 테스트 성공!")
        else:
            print("\n❌ 테스트 실패")
            sys.exit(1)
    else:
        print("\n❌ Import 테스트 실패")
        sys.exit(1) 