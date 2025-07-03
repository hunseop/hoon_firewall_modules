#!/usr/bin/env python3
"""
PolicyFilter 테스트 스크립트
"""

import pandas as pd
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fpat.firewall_analyzer import PolicyFilter
    print("✅ PolicyFilter import 성공")
except ImportError as e:
    print(f"❌ PolicyFilter import 실패: {e}")
    sys.exit(1)

def create_test_data():
    """테스트용 방화벽 정책 데이터 생성"""
    test_data = [
        {
            'Rule Name': 'Rule_1',
            'Enable': 'Y',
            'Action': 'allow',
            'Source': '192.168.1.0/24',
            'Destination': '10.0.0.0/8',
            'Service': 'TCP/80',
            'Extracted Source': '192.168.1.0/24',
            'Extracted Destination': '10.0.0.0/8',
            'Extracted Service': 'TCP/80'
        },
        {
            'Rule Name': 'Rule_2',
            'Enable': 'Y',
            'Action': 'allow',
            'Source': '192.168.1.100',
            'Destination': '10.1.1.1',
            'Service': 'TCP/443',
            'Extracted Source': '192.168.1.100',
            'Extracted Destination': '10.1.1.1',
            'Extracted Service': 'TCP/443'
        },
        {
            'Rule Name': 'Rule_3',
            'Enable': 'Y',
            'Action': 'deny',
            'Source': '172.16.0.0/16',
            'Destination': '10.2.2.0/24',
            'Service': 'TCP/22',
            'Extracted Source': '172.16.0.0/16',
            'Extracted Destination': '10.2.2.0/24',
            'Extracted Service': 'TCP/22'
        },
        {
            'Rule Name': 'Rule_4',
            'Enable': 'Y',
            'Action': 'allow',
            'Source': '192.168.1.1-192.168.1.50',
            'Destination': '10.3.3.3',
            'Service': 'UDP/53',
            'Extracted Source': '192.168.1.1-192.168.1.50',
            'Extracted Destination': '10.3.3.3',
            'Extracted Service': 'UDP/53'
        },
        {
            'Rule Name': 'Rule_5',
            'Enable': 'Y',
            'Action': 'allow',
            'Source': 'any',
            'Destination': '10.4.4.4',
            'Service': 'TCP/80',
            'Extracted Source': 'any',
            'Extracted Destination': '10.4.4.4',
            'Extracted Service': 'TCP/80'
        },
        {
            'Rule Name': 'Rule_6',
            'Enable': 'N',
            'Action': 'allow',
            'Source': '192.168.2.0/24',
            'Destination': '10.5.5.5',
            'Service': 'TCP/8080',
            'Extracted Source': '192.168.2.0/24',
            'Extracted Destination': '10.5.5.5',
            'Extracted Service': 'TCP/8080'
        }
    ]
    
    return pd.DataFrame(test_data)

def test_source_filtering():
    """Source 주소 기준 필터링 테스트"""
    print("\n=== Source 필터링 테스트 ===")
    
    df = create_test_data()
    filter_obj = PolicyFilter()
    
    # CIDR 검색 테스트
    print("\n1. CIDR 검색 테스트 (192.168.1.0/24)")
    result = filter_obj.filter_by_source(df, "192.168.1.0/24", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")
    
    # 단일 IP 검색 테스트
    print("\n2. 단일 IP 검색 테스트 (192.168.1.100)")
    result = filter_obj.filter_by_source(df, "192.168.1.100", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")
    
    # any 포함 테스트
    print("\n3. any 포함 검색 테스트 (192.168.1.100)")
    result = filter_obj.filter_by_source(df, "192.168.1.100", include_any=True)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")
    
    # 범위 검색 테스트
    print("\n4. 범위 검색 테스트 (192.168.1.1-192.168.1.50)")
    result = filter_obj.filter_by_source(df, "192.168.1.1-192.168.1.50", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")

def test_destination_filtering():
    """Destination 주소 기준 필터링 테스트"""
    print("\n=== Destination 필터링 테스트 ===")
    
    df = create_test_data()
    filter_obj = PolicyFilter()
    
    # CIDR 검색 테스트
    print("\n1. CIDR 검색 테스트 (10.0.0.0/8)")
    result = filter_obj.filter_by_destination(df, "10.0.0.0/8", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")
    
    # 단일 IP 검색 테스트
    print("\n2. 단일 IP 검색 테스트 (10.1.1.1)")
    result = filter_obj.filter_by_destination(df, "10.1.1.1", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")

def test_both_filtering():
    """Source/Destination 모두 검색 테스트"""
    print("\n=== Source/Destination 모두 검색 테스트 ===")
    
    df = create_test_data()
    filter_obj = PolicyFilter()
    
    # 192.168.1.0/24 범위가 포함된 모든 정책 검색
    print("\n1. 192.168.1.0/24가 포함된 모든 정책 검색")
    result = filter_obj.filter_by_both(df, "192.168.1.0/24", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")

def test_complex_filtering():
    """복합 조건 필터링 테스트"""
    print("\n=== 복합 조건 필터링 테스트 ===")
    
    df = create_test_data()
    filter_obj = PolicyFilter()
    
    # AND 모드 테스트
    print("\n1. AND 모드 테스트 (Source: 192.168.1.0/24, Destination: 10.0.0.0/8)")
    result = filter_obj.filter_by_criteria(
        df, 
        source_address="192.168.1.0/24", 
        destination_address="10.0.0.0/8",
        match_mode="AND",
        include_any=False
    )
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")
    
    # OR 모드 테스트
    print("\n2. OR 모드 테스트 (Source: 172.16.0.0/16, Destination: 10.4.4.4)")
    result = filter_obj.filter_by_criteria(
        df, 
        source_address="172.16.0.0/16", 
        destination_address="10.4.4.4",
        match_mode="OR",
        include_any=False
    )
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")

def test_filter_summary():
    """필터링 요약 기능 테스트"""
    print("\n=== 필터링 요약 테스트 ===")
    
    df = create_test_data()
    filter_obj = PolicyFilter()
    
    # Source 필터링
    result = filter_obj.filter_by_source(df, "192.168.1.0/24", include_any=True)
    
    # 요약 정보 생성
    summary = filter_obj.get_filter_summary(
        df, 
        result, 
        {'search_type': 'source', 'address': '192.168.1.0/24', 'include_any': True}
    )
    
    print("필터링 요약:")
    print(f"  - 검색 조건: {summary['search_criteria']}")
    print(f"  - 전체 정책 수: {summary['total_policies']}")
    print(f"  - 매치된 정책 수: {summary['matched_policies']}")
    print(f"  - 매치 비율: {summary['match_percentage']:.1f}%")
    print(f"  - 활성화된 정책 수: {summary['enabled_policies']}")
    print(f"  - Action 분포: {summary['action_distribution']}")

def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n=== 엣지 케이스 테스트 ===")
    
    df = create_test_data()
    filter_obj = PolicyFilter()
    
    # 빈 데이터프레임 테스트
    print("\n1. 빈 데이터프레임 테스트")
    empty_df = pd.DataFrame()
    result = filter_obj.filter_by_source(empty_df, "192.168.1.0/24")
    print(f"   결과: {len(result)}개 정책 발견")
    
    # 존재하지 않는 IP 테스트
    print("\n2. 존재하지 않는 IP 테스트 (203.0.113.0/24)")
    result = filter_obj.filter_by_source(df, "203.0.113.0/24", include_any=False)
    print(f"   결과: {len(result)}개 정책 발견")
    
    # any 검색 테스트
    print("\n3. any 검색 테스트")
    result = filter_obj.filter_by_source(df, "any", include_any=True)
    print(f"   결과: {len(result)}개 정책 발견")
    if not result.empty:
        print(f"   매치된 정책: {list(result['Rule Name'])}")

def main():
    """메인 테스트 함수"""
    print("PolicyFilter 종합 테스트 시작...")
    
    try:
        # 테스트 데이터 확인
        df = create_test_data()
        print(f"\n테스트 데이터: {len(df)}개 정책")
        print("정책 목록:")
        for idx, row in df.iterrows():
            print(f"  {row['Rule Name']}: {row['Source']} -> {row['Destination']} ({row['Action']})")
        
        # 각종 테스트 실행
        test_source_filtering()
        test_destination_filtering()
        test_both_filtering()
        test_complex_filtering()
        test_filter_summary()
        test_edge_cases()
        
        print("\n🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 