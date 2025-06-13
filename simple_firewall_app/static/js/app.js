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

        // 수동 모드 토글
        document.getElementById('manual-mode-btn').addEventListener('click', () => {
            this.toggleManualMode();
        });

        // 일시정지/재개
        document.getElementById('pause-btn').addEventListener('click', () => {
            this.togglePause();
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

        const nextBtn = document.getElementById('next-step-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.executeNextStep();
            });
        }
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
                    this.updateControlButtons();
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
                    
                    this.updateControlButtons();
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
        // 1초마다 상태 업데이트
        this.statusUpdateInterval = setInterval(() => {
            this.loadInitialStatus();
        }, 1000);
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
        let actions = '';
        
        // 기본 실행/업로드 버튼
        if (step.requires_user_input) {
            if (step.file_type) {
                // 파일 업로드 단계
                actions += `
                    <button class="btn btn-primary btn-sm me-2" onclick="app.openFileUpload('${step.file_type}', '${step.name}')">
                        <i class="fas fa-upload"></i> 파일 업로드
                    </button>
                `;
                
                // 파일 교체 버튼 (파일이 이미 업로드된 경우)
                if (stepStatus === 'completed' && step.allow_replace) {
                    actions += `
                        <button class="btn btn-warning btn-sm me-2" onclick="app.replaceFile('${step.file_type}')" title="파일 교체">
                            <i class="fas fa-exchange-alt"></i> 파일 교체
                        </button>
                    `;
                }
            } else {
                // 일반 설정 단계
                actions += `
                    <button class="btn btn-primary btn-sm me-2" onclick="app.openFirewallConfig()">
                        <i class="fas fa-cog"></i> 설정
                    </button>
                `;
            }
        } else {
            // 자동 실행 단계
            const canExecute = this.canExecuteStep(step.id);
            const isRunning = stepStatus === 'running';
            const isCompleted = stepStatus === 'completed';
            const isPaused = this.currentState.paused;
            const isManualMode = this.currentState.manual_mode;
            
            // 실행 버튼 (수동 모드이거나 일시정지 상태에서만 수동 실행 가능)
            if ((isManualMode || isPaused) && canExecute && !isRunning && !isCompleted) {
                actions += `
                    <button class="btn btn-success btn-sm me-2" onclick="app.executeStep('${step.id}')">
                        <i class="fas fa-play"></i> 실행
                    </button>
                `;
            }
        }
        
        // 되돌리기 버튼 (완료된 단계에 대해)
        if (stepStatus === 'completed' && step.allow_manual) {
            actions += `
                <button class="btn btn-outline-secondary btn-sm me-2" onclick="app.stepBack('${step.id}')" title="이 단계로 되돌리기">
                    <i class="fas fa-undo"></i> 되돌리기
                </button>
            `;
        }
        
        // 미리보기/다운로드 버튼 (업로드 단계)
        if (step.file_type && stepStatus === 'completed') {
            actions += `
                <button class="btn btn-info btn-sm" onclick="app.previewFile('${step.file_type}')" title="파일 미리보기">
                    <i class="fas fa-eye"></i> 미리보기
                </button>
                <button class="btn btn-secondary btn-sm ms-2" onclick="app.downloadFile('${step.file_type}')" title="파일 다운로드">
                    <i class="fas fa-download"></i> 다운로드
                </button>
            `;
        } else if (stepStatus === 'completed' && this.hasResultFile(step.id)) {
            actions += `
                <button class="btn btn-secondary btn-sm" onclick="app.downloadStepFile('${step.id}')" title="파일 다운로드">
                    <i class="fas fa-download"></i> 다운로드
                </button>
            `;
        }
        
        return actions;
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

    hasResultFile(stepId) {
        const stepData = this.currentState.steps[stepId];
        if (!stepData || stepData.status !== 'completed') return false;
        const r = stepData.result || {};
        if (r.file) return true;
        if (Array.isArray(r.files) && r.files.length) return true;
        if (Array.isArray(r.policies) && r.policies.length) return true;
        if (Array.isArray(r.usage) && r.usage.length) return true;
        if (Array.isArray(r.duplicate_policies) && r.duplicate_policies.length) return true;
        return false;
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
        const input = document.getElementById('file-input');
        input.value = '';
        document.getElementById('upload-file-btn').disabled = true;
        const help = document.getElementById('file-upload-help');

        if (fileType === 'mis_id') {
            input.accept = '.csv';
            help.innerHTML = '<i class="fas fa-info-circle"></i> CSV 파일(.csv)만 업로드 가능합니다.';
        } else {
            input.accept = '.xlsx,.xls';
            help.innerHTML = '<i class="fas fa-info-circle"></i> Excel 파일(.xlsx, .xls)만 업로드 가능합니다.';
        }

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
                await this.loadInitialStatus();
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
                await this.loadInitialStatus();
                setTimeout(() => {
                    this.autoExecuteNextSteps();
                }, 1000);
            }
        } catch (error) {
            console.error('단계 실행 오류:', error);
        }
    }

    async executeNextStep() {
        const nextStep = this.getNextPendingStep();
        if (!nextStep) {
            alert('더 이상 실행할 단계가 없습니다.');
            return;
        }
        if (!this.canExecuteStep(nextStep.id)) {
            alert('이전 단계가 완료되지 않았습니다.');
            return;
        }
        await this.executeStep(nextStep.id);
    }

    autoExecuteNextSteps() {
        // 수동 모드이거나 일시정지 상태면 자동 실행 안함
        if (this.currentState.manual_mode || this.currentState.paused) {
            return;
        }
        
        setTimeout(() => {
            const nextStep = this.getNextAutoExecutableStep();
            if (nextStep) {
                this.executeStep(nextStep.id);
            }
        }, 1000);
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
        this.currentState.logs = [];
    }
    
    // === 수동 제어 기능 ===
    
    async toggleManualMode() {
        try {
            const response = await fetch('/api/control/manual-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    enabled: !this.currentState.manual_mode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentState.manual_mode = data.manual_mode;
                this.updateManualModeButton();
                
                // 모든 단계 버튼 상태 업데이트
                this.updateStepsOnly();
                
                alert(data.message);
            } else {
                alert('오류: ' + data.error);
            }
        } catch (error) {
            console.error('수동 모드 토글 오류:', error);
            alert('수동 모드 변경 중 오류가 발생했습니다.');
        }
    }
    
    async togglePause() {
        try {
            const response = await fetch('/api/control/pause', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    paused: !this.currentState.paused
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentState.paused = data.paused;
                this.updatePauseButton();
                
                alert(data.message);
            } else {
                alert('오류: ' + data.error);
            }
        } catch (error) {
            console.error('일시정지 토글 오류:', error);
            alert('일시정지 상태 변경 중 오류가 발생했습니다.');
        }
    }
    
    async stepBack(stepId) {
        if (!confirm('이 단계로 되돌아가면 이후 모든 진행사항이 삭제됩니다. 계속하시겠습니까?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/control/step-back/${stepId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(data.message);
                // 상태 새로고침
                await this.loadInitialStatus();
            } else {
                alert('오류: ' + data.error);
            }
        } catch (error) {
            console.error('단계 되돌리기 오류:', error);
            alert('단계 되돌리기 중 오류가 발생했습니다.');
        }
    }
    
    async replaceFile(fileType) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.xlsx,.xls';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            if (!confirm(`${fileType} 파일을 교체하시겠습니까? 관련 처리 단계들이 재실행됩니다.`)) {
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`/api/file/replace/${fileType}`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(data.message);
                    // 상태 새로고침
                    await this.loadInitialStatus();
                } else {
                    alert('오류: ' + data.error);
                }
            } catch (error) {
                console.error('파일 교체 오류:', error);
                alert('파일 교체 중 오류가 발생했습니다.');
            }
        };
        
        input.click();
    }

    async downloadFile(fileType) {
        window.location.href = `/api/file/download/${fileType}`;
    }

    async downloadStepFile(stepId) {
        window.location.href = `/api/step/download/${stepId}/0`;
    }
    
    updateManualModeButton() {
        const btn = document.getElementById('manual-mode-btn');
        if (this.currentState.manual_mode) {
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-primary');
            btn.innerHTML = '<i class="fas fa-hand-paper"></i> 수동 모드';
        } else {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-primary');
            btn.innerHTML = '<i class="fas fa-play"></i> 자동 모드';
        }
    }
    
    updatePauseButton() {
        const btn = document.getElementById('pause-btn');
        if (this.currentState.paused) {
            btn.classList.remove('btn-outline-warning');
            btn.classList.add('btn-warning');
            btn.innerHTML = '<i class="fas fa-play"></i> 재개';
        } else {
            btn.classList.remove('btn-warning');
            btn.classList.add('btn-outline-warning');
            btn.innerHTML = '<i class="fas fa-pause"></i> 일시정지';
        }
    }

    updateControlButtons() {
        this.updateManualModeButton();
        this.updatePauseButton();

        const nextBtn = document.getElementById('next-step-btn');
        if (nextBtn) {
            if (this.currentState.manual_mode || this.currentState.paused) {
                nextBtn.style.display = 'inline-block';
                const next = this.getNextPendingStep();
                nextBtn.disabled = !next || !this.canExecuteStep(next.id);
            } else {
                nextBtn.style.display = 'none';
            }
        }
    }
}

// 앱 인스턴스 생성
let app;

document.addEventListener('DOMContentLoaded', function() {
    app = new FirewallProcessApp();
}); 