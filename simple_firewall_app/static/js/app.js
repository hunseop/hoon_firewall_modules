/**
 * 방화벽 정책 정리 프로세스 - SPA JavaScript
 */

class FirewallProcessApp {
    constructor() {
        this.phases = {};
        this.currentState = {};
        this.statusUpdateInterval = null;
        this.currentFileType = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialStatus();
        this.startStatusUpdates();
    }

    setupEventListeners() {
        // 초기화 버튼
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.resetProcess();
        });

        // 로그 지우기
        document.getElementById('clear-logs-btn').addEventListener('click', () => {
            this.clearLogs();
        });

        // 방화벽 설정 저장
        document.getElementById('save-firewall-config').addEventListener('click', () => {
            this.saveFirewallConfig();
        });

        // 파일 업로드
        document.getElementById('file-input').addEventListener('change', (e) => {
            const uploadBtn = document.getElementById('upload-file-btn');
            uploadBtn.disabled = !e.target.files.length;
        });

        document.getElementById('upload-file-btn').addEventListener('click', () => {
            this.uploadFile();
        });
    }

    async loadInitialStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                // 첫 로드인지 확인
                const isFirstLoad = !this.phases || Object.keys(this.phases).length === 0;
                
                if (isFirstLoad) {
                    // 첫 로드시 전체 렌더링
                    this.phases = data.phases;
                    this.currentState = data.state;
                    this.renderPhases();
                } else {
                    // 상태가 실제로 변경되었는지 확인
                    const hasStateChanged = this.hasStateChanged(data.state);
                    const hasLogsChanged = this.hasLogsChanged(data.state.logs);
                    
                    this.phases = data.phases;
                    this.currentState = data.state;
                    
                    // 변경된 경우에만 업데이트
                    if (hasStateChanged) {
                        this.updateStepsOnly();
                    }
                    
                    if (hasLogsChanged) {
                        this.updateLogs();
                    }
                }
                
                this.updateCurrentStatus();
            }
        } catch (error) {
            console.error('상태 로드 오류:', error);
        }
    }

    hasStateChanged(newState) {
        // 기존 상태와 비교해서 변경되었는지 확인
        const currentStepsJson = JSON.stringify(this.currentState.steps || {});
        const newStepsJson = JSON.stringify(newState.steps || {});
        return currentStepsJson !== newStepsJson;
    }

    hasLogsChanged(newLogs) {
        const currentLogsLength = (this.currentState.logs || []).length;
        const newLogsLength = (newLogs || []).length;
        return currentLogsLength !== newLogsLength;
    }

    startStatusUpdates() {
        // 5초마다 상태 업데이트
        this.statusUpdateInterval = setInterval(() => {
            this.loadInitialStatus();
        }, 5000); // 5초로 늘림
    }

    renderPhases() {
        const container = document.getElementById('phases-container');
        container.innerHTML = '';

        Object.entries(this.phases).forEach(([phaseId, phase]) => {
            const phaseElement = this.createPhaseElement(phaseId, phase);
            container.appendChild(phaseElement);
        });
    }

    updateStepsOnly() {
        // 기존 DOM 요소를 찾아서 상태만 업데이트
        Object.entries(this.phases).forEach(([phaseId, phase]) => {
            phase.steps.forEach(step => {
                this.updateSingleStep(step);
            });
            this.updatePhaseStatus(phaseId, phase);
        });
    }

    updateSingleStep(step) {
        const stepElement = document.getElementById(`step-${step.id}`);
        if (!stepElement) return;

        const stepStatus = this.getStepStatus(step.id);
        const stepData = this.currentState.steps[step.id] || {};

        // 클래스 업데이트
        stepElement.className = `step-item ${stepStatus}`;

        // 상태 아이콘 업데이트
        const statusIcon = stepElement.querySelector('.status-icon');
        if (statusIcon) {
            statusIcon.className = `status-icon ${stepStatus}`;
            statusIcon.innerHTML = this.getStatusIcon(stepStatus);
        }

        // 결과 정보 업데이트
        const stepInfo = stepElement.querySelector('.step-info');
        if (stepInfo) {
            // 기존 결과/오류 제거
            const existingResult = stepInfo.querySelector('.step-result');
            const existingError = stepInfo.querySelector('.alert-danger');
            if (existingResult) existingResult.remove();
            if (existingError) existingError.remove();

            // 새 결과/오류 추가
            if (stepData.result) {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'step-result';
                resultDiv.innerHTML = this.formatStepResult(stepData.result);
                stepInfo.appendChild(resultDiv);
            }

            if (stepData.error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    오류: ${stepData.error}
                `;
                stepInfo.appendChild(errorDiv);
            }
        }

        // 액션 버튼 업데이트
        const stepActions = stepElement.querySelector('.step-actions');
        if (stepActions) {
            stepActions.innerHTML = this.getStepActions(step, stepStatus);
        }
    }

    updatePhaseStatus(phaseId, phase) {
        const phaseElement = document.getElementById(`phase-${phaseId}`);
        if (!phaseElement) return;

        const phaseStatus = this.calculatePhaseStatus(phase.steps);
        
        // Phase 클래스 업데이트
        phaseElement.className = `phase-section fade-in ${phaseStatus}`;

        // Phase 헤더 업데이트
        const phaseHeader = phaseElement.querySelector('.phase-header');
        if (phaseHeader) {
            phaseHeader.className = `phase-header ${phaseStatus}`;
            
            // 배지 업데이트
            const badge = phaseHeader.querySelector('.badge');
            if (badge) {
                phaseHeader.querySelector('div:last-child').innerHTML = this.getPhaseStatusBadge(phaseStatus);
            }
        }
    }

    createPhaseElement(phaseId, phase) {
        const phaseDiv = document.createElement('div');
        phaseDiv.className = 'phase-section fade-in';
        phaseDiv.id = `phase-${phaseId}`;

        // Phase 상태 계산
        const phaseStatus = this.calculatePhaseStatus(phase.steps);
        phaseDiv.classList.add(phaseStatus);

        phaseDiv.innerHTML = `
            <div class="phase-header ${phaseStatus}">
                <div class="phase-title">
                    <i class="fas fa-${this.getPhaseIcon(phaseId)} phase-icon"></i>
                    ${phase.name}
                </div>
                <div>
                    ${this.getPhaseStatusBadge(phaseStatus)}
                </div>
            </div>
            <div class="phase-body">
                ${phase.steps.map(step => this.createStepElement(step)).join('')}
            </div>
        `;

        return phaseDiv;
    }

    createStepElement(step) {
        const stepStatus = this.getStepStatus(step.id);
        const stepData = this.currentState.steps[step.id] || {};

        return `
            <div class="step-item ${stepStatus}" id="step-${step.id}">
                <div class="step-content">
                    <div class="step-info">
                        <div class="step-title">
                            <span class="status-icon ${stepStatus}">
                                ${this.getStatusIcon(stepStatus)}
                            </span>
                            ${step.name}
                        </div>
                        <div class="step-description">
                            ${step.description}
                        </div>
                        ${stepData.result ? `
                            <div class="step-result">
                                ${this.formatStepResult(stepData.result)}
                            </div>
                        ` : ''}
                        ${stepData.error ? `
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-triangle"></i>
                                오류: ${stepData.error}
                            </div>
                        ` : ''}
                    </div>
                    <div class="step-actions">
                        ${this.getStepActions(step, stepStatus)}
                    </div>
                </div>
            </div>
        `;
    }

    getStepActions(step, stepStatus) {
        const actions = [];

        if (step.requires_user_input) {
            if (step.id === 'firewall_config') {
                if (stepStatus === 'pending') {
                    actions.push(`
                        <button class="btn btn-primary" 
                                onclick="app.openFirewallConfig()">
                            <i class="fas fa-cog"></i>
                            설정
                        </button>
                    `);
                }
            } else if (step.file_type) {
                if (stepStatus === 'pending') {
                    actions.push(`
                        <button class="btn btn-primary" 
                                onclick="app.openFileUpload('${step.file_type}', '${step.name}')">
                            <i class="fas fa-upload"></i>
                            업로드
                        </button>
                    `);
                } else if (stepStatus === 'completed') {
                    actions.push(`
                        <button class="btn btn-outline-info btn-sm" 
                                onclick="app.previewFile('${step.file_type}')">
                            <i class="fas fa-eye"></i>
                            미리보기
                        </button>
                    `);
                }
            }
        } else {
            if (stepStatus === 'pending' && this.canExecuteStep(step.id)) {
                actions.push(`
                    <button class="btn btn-success" 
                            onclick="app.executeStep('${step.id}')">
                        <i class="fas fa-play"></i>
                        실행
                    </button>
                `);
            } else if (stepStatus === 'running') {
                actions.push(`
                    <button class="btn btn-outline-secondary" disabled>
                        <i class="fas fa-spinner fa-spin"></i>
                        실행 중
                    </button>
                `);
            } else if (stepStatus === 'completed') {
                actions.push(`
                    <button class="btn btn-outline-success btn-sm" 
                            onclick="app.executeStep('${step.id}')">
                        <i class="fas fa-redo"></i>
                        재실행
                    </button>
                `);
            } else if (stepStatus === 'error') {
                actions.push(`
                    <button class="btn btn-warning" 
                            onclick="app.executeStep('${step.id}')">
                        <i class="fas fa-redo"></i>
                        재시도
                    </button>
                `);
            }
        }

        return actions.join('');
    }

    canExecuteStep(stepId) {
        // 이전 단계들이 완료되었는지 확인
        const allSteps = this.getAllStepsInOrder();
        const currentIndex = allSteps.findIndex(s => s.id === stepId);
        
        for (let i = 0; i < currentIndex; i++) {
            const prevStep = allSteps[i];
            const prevStatus = this.getStepStatus(prevStep.id);
            if (prevStatus !== 'completed') {
                return false;
            }
        }
        
        return true;
    }

    getAllStepsInOrder() {
        const steps = [];
        Object.values(this.phases).forEach(phase => {
            steps.push(...phase.steps);
        });
        return steps;
    }

    getStepStatus(stepId) {
        const stepData = this.currentState.steps[stepId];
        if (!stepData) return 'pending';
        return stepData.status;
    }

    calculatePhaseStatus(steps) {
        const statuses = steps.map(step => this.getStepStatus(step.id));
        
        if (statuses.every(s => s === 'completed')) return 'completed';
        if (statuses.some(s => s === 'running')) return 'active';
        if (statuses.some(s => s === 'error')) return 'error';
        if (statuses.some(s => s === 'completed')) return 'active';
        
        return 'pending';
    }

    getPhaseIcon(phaseId) {
        const icons = {
            1: 'cog',
            2: 'download',
            3: 'search',
            4: 'file-upload',
            5: 'puzzle-piece',
            6: 'check-circle'
        };
        return icons[phaseId] || 'circle';
    }

    getPhaseStatusBadge(status) {
        const badges = {
            pending: '<span class="status-badge" style="background: var(--bg-secondary); color: var(--text-muted);">대기</span>',
            active: '<span class="status-badge" style="background: var(--accent-color); color: white;">진행</span>',
            completed: '<span class="status-badge" style="background: var(--success-color); color: white;">완료</span>',
            error: '<span class="status-badge" style="background: var(--danger-color); color: white;">오류</span>'
        };
        return badges[status] || '';
    }

    getStatusIcon(status) {
        const icons = {
            pending: '<i class="fas fa-clock"></i>',
            running: '<i class="fas fa-spinner fa-spin"></i>',
            completed: '<i class="fas fa-check"></i>',
            error: '<i class="fas fa-exclamation"></i>'
        };
        return icons[status] || '';
    }

    formatStepResult(result) {
        if (typeof result === 'object') {
            // 멀티 장비 결과인 경우 특별 포맷
            if (result.primary_count !== undefined || result.secondary_count !== undefined) {
                let parts = [];
                
                if (result.policies_count !== undefined) {
                    parts.push(`총 정책: ${result.policies_count}개`);
                } else if (result.usage_records !== undefined) {
                    parts.push(`총 사용이력: ${result.usage_records}개`);
                }
                
                if (result.primary_count !== undefined) {
                    parts.push(`Primary: ${result.primary_count}개`);
                }
                
                if (result.secondary_count !== undefined && result.secondary_count > 0) {
                    parts.push(`Secondary: ${result.secondary_count}개`);
                }
                
                if (result.duplicate_removed !== undefined && result.duplicate_removed > 0) {
                    parts.push(`중복제거: ${result.duplicate_removed}개`);
                }
                
                return parts.join(' | ');
            }
            
            // 일반 결과 포맷
            return Object.entries(result)
                .map(([key, value]) => `${key}: ${value}`)
                .join(' | ');
        }
        return result;
    }

    updateCurrentStatus() {
        const statusDiv = document.getElementById('current-status');
        const runningSteps = Object.entries(this.currentState.steps)
            .filter(([_, data]) => data.status === 'running');
        
        if (runningSteps.length > 0) {
            const stepId = runningSteps[0][0];
            const step = this.findStepById(stepId);
            statusDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                    <strong>실행 중:</strong> ${step ? step.name : stepId}
                </div>
            `;
        } else {
            const nextStep = this.getNextPendingStep();
            if (nextStep) {
                statusDiv.innerHTML = `
                    <div>
                        <strong>다음 단계:</strong> ${nextStep.name}
                        ${nextStep.requires_user_input ? 
                            '<span class="badge bg-warning ms-2">사용자 입력 필요</span>' : 
                            '<span class="badge bg-info ms-2">자동 실행 가능</span>'
                        }
                    </div>
                `;
            } else {
                statusDiv.innerHTML = '<div class="text-success"><strong>모든 작업 완료!</strong></div>';
            }
        }
    }

    findStepById(stepId) {
        for (const phase of Object.values(this.phases)) {
            const step = phase.steps.find(s => s.id === stepId);
            if (step) return step;
        }
        return null;
    }

    getNextPendingStep() {
        const allSteps = this.getAllStepsInOrder();
        return allSteps.find(step => this.getStepStatus(step.id) === 'pending');
    }

    updateLogs() {
        const logsContainer = document.getElementById('logs-container');
        const logs = this.currentState.logs || [];
        
        logsContainer.innerHTML = logs.map(log => `
            <div class="log-entry">
                <span class="log-timestamp">[${log.timestamp}]</span>
                <span class="log-level-${log.level}">${log.message}</span>
            </div>
        `).join('');
        
        // 자동 스크롤
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    // 액션 메서드들
    openFirewallConfig() {
        const modal = new bootstrap.Modal(document.getElementById('firewall-config-modal'));
        modal.show();
    }

    async saveFirewallConfig() {
        const form = document.getElementById('firewall-config-form');
        const formData = new FormData(form);
        const config = Object.fromEntries(formData);

        try {
            const response = await fetch('/api/firewall/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('firewall-config-modal')).hide();
                this.autoExecuteNextSteps();
            } else {
                alert('오류: ' + result.error);
            }
        } catch (error) {
            alert('연결 오류: ' + error.message);
        }
    }

    openFileUpload(fileType, stepName) {
        this.currentFileType = fileType;
        document.getElementById('file-upload-title').textContent = stepName;
        document.getElementById('file-input').value = '';
        document.getElementById('upload-file-btn').disabled = true;
        
        const modal = new bootstrap.Modal(document.getElementById('file-upload-modal'));
        modal.show();
    }

    async uploadFile() {
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('파일을 선택해주세요.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`/api/file/upload/${this.currentFileType}`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('file-upload-modal')).hide();
                this.autoExecuteNextSteps();
            } else {
                alert('업로드 오류: ' + result.error);
            }
        } catch (error) {
            alert('업로드 오류: ' + error.message);
        }
    }

    async executeStep(stepId) {
        try {
            const response = await fetch(`/api/step/execute/${stepId}`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                // 자동으로 다음 단계들 실행
                setTimeout(() => {
                    this.autoExecuteNextSteps();
                }, 1000);
            }
        } catch (error) {
            console.error('단계 실행 오류:', error);
        }
    }

    autoExecuteNextSteps() {
        // 자동 실행 가능한 다음 단계들을 연속으로 실행
        setTimeout(() => {
            const nextStep = this.getNextAutoExecutableStep();
            if (nextStep) {
                this.executeStep(nextStep.id);
            }
        }, 2000);
    }

    getNextAutoExecutableStep() {
        const allSteps = this.getAllStepsInOrder();
        const nextStep = allSteps.find(step => {
            const status = this.getStepStatus(step.id);
            return status === 'pending' && 
                   !step.requires_user_input && 
                   step.auto_proceed && 
                   this.canExecuteStep(step.id);
        });
        
        return nextStep;
    }

    async previewFile(fileType) {
        try {
            const response = await fetch(`/api/file/preview/${fileType}`);
            const result = await response.json();
            
            if (result.success) {
                this.showFilePreview(result);
            } else {
                alert('미리보기 오류: ' + result.error);
            }
        } catch (error) {
            alert('미리보기 오류: ' + error.message);
        }
    }

    showFilePreview(data) {
        const content = document.getElementById('file-preview-content');
        content.innerHTML = `
            <div class="mb-3">
                <strong>총 행 수:</strong> ${data.total_rows}
            </div>
            <div class="table-responsive">
                <table class="table table-sm preview-table">
                    <thead>
                        <tr>
                            ${data.columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.data.map(row => `
                            <tr>
                                ${data.columns.map(col => `<td>${row[col] || ''}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('file-preview-modal'));
        modal.show();
    }

    async resetProcess() {
        if (confirm('모든 프로세스를 초기화하시겠습니까?')) {
            try {
                const response = await fetch('/api/reset', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    location.reload();
                }
            } catch (error) {
                console.error('초기화 오류:', error);
            }
        }
    }

    clearLogs() {
        document.getElementById('logs-container').innerHTML = '';
    }
}

// 앱 인스턴스 생성
let app;

document.addEventListener('DOMContentLoaded', function() {
    app = new FirewallProcessApp();
}); 