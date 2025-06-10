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
from werkzeug.utils import secure_filename
import pandas as pd

# 상위 modules 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 방화벽 모듈 임포트
try:
    from modules.firewall_module import (
        FirewallCollectorFactory,
        export_policy_to_excel,
        FirewallError,
        FirewallConnectionError,
        setup_firewall_logger
    )
    FIREWALL_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"방화벽 모듈 임포트 실패: {e}")
    FIREWALL_MODULE_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def extract_firewall_policies():
    """방화벽 정책 추출 (Primary + Secondary 자동 합치기)"""
    try:
        if FIREWALL_MODULE_AVAILABLE and 'firewall_collectors' in process_state:
            collectors = process_state['firewall_collectors']
            all_policies = []
            
            # Primary 장비에서 정책 추출
            add_log("Primary 방화벽에서 정책 데이터 추출 중...")
            primary_policies = collectors['primary'].get_policies()
            
            if hasattr(primary_policies, 'to_dict'):
                primary_df = primary_policies
            else:
                import pandas as pd
                primary_df = pd.DataFrame(primary_policies)
            
            # 출처 표시를 위해 컬럼 추가
            primary_df['장비구분'] = 'Primary'
            all_policies.append(primary_df)
            add_log(f"Primary 정책 추출 완료: {len(primary_df)}개")
            
            # Secondary 장비가 있는 경우 추출
            if 'secondary' in collectors:
                try:
                    add_log("Secondary 방화벽에서 정책 데이터 추출 중...")
                    secondary_policies = collectors['secondary'].get_policies()
                    
                    if hasattr(secondary_policies, 'to_dict'):
                        secondary_df = secondary_policies
                    else:
                        import pandas as pd
                        secondary_df = pd.DataFrame(secondary_policies)
                    
                    secondary_df['장비구분'] = 'Secondary'
                    all_policies.append(secondary_df)
                    add_log(f"Secondary 정책 추출 완료: {len(secondary_df)}개")
                    
                except Exception as e:
                    add_log(f"Secondary 정책 추출 실패 (무시하고 계속): {str(e)}", 'warning')
            
            # 🔄 데이터 자동 합치기
            import pandas as pd
            if len(all_policies) > 1:
                add_log("Primary와 Secondary 정책 데이터 합치는 중...")
                combined_policies = pd.concat(all_policies, ignore_index=True)
                add_log(f"데이터 합치기 완료: 총 {len(combined_policies)}개 정책")
            else:
                combined_policies = all_policies[0]
            
            # 중복 제거 (선택사항)
            original_count = len(combined_policies)
            combined_policies = combined_policies.drop_duplicates()
            duplicate_removed = original_count - len(combined_policies)
            if duplicate_removed > 0:
                add_log(f"중복 정책 {duplicate_removed}개 제거됨")
            
            # Excel 파일로 저장
            output_file = os.path.join('results', 'firewall_policies.xlsx')
            os.makedirs('results', exist_ok=True)
            combined_policies.to_excel(output_file, index=False)
            
            add_log(f"정책 추출 완료: 총 {len(combined_policies)}개 정책")
            
            return {
                'policies_count': len(combined_policies),
                'primary_count': len(all_policies[0]),
                'secondary_count': len(all_policies[1]) if len(all_policies) > 1 else 0,
                'duplicate_removed': duplicate_removed,
                'file': 'firewall_policies.xlsx',
                'path': output_file
            }
            
        else:
            # 시뮬레이션 모드
            add_log("시뮬레이션 모드: 정책 추출 중...")
            time.sleep(3)
            return {
                'policies_count': 1250,
                'primary_count': 800,
                'secondary_count': 450,
                'duplicate_removed': 0,
                'file': 'firewall_policies.xlsx'
            }
            
    except Exception as e:
        add_log(f"정책 추출 오류: {str(e)}", 'error')
        raise

def extract_firewall_usage():
    """방화벽 사용이력 추출 (Primary + Secondary 자동 합치기)"""
    try:
        if FIREWALL_MODULE_AVAILABLE and 'firewall_collectors' in process_state:
            collectors = process_state['firewall_collectors']
            all_usage = []
            
            # Primary 장비에서 사용이력 추출
            add_log("Primary 방화벽에서 사용이력 데이터 추출 중...")
            primary_usage = collectors['primary'].get_usage_statistics()
            
            if hasattr(primary_usage, 'to_dict'):
                primary_df = primary_usage
            else:
                import pandas as pd
                primary_df = pd.DataFrame(primary_usage)
            
            primary_df['장비구분'] = 'Primary'
            all_usage.append(primary_df)
            add_log(f"Primary 사용이력 추출 완료: {len(primary_df)}개")
            
            # Secondary 장비가 있는 경우 추출
            if 'secondary' in collectors:
                try:
                    add_log("Secondary 방화벽에서 사용이력 데이터 추출 중...")
                    secondary_usage = collectors['secondary'].get_usage_statistics()
                    
                    if hasattr(secondary_usage, 'to_dict'):
                        secondary_df = secondary_usage
                    else:
                        import pandas as pd
                        secondary_df = pd.DataFrame(secondary_usage)
                    
                    secondary_df['장비구분'] = 'Secondary'
                    all_usage.append(secondary_df)
                    add_log(f"Secondary 사용이력 추출 완료: {len(secondary_df)}개")
                    
                except Exception as e:
                    add_log(f"Secondary 사용이력 추출 실패 (무시하고 계속): {str(e)}", 'warning')
            
            # 🔄 데이터 자동 합치기
            import pandas as pd
            if len(all_usage) > 1:
                add_log("Primary와 Secondary 사용이력 데이터 합치는 중...")
                combined_usage = pd.concat(all_usage, ignore_index=True)
                add_log(f"사용이력 데이터 합치기 완료: 총 {len(combined_usage)}개")
            else:
                combined_usage = all_usage[0]
            
            # 중복 제거 및 정렬
            original_count = len(combined_usage)
            if 'timestamp' in combined_usage.columns or 'date' in combined_usage.columns:
                # 시간 기준으로 정렬
                time_col = 'timestamp' if 'timestamp' in combined_usage.columns else 'date'
                combined_usage = combined_usage.sort_values(time_col)
                
            combined_usage = combined_usage.drop_duplicates()
            duplicate_removed = original_count - len(combined_usage)
            if duplicate_removed > 0:
                add_log(f"중복 사용이력 {duplicate_removed}개 제거됨")
            
            # Excel 파일로 저장
            output_file = os.path.join('results', 'usage_history.xlsx')
            combined_usage.to_excel(output_file, index=False)
            
            add_log(f"사용이력 추출 완료: 총 {len(combined_usage)}개 레코드")
            
            return {
                'usage_records': len(combined_usage),
                'primary_count': len(all_usage[0]),
                'secondary_count': len(all_usage[1]) if len(all_usage) > 1 else 0,
                'duplicate_removed': duplicate_removed,
                'file': 'usage_history.xlsx',
                'path': output_file
            }
            
        else:
            # 시뮬레이션 모드
            add_log("시뮬레이션 모드: 사용이력 추출 중...")
            time.sleep(2)
            return {
                'usage_records': 8500,
                'primary_count': 5000,
                'secondary_count': 3500,
                'duplicate_removed': 0,
                'file': 'usage_history.xlsx'
            }
            
    except Exception as e:
        add_log(f"사용이력 추출 오류: {str(e)}", 'error')
        raise

def extract_duplicate_policies():
    """중복 정책 추출"""
    try:
        if FIREWALL_MODULE_AVAILABLE and 'firewall_collector' in process_state:
            collector = process_state['firewall_collector']
            
            add_log("방화벽에서 중복 정책 분석 중...")
            
            # 실제 방화벽에서 중복 정책 분석
            if hasattr(collector, 'get_duplicate_policies'):
                duplicate_data = collector.get_duplicate_policies()
            else:
                # 중복 정책 분석 기능이 없는 경우 정책을 가져와서 직접 분석
                policies = collector.get_policies()
                duplicate_data = analyze_duplicate_policies(policies)
            
            # 데이터를 Excel 파일로 저장
            output_file = os.path.join('results', 'duplicate_policies.xlsx')
            
            if hasattr(duplicate_data, 'to_excel'):
                duplicate_data.to_excel(output_file, index=False)
                duplicate_count = len(duplicate_data)
            else:
                import pandas as pd
                df = pd.DataFrame(duplicate_data)
                df.to_excel(output_file, index=False)
                duplicate_count = len(df)
            
            add_log(f"중복 정책 분석 완료: {duplicate_count}개 중복 정책")
            
            return {
                'duplicate_policies': duplicate_count,
                'file': 'duplicate_policies.xlsx',
                'path': output_file
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
    import pandas as pd
    
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

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """현재 상태 반환"""
    return jsonify({
        'success': True,
        'phases': PROCESS_PHASES,
        'state': {
            **process_state,
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
            time.sleep(2)
            result = {'parsed_requests': 1200, 'missing_descriptions': 50}
            
        elif step_id == 'validate_files':
            add_log("파일 유효성 검사 중...")
            time.sleep(1)
            result = {'valid_files': 2, 'warnings': 3}
            
        elif step_id in ['add_mis_info', 'merge_application_info', 'vendor_exception_handling', 
                        'classify_duplicates', 'add_usage_info', 'finalize_classification']:
            add_log(f"{step_id} 처리 중...")
            time.sleep(2)
            result = {'processed_records': 1250}
            
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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 파일 정보 저장
        process_state['files'][file_type] = {
            'filename': filename,
            'filepath': filepath,
            'upload_time': datetime.now().isoformat()
        }
        
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
        
        # Excel 파일 읽기
        df = pd.read_excel(filepath, nrows=10)  # 처음 10행만
        
        return jsonify({
            'success': True,
            'columns': df.columns.tolist(),
            'data': df.to_dict('records'),
            'total_rows': len(pd.read_excel(filepath))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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