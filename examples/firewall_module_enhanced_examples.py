#!/usr/bin/env python3
"""
Firewall Module Enhanced Examples
개선된 방화벽 모듈의 기능들을 보여주는 종합 예제

v1.2.0의 주요 개선사항:
- 로깅 시스템
- 예외 처리 강화
- 입력 검증
- 성능 최적화
- 진행률 추적
"""

import sys
import logging
import time
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

import modules.firewall_module as fw

def example_1_basic_usage():
    """예제 1: 기본 사용법 - 로깅과 예외 처리"""
    print("=" * 60)
    print("예제 1: 기본 사용법 - 로깅과 예외 처리")
    print("=" * 60)
    
    # 로깅 설정
    logger = fw.setup_firewall_logger(__name__, level=logging.INFO)
    
    try:
        logger.info("방화벽 정책 추출 시작")
        
        # Mock 방화벽을 사용한 안전한 테스트
        output_file = fw.export_policy_to_excel(
            vendor="mock",
            hostname="test-firewall.local",
            username="admin",
            password="password",
            export_type="policy",
            output_path="./examples/output/basic_policies.xlsx"
        )
        
        logger.info(f"정책 추출 완료: {output_file}")
        
    except fw.FirewallConnectionError as e:
        logger.error(f"방화벽 연결 실패: {e}")
    except fw.FirewallAuthenticationError as e:
        logger.error(f"인증 실패: {e}")
    except fw.FirewallDataError as e:
        logger.error(f"데이터 추출 실패: {e}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")

def example_2_progress_tracking():
    """예제 2: 진행률 추적 및 성능 모니터링"""
    print("\n" + "=" * 60)
    print("예제 2: 진행률 추적 및 성능 모니터링")
    print("=" * 60)
    
    def progress_callback(current: int, total: int):
        """진행률 콜백 함수"""
        percentage = (current / total) * 100
        print(f"  📊 진행률: {percentage:.1f}% ({current}/{total})")
    
    # 로깅 설정
    logger = fw.setup_firewall_logger(__name__)
    
    try:
        logger.info("전체 데이터 추출 시작 (진행률 추적 포함)")
        
        # 성능 모니터링과 함께 실행
        with fw.performance_monitor("전체 데이터 추출", logger):
            output_file = fw.export_policy_to_excel(
                vendor="mock",
                hostname="test-firewall.local",
                username="admin",
                password="password",
                export_type="all",
                output_path="./examples/output/complete_data.xlsx",
                chunk_size=100,  # 작은 청크로 더 자주 업데이트
                progress_callback=progress_callback
            )
        
        logger.info(f"전체 데이터 추출 완료: {output_file}")
        
    except Exception as e:
        logger.error(f"데이터 추출 실패: {e}")

def example_3_retry_logic():
    """예제 3: 재시도 로직 및 안정적인 연결"""
    print("\n" + "=" * 60)
    print("예제 3: 재시도 로직 및 안정적인 연결")
    print("=" * 60)
    
    # 재시도 데코레이터 적용
    @fw.retry_on_failure(max_attempts=3, delay=1.0, backoff_factor=2.0)
    def extract_with_retry():
        """재시도 로직이 적용된 데이터 추출"""
        logger = fw.setup_firewall_logger(__name__)
        
        # 가끔 실패하는 상황을 시뮬레이션
        import random
        if random.random() < 0.5:  # 50% 확률로 실패
            raise fw.FirewallConnectionError("임시 연결 실패 (테스트)")
        
        return fw.export_policy_to_excel(
            vendor="mock",
            hostname="unstable-firewall.local",
            username="admin",
            password="password",
            export_type="address",
            output_path="./examples/output/retry_test.xlsx"
        )
    
    logger = fw.setup_firewall_logger(__name__)
    
    try:
        logger.info("재시도 로직 테스트 시작")
        output_file = extract_with_retry()
        logger.info(f"재시도 로직으로 추출 성공: {output_file}")
        
    except Exception as e:
        logger.error(f"최종 실패: {e}")

def example_4_collector_direct_usage():
    """예제 4: Collector 직접 사용 및 연결 상태 관리"""
    print("\n" + "=" * 60)
    print("예제 4: Collector 직접 사용 및 연결 상태 관리")
    print("=" * 60)
    
    logger = fw.setup_firewall_logger(__name__)
    collector = None
    
    try:
        logger.info("Collector 직접 사용 예제 시작")
        
        # Collector 생성
        collector = fw.FirewallCollectorFactory.get_collector(
            source_type="mock",
            hostname="test-firewall.local",
            username="admin",
            password="password",
            timeout=30
        )
        
        # 연결 상태 확인
        if collector.is_connected():
            logger.info("✅ 방화벽 연결 성공")
            
            # 연결 정보 출력
            conn_info = collector.get_connection_info()
            logger.info(f"📡 연결 정보: {conn_info}")
            
            # 개별 데이터 추출
            logger.info("개별 데이터 추출 시작")
            
            policies = collector.export_security_rules()
            addresses = collector.export_network_objects()
            services = collector.export_service_objects()
            
            logger.info(f"📋 추출 완료 - 정책: {len(policies)}개, "
                       f"주소: {len(addresses)}개, 서비스: {len(services)}개")
        else:
            logger.error("❌ 방화벽 연결 실패")
            
    except fw.FirewallUnsupportedError as e:
        logger.error(f"지원하지 않는 방화벽: {e}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
    finally:
        # 연결 해제
        if collector:
            try:
                collector.disconnect()
                logger.info("🔌 방화벽 연결 해제 완료")
            except Exception as e:
                logger.warning(f"연결 해제 중 오류: {e}")

def example_5_input_validation():
    """예제 5: 입력 검증 및 설정 확인"""
    print("\n" + "=" * 60)
    print("예제 5: 입력 검증 및 설정 확인")
    print("=" * 60)
    
    logger = fw.setup_firewall_logger(__name__)
    
    # 지원되는 벤더 확인
    supported_vendors = fw.FirewallCollectorFactory.get_supported_vendors()
    logger.info(f"🏢 지원되는 벤더: {supported_vendors}")
    
    # 특정 벤더의 요구사항 확인
    for vendor in supported_vendors:
        try:
            requirements = fw.FirewallCollectorFactory.get_vendor_requirements(vendor)
            logger.info(f"📋 {vendor.upper()} 필수 파라미터: {requirements}")
        except fw.FirewallUnsupportedError as e:
            logger.error(f"❌ {vendor}: {e}")
    
    # 입력값 검증 테스트
    validator = fw.FirewallValidator()
    
    test_cases = [
        # (설명, 검증 함수, 입력값, 예상 결과)
        ("올바른 IP 주소", validator.validate_hostname, "192.168.1.100", True),
        ("올바른 호스트명", validator.validate_hostname, "firewall.company.com", True),
        ("잘못된 IP 주소", validator.validate_hostname, "999.999.999.999", False),
        ("빈 호스트명", validator.validate_hostname, "", False),
        ("올바른 인증 정보", lambda: validator.validate_credentials("admin", "password123"), None, True),
        ("빈 사용자명", lambda: validator.validate_credentials("", "password"), None, False),
        ("올바른 익스포트 타입", validator.validate_export_type, "policy", True),
        ("잘못된 익스포트 타입", validator.validate_export_type, "invalid", False),
    ]
    
    logger.info("🔍 입력 검증 테스트 시작")
    
    for description, func, input_value, expected in test_cases:
        try:
            if input_value is not None:
                result = func(input_value)
            else:
                result = func()
            
            if expected:
                logger.info(f"  ✅ {description}: 통과")
            else:
                logger.warning(f"  ⚠️  {description}: 예상과 다른 결과 (통과됨)")
                
        except fw.FirewallConfigurationError as e:
            if not expected:
                logger.info(f"  ✅ {description}: 예상대로 실패 ({e})")
            else:
                logger.error(f"  ❌ {description}: 예상치 못한 실패 ({e})")
        except Exception as e:
            logger.error(f"  ❌ {description}: 검증 오류 ({e})")

def example_6_memory_optimization():
    """예제 6: 메모리 최적화 및 대용량 데이터 처리"""
    print("\n" + "=" * 60)
    print("예제 6: 메모리 최적화 및 대용량 데이터 처리")
    print("=" * 60)
    
    logger = fw.setup_firewall_logger(__name__)
    
    # 메모리 사용량 모니터링을 위한 간단한 함수
    def get_memory_usage():
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0  # psutil이 없으면 0 반환
    
    initial_memory = get_memory_usage()
    logger.info(f"💾 초기 메모리 사용량: {initial_memory:.1f} MB")
    
    try:
        # 다양한 청크 크기로 테스트
        chunk_sizes = [100, 500, 1000]
        
        for chunk_size in chunk_sizes:
            logger.info(f"🔄 청크 크기 {chunk_size}로 테스트 시작")
            
            start_memory = get_memory_usage()
            
            with fw.performance_monitor(f"청크 크기 {chunk_size} 처리", logger):
                output_file = fw.export_policy_to_excel(
                    vendor="mock",
                    hostname="test-firewall.local",
                    username="admin",
                    password="password",
                    export_type="all",
                    output_path=f"./examples/output/chunk_{chunk_size}.xlsx",
                    chunk_size=chunk_size
                )
            
            end_memory = get_memory_usage()
            memory_diff = end_memory - start_memory
            
            logger.info(f"  📁 파일 생성: {output_file}")
            logger.info(f"  💾 메모리 증가: {memory_diff:.1f} MB")
            
            # 잠시 대기 (메모리 정리 시간)
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"메모리 최적화 테스트 실패: {e}")
    
    final_memory = get_memory_usage()
    total_diff = final_memory - initial_memory
    logger.info(f"💾 최종 메모리 사용량: {final_memory:.1f} MB (증가: {total_diff:.1f} MB)")

def example_7_error_handling():
    """예제 7: 종합 오류 처리 시나리오"""
    print("\n" + "=" * 60)
    print("예제 7: 종합 오류 처리 시나리오")
    print("=" * 60)
    
    logger = fw.setup_firewall_logger(__name__)
    
    # 다양한 오류 시나리오 테스트
    error_scenarios = [
        {
            "name": "지원하지 않는 벤더",
            "params": {
                "vendor": "unsupported",
                "hostname": "test.local",
                "username": "admin",
                "password": "password",
                "export_type": "policy"
            },
            "expected_error": fw.FirewallUnsupportedError
        },
        {
            "name": "잘못된 호스트명",
            "params": {
                "vendor": "mock",
                "hostname": "",
                "username": "admin",
                "password": "password",
                "export_type": "policy"
            },
            "expected_error": fw.FirewallConfigurationError
        },
        {
            "name": "잘못된 익스포트 타입",
            "params": {
                "vendor": "mock",
                "hostname": "test.local",
                "username": "admin",
                "password": "password",
                "export_type": "invalid_type"
            },
            "expected_error": fw.FirewallConfigurationError
        }
    ]
    
    logger.info("🧪 오류 처리 시나리오 테스트 시작")
    
    for scenario in error_scenarios:
        logger.info(f"  🔄 테스트: {scenario['name']}")
        
        try:
            fw.export_policy_to_excel(
                **scenario['params'],
                output_path="./examples/output/error_test.xlsx"
            )
            
            logger.warning(f"    ⚠️  예상된 오류가 발생하지 않음")
            
        except scenario['expected_error'] as e:
            logger.info(f"    ✅ 예상된 오류 정상 처리: {e}")
        except Exception as e:
            logger.error(f"    ❌ 예상과 다른 오류: {type(e).__name__}: {e}")

def create_output_directory():
    """출력 디렉토리 생성"""
    output_dir = Path("./examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def main():
    """메인 함수 - 모든 예제 실행"""
    print("🔥 Firewall Module Enhanced Examples")
    print(f"📦 버전: {fw.__version__}")
    print(f"⏰ 실행 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 출력 디렉토리 생성
    output_dir = create_output_directory()
    print(f"📁 출력 디렉토리: {output_dir.absolute()}")
    
    # 예제 실행
    examples = [
        example_1_basic_usage,
        example_2_progress_tracking,
        example_3_retry_logic,
        example_4_collector_direct_usage,
        example_5_input_validation,
        example_6_memory_optimization,
        example_7_error_handling
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except KeyboardInterrupt:
            print(f"\n⏹️  사용자에 의해 중단됨 (예제 {i})")
            break
        except Exception as e:
            print(f"\n❌ 예제 {i} 실행 중 오류: {e}")
            continue
    
    print(f"\n🎉 모든 예제 실행 완료!")
    print(f"📁 생성된 파일들을 확인하세요: {output_dir.absolute()}")

if __name__ == "__main__":
    main() 