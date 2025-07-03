#!/usr/bin/env python3
"""
Hoon Firewall Modules 라이브러리 테스트 스크립트

이 스크립트는 라이브러리가 정상적으로 import되고 사용 가능한지 테스트합니다.
"""

def test_imports():
    """모든 주요 모듈이 정상적으로 import되는지 테스트"""
    try:
        # 현재 디렉토리에서 직접 import 테스트
        print("1. 현재 디렉토리에서 직접 import 테스트...")
        import __init__ as hoon_firewall_modules
        print(f"   ✅ 라이브러리 버전: {hoon_firewall_modules.__version__}")
        
        # 주요 클래스들 import 테스트
        print("2. 주요 클래스 import 테스트...")
        from __init__ import PolicyComparator, FirewallInterface, PolicyAnalyzer
        print("   ✅ PolicyComparator, FirewallInterface, PolicyAnalyzer import 성공")
        
        # 모듈별 import 테스트
        print("3. 모듈별 import 테스트...")
        import fpat.policy_comparator as policy_comparator
        import fpat.firewall_module as firewall_module  
        import fpat.firewall_analyzer as firewall_analyzer
        import fpat.policy_deletion_processor as policy_deletion_processor
        print("   ✅ 모든 서브모듈 import 성공")
        
        # 개별 모듈 클래스 테스트
        print("4. 개별 모듈 클래스 테스트...")
        from fpat.policy_comparator import PolicyComparator
        from fpat.firewall_analyzer import RedundancyAnalyzer
        print("   ✅ 개별 모듈 클래스 import 성공")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
        return False

def test_basic_functionality():
    """기본 기능이 정상 작동하는지 테스트"""
    try:
        print("5. 기본 기능 테스트...")
        
        # PolicyComparator 인스턴스 생성 테스트
        from fpat.policy_comparator import PolicyComparator
        # 실제 파일이 없어도 인스턴스 생성은 가능해야 함
        comparator = PolicyComparator("test1.xlsx", "test2.xlsx", "test3.xlsx", "test4.xlsx")
        print("   ✅ PolicyComparator 인스턴스 생성 성공")
        
        # PolicyAnalyzer 인스턴스 생성 테스트
        from fpat.firewall_analyzer import PolicyAnalyzer
        analyzer = PolicyAnalyzer()
        print("   ✅ PolicyAnalyzer 인스턴스 생성 성공")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 기능 테스트 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 Hoon Firewall Modules 라이브러리 테스트 시작\n")
    
    success_count = 0
    total_tests = 2
    
    # Import 테스트
    if test_imports():
        success_count += 1
    
    print()  # 빈 줄
    
    # 기본 기능 테스트  
    if test_basic_functionality():
        success_count += 1
    
    print("\n" + "="*50)
    print(f"📊 테스트 결과: {success_count}/{total_tests} 성공")
    
    if success_count == total_tests:
        print("🎉 모든 테스트 통과! 라이브러리가 정상적으로 작동합니다.")
        print("\n📚 사용법:")
        print("   # 현재 디렉토리에서:")
        print("   from modules.policy_comparator import PolicyComparator")
        print("   from modules.firewall_analyzer import PolicyAnalyzer")
        print("   from modules.firewall_module import FirewallInterface")
        return 0
    else:
        print("⚠️  일부 테스트 실패. 라이브러리 설정을 확인해주세요.")
        return 1

if __name__ == "__main__":
    exit(main()) 