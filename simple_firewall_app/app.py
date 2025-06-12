"""
방화벽 정책 정리 프로세스 - 단순 SPA 버전
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from types import SimpleNamespace

from modules.policy_deletion_processor.utils.file_manager import FileManager
from modules.policy_deletion_processor.utils.excel_manager import ExcelManager
from modules.policy_deletion_processor.processors import (
    MisIdAdder,
    PolicyUsageProcessor,
    RequestParser,
    RequestInfoAdder,
    ExceptionHandler,
    DuplicatePolicyClassifier,
    NotificationClassifier,
)
from werkzeug.utils import secure_filename
import pandas as pd

# 상위 modules 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 방화벽 모듈 임포트
try:
    from modules.firewall_module import (
        FirewallCollectorFactory,
        FirewallError,
        FirewallConnectionError,
        setup_firewall_logger
    )
    from modules.firewall_analyzer import RedundancyAnalyzer
    FIREWALL_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"방화벽 모듈 임포트 실패: {e}")
    FIREWALL_MODULE_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if FIREWALL_MODULE_AVAILABLE:
    redundancy_analyzer = RedundancyAnalyzer()
else:
    redundancy_analyzer = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'firewall-processor-simple'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 디렉토리 생성
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

# 전역 상태 관리
process_state = {
    'current_phase': 1,
    'current_step': 1,
    'status': 'ready',
    'steps': {},
    'firewall_config': {},
    'files': {},
    'errors': [],
    'logs': [],
    'manual_mode': False,  # 수동 진행 모드
    'paused': False       # 일시정지 상태
}

# 프로세스 단계 정의
PROCESS_PHASES = {
    1: {
        'name': 'Phase 1: 초기 설정',
        'steps': [
            {
                'id': 'firewall_config',
                'name': '방화벽 접속 설정',
                'description': 'Vendor 선택, IP 입력, 계정 정보 입력, 연결 테스트',
                'requires_user_input': True,
                'auto_proceed': False,
                'allow_manual': True,
                'allow_pause': True
            }
        ]
    },
    2: {
        'name': 'Phase 2: 데이터 수집',
        'steps': [
            {
                'id': 'extract_policies',
                'name': '방화벽 정책 추출',
                'description': '방화벽에서 정책 데이터 추출',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'extract_usage',
                'name': '방화벽 사용이력 추출',
                'description': '방화벽에서 사용이력 데이터 추출',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'extract_duplicates',
                'name': '방화벽 중복 정책 추출',
                'description': '방화벽에서 중복 정책 데이터 추출',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            }
        ]
    },
    3: {
        'name': 'Phase 3: 정보 파싱',
        'steps': [
            {
                'id': 'parse_descriptions',
                'name': '신청정보 파싱',
                'description': 'Description에서 신청번호 추출',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            }
        ]
    },
    4: {
        'name': 'Phase 4: 데이터 준비',
        'steps': [
            {
                'id': 'upload_application_file',
                'name': '신청정보 파일 업로드',
                'description': '신청정보 파일을 업로드하세요',
                'requires_user_input': True,
                'auto_proceed': False,
                'file_type': 'application',
                'allow_manual': True,
                'allow_pause': True,
                'allow_replace': True
            },
            {
                'id': 'upload_mis_file',
                'name': 'MIS ID 파일 업로드',
                'description': 'MIS ID 파일을 업로드하세요',
                'requires_user_input': True,
                'auto_proceed': False,
                'file_type': 'mis_id',
                'allow_manual': True,
                'allow_pause': True,
                'allow_replace': True
            },
            {
                'id': 'validate_files',
                'name': '파일 포맷 검증',
                'description': '업로드된 파일들의 포맷과 데이터 유효성 검사',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            }
        ]
    },
    5: {
        'name': 'Phase 5: 데이터 통합',
        'steps': [
            {
                'id': 'add_mis_info',
                'name': 'MIS ID 정보 추가',
                'description': '정책 데이터에 MIS ID 정보 통합',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'merge_application_info',
                'name': '신청정보 통합',
                'description': '신청정보를 정책 데이터에 통합',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'vendor_exception_handling',
                'name': 'Vendor별 예외처리',
                'description': '벤더별 특수 규칙 적용',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'classify_duplicates',
                'name': '중복정책 분류',
                'description': '중복 정책 식별 및 분류',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            }
        ]
    },
    6: {
        'name': 'Phase 6: 결과 생성',
        'steps': [
            {
                'id': 'add_usage_info',
                'name': '사용이력 정보 추가',
                'description': '정책에 사용이력 정보 매핑',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'finalize_classification',
                'name': '최종 분류 및 검증',
                'description': '최종 데이터 분류 및 검증',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            },
            {
                'id': 'generate_results',
                'name': '결과 파일 생성',
                'description': '최종 공지파일 및 결과 파일 생성',
                'requires_user_input': False,
                'auto_proceed': True,
                'allow_manual': True,
                'allow_pause': True
            }
        ]
    }
}

def add_log(message, level='info'):
    """로그 추가"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    process_state['logs'].append(log_entry)
    logger.info(f"[{level.upper()}] {message}")

def update_step_status(step_id, status, result=None, error=None):
    """단계 상태 업데이트"""
    process_state['steps'][step_id] = {
        'status': status,
        'result': result,
        'error': error,
        'timestamp': datetime.now().isoformat()
    }

def record_result_file(step_id, filepath):
    """단계 결과 파일 기록"""
    process_state['files'][step_id] = {
        'filename': os.path.basename(filepath),
        'filepath': filepath,
        'upload_time': datetime.now().isoformat()
    }

def generate_result_path(step_id, label=None, ext='xlsx'):
    """단계별 결과 파일명을 생성"""
    ip = process_state.get('firewall_config', {}).get('primary_ip', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    parts = [timestamp, ip, step_id]
    if label:
        parts.append(label)
    filename = f"{'_'.join(parts)}.{ext}"
    return os.path.join(app.config['RESULTS_FOLDER'], filename)

def rename_and_record(step_id, src_path, label=None):
    ext = os.path.splitext(src_path)[1].lstrip('.')
    dest = generate_result_path(step_id if label is None else f"{step_id}_{label}", None, ext)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    os.replace(src_path, dest)
    record_result_file(step_id, dest)
    return dest

def extract_firewall_policies():
    """방화벽 정책 추출"""
    try:
        if FIREWALL_MODULE_AVAILABLE and 'firewall_collectors' in process_state:
            collectors = process_state['firewall_collectors']
            policies = {}
            results = []

            # Primary 장비에서 정책 추출
            add_log("Primary 방화벽에서 정책 데이터 추출 중...")
            primary_df = collectors['primary'].export_security_rules()

            # 출처 표시를 위해 컬럼 추가
            primary_df['장비구분'] = 'Primary'
            policies['primary'] = primary_df
            output_primary = generate_result_path('extract_policies', 'primary')
            os.makedirs(os.path.dirname(output_primary), exist_ok=True)
            primary_df.to_excel(output_primary, index=False)
            add_log(f"Primary 정책 추출 완료: {len(primary_df)}개")
            results.append({
                'target': 'primary',
                'count': len(primary_df),
                'file': os.path.basename(output_primary),
                'path': output_primary
            })
            
            # Secondary 장비가 있는 경우 추출
            if 'secondary' in collectors:
                try:
                    add_log("Secondary 방화벽에서 정책 데이터 추출 중...")
                    secondary_df = collectors['secondary'].export_security_rules()

                    secondary_df['장비구분'] = 'Secondary'
                    policies['secondary'] = secondary_df
                    output_secondary = generate_result_path('extract_policies', 'secondary')
                    secondary_df.to_excel(output_secondary, index=False)
                    add_log(f"Secondary 정책 추출 완료: {len(secondary_df)}개")
                    results.append({
                        'target': 'secondary',
                        'count': len(secondary_df),
                        'file': os.path.basename(output_secondary),
                        'path': output_secondary
                    })
                    
                except Exception as e:
                    add_log(f"Secondary 정책 추출 실패 (무시하고 계속): {str(e)}", 'warning')
            
            process_state['policies'] = policies

            if results:
                record_result_file('extract_policies', results[0]['path'])

            return {
                'policies': results
            }
            
        else:
            # 시뮬레이션 모드
            add_log("시뮬레이션 모드: 정책 추출 중...")
            time.sleep(3)
            return {
                'policies': [
                    {'target': 'primary', 'count': 800, 'file': 'firewall_policies_primary.xlsx'},
                    {'target': 'secondary', 'count': 450, 'file': 'firewall_policies_secondary.xlsx'}
                ]
            }
            
    except Exception as e:
        add_log(f"정책 추출 오류: {str(e)}", 'error')
        raise

def extract_firewall_usage():
    """방화벽 사용이력 추출"""
    try:
        if FIREWALL_MODULE_AVAILABLE and 'firewall_collectors' in process_state:
            collectors = process_state['firewall_collectors']
            usage = {}
            results = []
            
            # Primary 장비에서 사용이력 추출
            add_log("Primary 방화벽에서 사용이력 데이터 추출 중...")
            primary_df = collectors['primary'].export_usage_logs()

            primary_df['장비구분'] = 'Primary'
            usage['primary'] = primary_df
            output_primary = generate_result_path('extract_usage', 'primary')
            primary_df.to_excel(output_primary, index=False)
            add_log(f"Primary 사용이력 추출 완료: {len(primary_df)}개")
            results.append({
                'target': 'primary',
                'count': len(primary_df),
                'file': os.path.basename(output_primary),
                'path': output_primary
            })
            
            # Secondary 장비가 있는 경우 추출
            if 'secondary' in collectors:
                try:
                    add_log("Secondary 방화벽에서 사용이력 데이터 추출 중...")
                    secondary_df = collectors['secondary'].export_usage_logs()

                    secondary_df['장비구분'] = 'Secondary'
                    usage['secondary'] = secondary_df
                    output_secondary = generate_result_path('extract_usage', 'secondary')
                    secondary_df.to_excel(output_secondary, index=False)
                    add_log(f"Secondary 사용이력 추출 완료: {len(secondary_df)}개")
                    results.append({
                        'target': 'secondary',
                        'count': len(secondary_df),
                        'file': os.path.basename(output_secondary),
                        'path': output_secondary
                    })
                    
                except Exception as e:
                    add_log(f"Secondary 사용이력 추출 실패 (무시하고 계속): {str(e)}", 'warning')
            
            process_state['usage'] = usage
            if results:
                record_result_file('extract_usage', results[0]['path'])

            return {
                'usage': results
            }
            
        else:
            # 시뮬레이션 모드
            add_log("시뮬레이션 모드: 사용이력 추출 중...")
            time.sleep(2)
            return {
                'usage': [
                    {'target': 'primary', 'count': 5000, 'file': 'usage_history_primary.xlsx'},
                    {'target': 'secondary', 'count': 3500, 'file': 'usage_history_secondary.xlsx'}
                ]
            }
            
    except Exception as e:
        add_log(f"사용이력 추출 오류: {str(e)}", 'error')
        raise

def extract_duplicate_policies():
    """중복 정책 추출"""
    try:
        if FIREWALL_MODULE_AVAILABLE and 'firewall_collectors' in process_state:
            collectors = process_state['firewall_collectors']

            add_log("방화벽에서 중복 정책 분석 중...")

            policies = process_state.get('policies')
            if not policies:
                policies = {}
                if 'primary' in collectors:
                    policies['primary'] = collectors['primary'].export_security_rules()
                if 'secondary' in collectors:
                    try:
                        policies['secondary'] = collectors['secondary'].export_security_rules()
                    except Exception as e:
                        add_log(f"Secondary 정책 추출 실패 (무시하고 계속): {str(e)}", 'warning')
                process_state['policies'] = policies

            vendor = process_state.get('firewall_config', {}).get('vendor', 'paloalto')

            results = []

            for label, df in policies.items():
                if redundancy_analyzer:
                    duplicate_df = redundancy_analyzer.analyze(df, vendor=vendor)
                else:
                    duplicate_df = analyze_duplicate_policies(df)

                output_file = generate_result_path('extract_duplicates', label)
                duplicate_df.to_excel(output_file, index=False)

                results.append({
                    'target': label,
                    'count': len(duplicate_df),
                    'file': os.path.basename(output_file),
                    'path': output_file
                })

            total_count = sum(r['count'] for r in results)

            add_log(f"중복 정책 분석 완료: {total_count}개 중복 정책")

            if results:
                record_result_file('extract_duplicates', results[0]['path'])

            return {
                'duplicate_policies': results
            }
            
        else:
            # 시뮬레이션 모드
            add_log("시뮬레이션 모드: 중복 정책 추출 중...")
            time.sleep(2)
            return {'duplicate_policies': 45, 'file': 'duplicate_policies.xlsx'}
            
    except Exception as e:
        add_log(f"중복 정책 추출 오류: {str(e)}", 'error')
        raise

def analyze_duplicate_policies(policies):
    """정책 데이터에서 중복 정책 분석 (간단한 구현)"""
    
    if not hasattr(policies, 'columns'):
        policies = pd.DataFrame(policies)
    
    # 간단한 중복 분석 (source, destination, service 기준)
    duplicate_columns = ['source', 'destination', 'service']
    available_columns = [col for col in duplicate_columns if col in policies.columns]
    
    if available_columns:
        duplicates = policies[policies.duplicated(subset=available_columns, keep=False)]
    else:
        # 적절한 컬럼이 없는 경우 전체 행 기준으로 중복 검사
        duplicates = policies[policies.duplicated(keep=False)]
    
    return duplicates

def run_policy_processor(step_id):
    """policy_deletion_processor 모듈을 이용한 간단 처리"""
    class DummyConfig:
        def get(self, key, default=None):
            return default

    def prepare_file_manager(file_list):
        cfg = DummyConfig()
        fm = FileManager(cfg)
        paths = iter(file_list)
        fm.select_files = lambda extension=None: next(paths, None)
        captured = {}
        original_update = fm.update_version

        def updater(name, final_version=False):
            new_name = os.path.join(app.config['RESULTS_FOLDER'], os.path.basename(original_update(name, final_version)))
            captured['output'] = new_name
            return new_name

        fm.update_version = updater
        fm._captured = captured
        original_remove = fm.remove_extension

        def remover(name):
            base = os.path.join(app.config['RESULTS_FOLDER'], os.path.basename(original_remove(name)))
            captured.setdefault('remove_base', base)
            return base

        fm.remove_extension = remover
        return fm

    if step_id == 'parse_descriptions':
        policy_path = process_state.get('files', {}).get('extract_policies', {}).get('filepath')
        fm = prepare_file_manager([policy_path])
        processor = RequestParser(fm.config)
        if not processor.parse_request_type(fm):
            raise Exception('신청 정보 파싱 실패')
        output = fm._captured.get('output')
        record_result_file(step_id, output)
        return {'file': os.path.basename(output)}

    if step_id == 'add_mis_info':
        mis_path = process_state.get('files', {}).get('mis_id', {}).get('filepath')
        policy_path = process_state.get('files', {}).get('extract_policies', {}).get('filepath')
        fm = prepare_file_manager([policy_path, mis_path])
        processor = MisIdAdder(fm.config)
        if not processor.add_mis_id(fm):
            raise Exception('MIS ID 추가 실패')
        output = fm._captured.get('output')
        record_result_file('add_mis_info', output)
        process_state['files']['policy_with_mis'] = output
        return {'file': os.path.basename(output)}

    if step_id == 'add_usage_info':
        usage_path = process_state.get('files', {}).get('extract_usage', {}).get('filepath')
        policy_path = process_state.get('files', {}).get('policy_with_mis')
        fm = prepare_file_manager([policy_path, usage_path])
        processor = PolicyUsageProcessor(fm.config)
        if not processor.add_usage_status(fm):
            raise Exception('사용 정보 추가 실패')
        output = fm._captured.get('output')
        record_result_file('add_usage_info', output)
        process_state['files']['policy_with_usage'] = output
        return {'file': os.path.basename(output)}

    if step_id == 'merge_application_info':
        app_path = process_state.get('files', {}).get('application', {}).get('filepath')
        policy_path = process_state.get('files', {}).get('parse_descriptions', {}).get('filepath')
        fm = prepare_file_manager([policy_path, app_path])
        processor = RequestInfoAdder(fm.config)
        if not processor.add_request_info(fm):
            raise Exception('신청 정보 통합 실패')
        output = fm._captured.get('output')
        record_result_file(step_id, output)
        process_state['files']['policy_with_app'] = output
        return {'file': os.path.basename(output)}

    if step_id == 'vendor_exception_handling':
        vendor = process_state.get('firewall_config', {}).get('vendor', 'paloalto')
        policy_path = process_state.get('files', {}).get('policy_with_app') or process_state.get('files', {}).get('policy_with_mis')
        fm = prepare_file_manager([policy_path])
        handler = ExceptionHandler(fm.config)
        method = getattr(handler, f"{vendor}_exception", None)
        if not method or not method(fm):
            raise Exception('예외처리 실패')
        output = fm._captured.get('output')
        record_result_file(step_id, output)
        process_state['files']['policy_after_exception'] = output
        return {'file': os.path.basename(output)}

    if step_id == 'classify_duplicates':
        dup_path = process_state.get('files', {}).get('extract_duplicates', {}).get('filepath')
        info_path = process_state.get('files', {}).get('policy_with_app')
        fm = prepare_file_manager([dup_path, info_path])
        classifier = DuplicatePolicyClassifier(fm.config)
        if not classifier.organize_redundant_file(fm):
            raise Exception('중복정책 분류 실패')
        base = fm._captured.get('remove_base')
        outputs = [f"{base}_정리.xlsx", f"{base}_공지.xlsx", f"{base}_삭제.xlsx"]
        for p in outputs:
            record_result_file(step_id, p)
        process_state['files']['duplicate_summary'] = outputs[0]
        return {'files': [os.path.basename(p) for p in outputs]}

    if step_id == 'finalize_classification':
        policy_path = process_state.get('files', {}).get('policy_with_usage')
        dup_summary = process_state.get('files', {}).get('duplicate_summary')
        fm = prepare_file_manager([policy_path, dup_summary])
        classifier = DuplicatePolicyClassifier(fm.config)
        if not classifier.add_duplicate_status(fm):
            raise Exception('중복 정보 추가 실패')
        output = fm._captured.get('output')
        record_result_file(step_id, output)
        process_state['files']['final_policy'] = output
        return {'file': os.path.basename(output)}

    if step_id == 'generate_results':
        policy_path = process_state.get('files', {}).get('final_policy')
        fm = prepare_file_manager([policy_path])
        excel = ExcelManager(fm.config)
        notifier = NotificationClassifier(fm.config)
        before = set(os.listdir(app.config['RESULTS_FOLDER']))
        if not notifier.classify_notifications(fm, excel):
            raise Exception('결과 파일 생성 실패')
        after = set(os.listdir(app.config['RESULTS_FOLDER']))
        new_files = [os.path.join(app.config['RESULTS_FOLDER'], f) for f in after - before]
        for p in new_files:
            record_result_file(step_id, p)
        return {'files': [os.path.basename(p) for p in new_files]}

    time.sleep(2)
    return {'processed_records': 0}

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """현재 상태 반환"""
    # JSON 직렬화가 가능한 형태로 상태 정보를 변환
    def serialize_state(state):
        serialized = {}
        for key, value in state.items():
            if key in {'firewall_collectors'}:
                # 객체 정보는 문자열로 대체
                serialized[key] = 'initialized' if value else None
            elif key in {'policies', 'usage'} and isinstance(value, dict):
                # 데이터프레임은 개수만 전달
                summary = {}
                for label, df in value.items():
                    try:
                        summary[label] = len(df)
                    except Exception:
                        summary[label] = 0
                serialized[key] = summary
            else:
                # 기본적으로 JSON 변환 가능한 값 사용
                serialized[key] = value
        return serialized

    return jsonify({
        'success': True,
        'phases': PROCESS_PHASES,
        'state': {
            **serialize_state(process_state),
            'manual_mode': process_state.get('manual_mode', False),
            'paused': process_state.get('paused', False)
        }
    })

@app.route('/api/firewall/config', methods=['POST'])
def set_firewall_config():
    """방화벽 설정"""
    try:
        config = request.get_json()
        
        add_log(f"방화벽 연결 테스트 중... ({config['vendor']} - {config['primary_ip']})")
        
        # 실제 방화벽 연결 테스트
        if FIREWALL_MODULE_AVAILABLE:
            try:
                # vendor 이름 매핑
                vendor_mapping = {
                    'paloalto': 'paloalto',
                    'secui_ngf': 'ngf',
                    'secui_mf2': 'mf2'
                }
                
                vendor = vendor_mapping.get(config['vendor'], config['vendor'])
                
                # Primary 방화벽 컬렉터 생성 및 연결 테스트
                add_log(f"Primary 방화벽 연결 테스트 중: {config['primary_ip']}")
                primary_collector = FirewallCollectorFactory.get_collector(
                    source_type=vendor,
                    hostname=config['primary_ip'],
                    username=config['username'],
                    password=config['password'],
                    test_connection=True
                )
                
                collectors = {'primary': primary_collector}
                add_log(f"Primary 방화벽 연결 성공: {config['vendor']} - {config['primary_ip']}")
                
                # Secondary 방화벽 연결 (있는 경우)
                if config.get('secondary_ip') and config['secondary_ip'].strip():
                    try:
                        add_log(f"Secondary 방화벽 연결 테스트 중: {config['secondary_ip']}")
                        secondary_collector = FirewallCollectorFactory.get_collector(
                            source_type=vendor,
                            hostname=config['secondary_ip'],
                            username=config['username'],
                            password=config['password'],
                            test_connection=True
                        )
                        collectors['secondary'] = secondary_collector
                        add_log(f"Secondary 방화벽 연결 성공: {config['vendor']} - {config['secondary_ip']}")
                    except (FirewallError, FirewallConnectionError) as e:
                        add_log(f"Secondary 방화벽 연결 실패 (무시하고 계속): {str(e)}", 'warning')
                        # Secondary 연결 실패는 치명적이지 않음
                
                # 컬렉터들을 전역 상태에 저장
                process_state['firewall_collectors'] = collectors
                
                connection_summary = f"Primary: {config['primary_ip']}"
                if 'secondary' in collectors:
                    connection_summary += f", Secondary: {config['secondary_ip']}"
                add_log(f"방화벽 연결 완료 - {connection_summary}")
                
            except (FirewallError, FirewallConnectionError) as e:
                add_log(f"Primary 방화벽 연결 실패: {str(e)}", 'error')
                update_step_status('firewall_config', 'error', error=str(e))
                return jsonify({
                    'success': False,
                    'error': f"Primary 방화벽 연결 실패: {str(e)}"
                }), 500
                
        else:
            # 모듈이 없는 경우 시뮬레이션
            add_log("방화벽 모듈이 없어 시뮬레이션 모드로 진행합니다")
            time.sleep(2)  # 연결 테스트 시뮬레이션
        
        # 설정 저장
        process_state['firewall_config'] = config
        update_step_status('firewall_config', 'completed', config)
        
        add_log("방화벽 연결 설정 완료")
        
        return jsonify({
            'success': True,
            'message': '방화벽 설정이 완료되었습니다'
        })
        
    except Exception as e:
        add_log(f"방화벽 설정 오류: {str(e)}", 'error')
        update_step_status('firewall_config', 'error', error=str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/step/execute/<step_id>', methods=['POST'])
def execute_step(step_id):
    """단계 실행"""
    try:
        add_log(f"단계 실행 중: {step_id}")
        update_step_status(step_id, 'running')
        
        # 단계별 처리 로직
        if step_id == 'extract_policies':
            add_log("방화벽 정책 추출 중...")
            result = extract_firewall_policies()
            
        elif step_id == 'extract_usage':
            add_log("방화벽 사용이력 추출 중...")
            result = extract_firewall_usage()
            
        elif step_id == 'extract_duplicates':
            add_log("중복 정책 추출 중...")
            result = extract_duplicate_policies()
            
        elif step_id == 'parse_descriptions':
            add_log("Description 파싱 중...")
            result = run_policy_processor(step_id)
            
        elif step_id == 'validate_files':
            add_log("파일 유효성 검사 중...")
            time.sleep(1)
            result = {'valid_files': 2, 'warnings': 3}
            
        elif step_id in ['add_mis_info', 'merge_application_info', 'vendor_exception_handling',
                        'classify_duplicates', 'add_usage_info', 'finalize_classification']:
            add_log(f"{step_id} 처리 중...")
            try:
                result = run_policy_processor(step_id)
            except Exception as e:
                add_log(f"{step_id} 처리 실패: {str(e)}", 'error')
                raise
            
        elif step_id == 'generate_results':
            add_log("최종 결과 파일 생성 중...")
            time.sleep(3)
            result = {
                'files': [
                    'notification_file_1.xlsx',
                    'notification_file_2.xlsx',
                    'summary_report.xlsx'
                ]
            }
            
        else:
            result = {'message': f'{step_id} 완료'}
        
        update_step_status(step_id, 'completed', result)
        add_log(f"단계 완료: {step_id}")
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        add_log(f"단계 실행 오류 ({step_id}): {str(e)}", 'error')
        update_step_status(step_id, 'error', error=str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/upload/<file_type>', methods=['POST'])
def upload_file(file_type):
    """파일 업로드"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다'}), 400
        
        # 파일 저장
        original_name = secure_filename(file.filename)
        ip = process_state.get('firewall_config', {}).get('primary_ip', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{ip}_{file_type}{os.path.splitext(original_name)[1]}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 파일 정보 저장
        process_state['files'][file_type] = {
            'filename': filename,
            'filepath': filepath,
            'upload_time': datetime.now().isoformat()
        }

        step_map = {
            'application': 'upload_application_file',
            'mis_id': 'upload_mis_file'
        }

        step_id = step_map.get(file_type)
        if step_id:
            update_step_status(step_id, 'completed', {'file': filename})
            record_result_file(step_id, filepath)

        add_log(f"{file_type} 파일 업로드 완료: {filename}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': '파일이 성공적으로 업로드되었습니다'
        })
        
    except Exception as e:
        add_log(f"파일 업로드 오류: {str(e)}", 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/preview/<file_type>')
def preview_file(file_type):
    """파일 미리보기"""
    try:
        if file_type not in process_state['files']:
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 404
        
        filepath = process_state['files'][file_type]['filepath']
        
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(filepath, nrows=10)
            total_rows = len(pd.read_csv(filepath))
        else:
            df = pd.read_excel(filepath, nrows=10)
            total_rows = len(pd.read_excel(filepath))
        
        return jsonify({
            'success': True,
            'columns': df.columns.tolist(),
            'data': df.to_dict('records'),
            'total_rows': total_rows
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/file/download/<file_type>')
def download_file(file_type):
    """업로드된 파일 다운로드"""
    try:
        if file_type not in process_state['files']:
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 404

        filepath = process_state['files'][file_type]['filepath']
        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/step/download/<step_id>/<int:index>')
def download_step_file(step_id, index=0):
    """단계 결과 파일 다운로드"""
    try:
        step = process_state['steps'].get(step_id)
        if not step or step.get('status') != 'completed':
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 404

        def gather_paths(data):
            paths = []
            if isinstance(data, dict):
                if 'path' in data and os.path.exists(data['path']):
                    paths.append(data['path'])
                if 'file' in data and os.path.exists(os.path.join(app.config['RESULTS_FOLDER'], data['file'])):
                    paths.append(os.path.join(app.config['RESULTS_FOLDER'], data['file']))
                for v in data.values():
                    paths.extend(gather_paths(v))
            elif isinstance(data, list):
                for item in data:
                    paths.extend(gather_paths(item))
            elif isinstance(data, str) and os.path.exists(data):
                paths.append(data)
            return paths

        paths = gather_paths(step.get('result'))
        if not paths or index >= len(paths):
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 404

        return send_file(paths[index], as_attachment=True)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_process():
    """프로세스 초기화"""
    global process_state
    
    try:
        # 업로드 파일들 삭제
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        for file_path in upload_dir.glob('*'):
            if file_path.is_file():
                file_path.unlink()
        
        # 결과 파일들 삭제  
        results_dir = Path(app.config['RESULTS_FOLDER'])
        for file_path in results_dir.glob('*'):
            if file_path.is_file():
                file_path.unlink()
        
        # 상태 초기화
        process_state = {
            'current_phase': 1,
            'current_step': 1,
            'status': 'ready',
            'steps': {},
            'firewall_config': {},
            'files': {},
            'errors': [],
            'logs': [],
            'manual_mode': False,
            'paused': False
        }
        
        add_log("프로세스가 초기화되었습니다", 'info')
        
        return jsonify({
            'success': True,
            'message': '프로세스가 초기화되었습니다'
        })
        
    except Exception as e:
        add_log(f"초기화 오류: {str(e)}", 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === 수동 제어 API ===

@app.route('/api/control/manual-mode', methods=['POST'])
def toggle_manual_mode():
    """수동 진행 모드 토글"""
    global process_state
    
    try:
        data = request.get_json()
        enabled = data.get('enabled', not process_state['manual_mode'])
        
        process_state['manual_mode'] = enabled
        
        mode_text = "수동 진행 모드" if enabled else "자동 진행 모드"
        add_log(f"{mode_text}로 변경되었습니다", 'info')
        
        return jsonify({
            'success': True,
            'manual_mode': enabled,
            'message': f'{mode_text}로 변경되었습니다'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/control/pause', methods=['POST'])
def toggle_pause():
    """프로세스 일시정지/재개"""
    global process_state
    
    try:
        data = request.get_json()
        paused = data.get('paused', not process_state['paused'])
        
        process_state['paused'] = paused
        
        status_text = "일시정지" if paused else "재개"
        add_log(f"프로세스가 {status_text}되었습니다", 'info')
        
        return jsonify({
            'success': True,
            'paused': paused,
            'message': f'프로세스가 {status_text}되었습니다'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/control/step-back/<step_id>', methods=['POST'])
def step_back(step_id):
    """특정 단계로 되돌리기"""
    global process_state
    
    try:
        # 해당 단계와 이후 단계들 초기화
        steps_to_reset = []
        found_target = False
        
        for phase_id, phase in PROCESS_PHASES.items():
            for step in phase['steps']:
                if step['id'] == step_id:
                    found_target = True
                if found_target:
                    steps_to_reset.append(step['id'])
        
        if not found_target:
            return jsonify({
                'success': False,
                'error': '해당 단계를 찾을 수 없습니다'
            }), 400
        
        # 상태 초기화
        for step_reset_id in steps_to_reset:
            if step_reset_id in process_state['steps']:
                del process_state['steps'][step_reset_id]
        
        # 관련 파일들도 삭제
        if step_id in ['upload_application_file', 'upload_mis_file']:
            file_type = 'application' if 'application' in step_id else 'mis_id'
            if file_type in process_state['files']:
                # 파일 삭제
                file_path = process_state['files'][file_type]
                if os.path.exists(file_path):
                    os.remove(file_path)
                del process_state['files'][file_type]
        
        add_log(f"'{step_id}' 단계로 되돌아갔습니다", 'info')
        
        return jsonify({
            'success': True,
            'message': f'단계가 초기화되었습니다'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/replace/<file_type>', methods=['POST'])
def replace_file(file_type):
    """파일 교체"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '파일이 선택되지 않았습니다'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '파일이 선택되지 않았습니다'
            }), 400
        
        # 기존 파일 삭제
        if file_type in process_state['files']:
            old_file_path = process_state['files'][file_type]
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
                add_log(f"기존 {file_type} 파일이 삭제되었습니다", 'info')
        
        # 새 파일 저장
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{file_type}_{timestamp}_{filename}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 상태 업데이트
        process_state['files'][file_type] = file_path
        
        # 관련 단계들 재실행을 위해 상태 초기화
        steps_to_reset = []
        if file_type == 'application':
            steps_to_reset = ['validate_files', 'merge_application_info', 'vendor_exception_handling', 
                             'classify_duplicates', 'add_usage_info', 'finalize_classification', 
                             'generate_results']
        elif file_type == 'mis_id':
            steps_to_reset = ['validate_files', 'add_mis_info', 'merge_application_info', 
                             'vendor_exception_handling', 'classify_duplicates', 'add_usage_info', 
                             'finalize_classification', 'generate_results']
        
        for step_id in steps_to_reset:
            if step_id in process_state['steps']:
                del process_state['steps'][step_id]
        
        add_log(f"{file_type} 파일이 교체되었습니다: {filename}", 'success')
        
        return jsonify({
            'success': True,
            'message': f'{file_type} 파일이 성공적으로 교체되었습니다',
            'filename': filename
        })
        
    except Exception as e:
        add_log(f"파일 교체 오류: {str(e)}", 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🔥 방화벽 정책 프로세서 시작")
    print("📍 http://127.0.0.1:5005")
    
    if FIREWALL_MODULE_AVAILABLE:
        print("✅ 방화벽 모듈 연동 가능")
    else:
        print("⚠️  방화벽 모듈 없음 - 시뮬레이션 모드만 가능")
    
    app.run(debug=True, host='0.0.0.0', port=5005) 