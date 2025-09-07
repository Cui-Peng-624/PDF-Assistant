/**
 * PDF智能分析助手 - 前端应用
 */

class PDFAnalyzer {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.currentFileId = null;
        this.statusInterval = null;
        this.tasks = new Map();
        this.selectedFile = null; // 存储当前选中的文件
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadConfig();
        this.loadTasks();
        this.loadFileList();
    }

    setupEventListeners() {
        // 配置表单提交
        const configForm = document.getElementById('configForm');
        if (configForm) {
            configForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveConfig();
            });
        }

        // 测试连接按钮
        const testBtn = document.getElementById('testConnectionBtn');
        if (testBtn) {
            testBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.testConnection();
            });
        }

        // 文件上传表单提交
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.uploadAndProcess();
            });
        }

        // 设置文件上传监听器
        this.setupFileUploadListeners();
    }

    setupFileUploadListeners() {
        // 文件拖拽上传
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('pdfFile');

        if (fileUploadArea && fileInput) {
            // 先移除所有现有的事件监听器，避免重复绑定
            this.removeFileUploadListeners();
            
            // 使用事件委托，避免重复绑定问题
            fileUploadArea.onclick = () => {
                fileInput.click();
            };
            
            fileInput.onchange = (e) => {
                this.handleFileSelect(e);
            };

            // 拖拽事件
            fileUploadArea.ondragover = (e) => {
                e.preventDefault();
                fileUploadArea.classList.add('dragover');
            };

            fileUploadArea.ondragleave = () => {
                fileUploadArea.classList.remove('dragover');
            };

            fileUploadArea.ondrop = (e) => {
                e.preventDefault();
                fileUploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    this.handleFileSelect({ target: { files: files } });
                }
            };
        }
    }

    removeFileUploadListeners() {
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('pdfFile');

        if (fileUploadArea) {
            // 清空所有事件处理器
            fileUploadArea.onclick = null;
            fileUploadArea.ondragover = null;
            fileUploadArea.ondragleave = null;
            fileUploadArea.ondrop = null;
        }

        if (fileInput) {
            fileInput.onchange = null;
        }
    }

    async loadConfig() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/config`);
            const data = await response.json();
            
            if (data.success && data.config) {
                document.getElementById('apiKey').value = data.config.api_key || '';
                document.getElementById('apiBase').value = data.config.api_base || '';
                document.getElementById('model').value = data.config.model || 'gpt-4.1-2025-04-14';
                document.getElementById('systemPrompt').value = data.config.system_prompt || '';
            }
        } catch (error) {
            console.error('加载配置失败:', error);
            this.showAlert('加载配置失败', 'warning');
        }
    }

    async saveConfig() {
        const config = {
            api_key: document.getElementById('apiKey').value,
            api_base: document.getElementById('apiBase').value,
            model: document.getElementById('model').value,
            system_prompt: document.getElementById('systemPrompt').value
        };

        if (!config.api_key || !config.api_base) {
            this.showAlert('请填写API Key和API Base URL', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();
            if (data.success) {
                this.showAlert('配置保存成功！', 'success');
            } else {
                this.showAlert('配置保存失败：' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('配置保存失败：' + error.message, 'danger');
        }
    }

    async testConnection() {
        console.log('测试连接按钮被点击');
        
        const config = {
            api_key: document.getElementById('apiKey').value,
            api_base: document.getElementById('apiBase').value
        };

        if (!config.api_key || !config.api_base) {
            this.showAlert('请先填写API配置', 'warning');
            return;
        }

        try {
            console.log('开始测试连接...');
            // 先保存配置
            await this.saveConfig();
            
            // 测试连接
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            console.log('连接测试响应:', data);
            
            if (data.status === 'healthy') {
                this.showAlert('连接测试成功！', 'success');
            } else {
                this.showAlert('连接测试失败', 'danger');
            }
        } catch (error) {
            console.error('连接测试错误:', error);
            this.showAlert('连接测试失败：' + error.message, 'danger');
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        
        if (file) {
            // 验证文件类型
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                this.showAlert('请选择PDF文件', 'warning');
                event.target.value = ''; // 清空选择
                return;
            }
            
            // 验证文件大小 (50MB)
            const maxSize = 50 * 1024 * 1024; // 50MB
            if (file.size > maxSize) {
                this.showAlert('文件大小不能超过50MB', 'warning');
                event.target.value = ''; // 清空选择
                return;
            }
            
            // 存储选中的文件到实例变量
            this.selectedFile = file;
            
            const fileUploadArea = document.getElementById('fileUploadArea');
            fileUploadArea.innerHTML = `
                <i class="fas fa-file-pdf fa-3x text-danger mb-3"></i>
                <h5>已选择文件：${file.name}</h5>
                <p class="text-muted">文件大小：${this.formatFileSize(file.size)}</p>
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="app.resetFileInput()">
                    <i class="fas fa-times me-1"></i>重新选择
                </button>
            `;
        } else {
            this.selectedFile = null; // 清空选中的文件
        }
    }

    resetFileInput() {
        // 清空存储的文件
        this.selectedFile = null;
        
        // 先移除所有现有的事件监听器
        this.removeFileUploadListeners();
        
        // 清空文件输入
        const fileInput = document.getElementById('pdfFile');
        if (fileInput) {
            fileInput.value = '';
        }
        
        // 恢复文件上传区域的HTML
        document.getElementById('fileUploadArea').innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <h5>拖拽PDF文件到此处或点击选择文件</h5>
            <p class="text-muted">支持PDF格式，最大50MB</p>
            <input type="file" class="form-control d-none" id="pdfFile" accept=".pdf" required>
        `;
        
        // 重新绑定文件上传区域的事件监听器
        this.setupFileUploadListeners();
    }

    async uploadAndProcess() {
        // 直接使用存储在实例中的 selectedFile
        const file = this.selectedFile;
        const customPrompt = document.getElementById('customPrompt').value;

        if (!file) {
            this.showAlert('请选择PDF文件', 'warning');
            return;
        }

        // 获取配置
        const config = {
            api_key: document.getElementById('apiKey').value,
            api_base: document.getElementById('apiBase').value,
            model: document.getElementById('model').value,
            system_prompt: document.getElementById('systemPrompt').value
        };

        if (!config.api_key || !config.api_base) {
            this.showAlert('请先配置API Key和API Base URL', 'warning');
            return;
        }

        try {
            // 先保存配置
            await this.saveConfig();

            // 上传文件
            const formData = new FormData();
            formData.append('file', file);

            const uploadResponse = await fetch(`${this.apiBaseUrl}/upload`, {
                method: 'POST',
                body: formData
            });

            const uploadData = await uploadResponse.json();
            
            if (!uploadData.success) {
                this.showAlert('文件上传失败：' + uploadData.message, 'danger');
                return;
            }

            this.currentFileId = uploadData.file_id;

            // 开始处理
            const processData = {
                file_id: this.currentFileId,
                prompt: customPrompt,
                config: config
            };
            
            const processResponse = await fetch(`${this.apiBaseUrl}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(processData)
            });

            const processResult = await processResponse.json();
            
            if (processResult.success) {
                this.showAlert('开始处理PDF文件', 'info');
                this.showProgressSection();
                this.startStatusPolling();
                this.loadTasks(); // 刷新任务列表
            } else {
                this.showAlert('开始处理失败：' + processResult.message, 'danger');
            }

        } catch (error) {
            this.showAlert('处理失败：' + error.message, 'danger');
        }
    }

    showProgressSection() {
        const progressSection = document.getElementById('progressSection');
        const resultsSection = document.getElementById('resultsSection');
        
        if (progressSection) {
            progressSection.classList.remove('hidden');
            
            // 确保取消按钮在进度区域显示后立即可见
            setTimeout(() => {
                this.showCancelButton();
            }, 100);
        }
        
        if (resultsSection) {
            resultsSection.classList.add('hidden');
        }
    }

    showCancelButton() {
        const cancelBtn = document.getElementById('cancelTaskBtn');
        if (cancelBtn) {
            // 使用setAttribute设置style，这样可以包含!important
            cancelBtn.setAttribute('style', 'display: inline-block !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; position: relative !important; z-index: 999 !important;');
            cancelBtn.disabled = false;
        }
    }

    hideCancelButton() {
        const cancelBtn = document.getElementById('cancelTaskBtn');
        if (cancelBtn) {
            cancelBtn.setAttribute('style', 'display: none !important; opacity: 0.5 !important;');
            cancelBtn.disabled = true;
        }
    }

    hideProgressSection() {
        document.getElementById('progressSection').classList.add('hidden');
    }

    async cancelTask() {
        if (!this.currentFileId) {
            this.showAlert('没有正在处理的任务', 'warning');
            return;
        }

        // 显示确认对话框
        const confirmed = confirm('确定要取消当前正在处理的任务吗？\n\n取消后，已处理的部分将保留，但未处理的部分将停止。');
        
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/cancel/${this.currentFileId}`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('任务取消请求已发送', 'info');
                // 停止状态轮询
                if (this.statusInterval) {
                    clearInterval(this.statusInterval);
                }
                // 隐藏取消按钮
                this.hideCancelButton();
            } else {
                this.showAlert('取消任务失败：' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('取消任务失败：' + error.message, 'danger');
        }
    }

    startStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }

        this.statusInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/status/${this.currentFileId}`);
                const data = await response.json();
                
                if (data.success) {
                    this.updateProgress(data.status);
                    
                    if (!data.status.is_processing) {
                        clearInterval(this.statusInterval);
                        if (data.status.error === '用户取消') {
                            this.showAlert('任务已取消', 'warning');
                            this.hideProgressSection();
                        } else if (data.status.results && data.status.results.length > 0) {
                            this.showResults(data.status.results);
                        }
                        this.loadTasks(); // 刷新任务列表
                    }
                }
            } catch (error) {
                console.error('获取状态失败:', error);
            }
        }, 1000);
    }

    updateProgress(status) {
        document.getElementById('statusMessage').textContent = status.status_message;
        document.getElementById('progressText').textContent = status.progress + '%';
        document.getElementById('progressBar').style.width = status.progress + '%';
        
        if (status.total_pages > 0) {
            document.getElementById('currentPageInfo').textContent = 
                `正在处理第 ${status.current_page} 页，共 ${status.total_pages} 页`;
        }
        
        // 根据任务状态管理取消按钮
        const cancelBtn = document.getElementById('cancelTaskBtn');
        
        if (cancelBtn) {
            if (status.is_processing) {
                this.showCancelButton();
            } else {
                this.hideCancelButton();
            }
        }
    }

    showResults(results) {
        document.getElementById('progressSection').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden');
        
        const container = document.getElementById('resultsContainer');
        container.innerHTML = '';

        results.forEach((result, index) => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result-card fade-in';
            resultDiv.innerHTML = `
                <div class="row">
                    <div class="col-md-3">
                        <img src="file:///${result.image_path.replace(/\\/g, '/')}" 
                             class="page-preview img-fluid" alt="第${result.page}页预览">
                    </div>
                    <div class="col-md-9">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="mb-0">第 ${result.page} 页分析结果</h6>
                            <span class="status-badge ${result.success ? 'status-completed' : 'status-error'}">
                                ${result.success ? '分析完成' : '分析失败'}
                            </span>
                        </div>
                        <div class="explanation-preview mb-3">
                            ${result.explanation_preview || '暂无内容'}
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-primary btn-sm" onclick="app.viewResult(${index})">
                                <i class="fas fa-eye me-1"></i>查看详情
                            </button>
                            ${result.success ? `
                                <button class="btn btn-outline-success btn-sm" onclick="app.downloadResult('${this.currentFileId}', ${result.page})">
                                    <i class="fas fa-download me-1"></i>下载结果
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(resultDiv);
        });

        // 存储结果供详情查看使用
        this.currentResults = results;
    }

    viewResult(index) {
        const result = this.currentResults[index];
        const modal = new bootstrap.Modal(document.getElementById('resultModal'));
        
        document.getElementById('modalImage').src = `file:///${result.image_path.replace(/\\/g, '/')}`;
        document.getElementById('modalExplanation').innerHTML = 
            result.explanation ? marked.parse(result.explanation) : '<p class="text-muted">暂无分析结果</p>';
        
        // 设置下载按钮
        document.getElementById('downloadBtn').onclick = () => {
            this.downloadResult(this.currentFileId, result.page);
        };
        
        modal.show();
    }

    async downloadResult(fileId, page) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/download/${fileId}/${page}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `page_${page}_analysis.md`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.showAlert('文件下载成功', 'success');
            } else {
                this.showAlert('文件下载失败', 'danger');
            }
        } catch (error) {
            this.showAlert('文件下载失败：' + error.message, 'danger');
        }
    }

    async loadTasks() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks`);
            const data = await response.json();
            
            if (data.success) {
                this.tasks.clear();
                data.tasks.forEach(task => {
                    this.tasks.set(task.file_id, task);
                });
                this.updateTaskList();
            }
        } catch (error) {
            console.error('加载任务列表失败:', error);
        }
    }

    updateTaskList() {
        const taskList = document.getElementById('taskList');
        const taskListSection = document.getElementById('taskListSection');
        
        if (this.tasks.size === 0) {
            taskListSection.style.display = 'none';
            return;
        }
        
        taskListSection.style.display = 'block';
        taskList.innerHTML = '';

        this.tasks.forEach((task, fileId) => {
            const taskDiv = document.createElement('div');
            taskDiv.className = `task-item ${task.is_processing ? 'processing' : (task.error ? 'error' : 'completed')}`;
            
            const statusText = task.is_processing ? '处理中' : (task.error ? '失败' : '完成');
            const statusIcon = task.is_processing ? 'fa-spinner fa-spin' : (task.error ? 'fa-exclamation-circle' : 'fa-check-circle');
            
            taskDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${fileId}</h6>
                        <p class="mb-1 text-muted">${task.status_message}</p>
                        ${task.is_processing ? `
                            <div class="progress" style="height: 4px;">
                                <div class="progress-bar" style="width: ${task.progress}%"></div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="text-end">
                        <span class="badge ${task.is_processing ? 'bg-warning' : (task.error ? 'bg-danger' : 'bg-success')}">
                            <i class="fas ${statusIcon} me-1"></i>${statusText}
                        </span>
                        ${task.is_processing ? '' : `
                            <div class="mt-1">
                                <button class="btn btn-sm btn-outline-primary" onclick="app.viewTaskResults('${fileId}')">
                                    <i class="fas fa-eye me-1"></i>查看结果
                                </button>
                            </div>
                        `}
                    </div>
                </div>
            `;
            
            taskList.appendChild(taskDiv);
        });
    }

    async viewTaskResults(fileId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/results/${fileId}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentFileId = fileId;
                this.currentResults = data.results;
                this.showResults(data.results);
                document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
            } else {
                this.showAlert('获取结果失败：' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('获取结果失败：' + error.message, 'danger');
        }
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.main-container').insertBefore(alertDiv, document.querySelector('.section-card'));
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async loadFileList() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/files`);
            const data = await response.json();
            
            if (data.success) {
                this.updateFileList(data.files);
            } else {
                console.error('加载文件列表失败:', data.message);
            }
        } catch (error) {
            console.error('加载文件列表失败:', error);
        }
    }

    updateFileList(files) {
        const fileList = document.getElementById('fileList');
        const fileCount = document.getElementById('fileCount');
        
        fileCount.textContent = `共 ${files.length} 个PDF文件`;
        
        if (files.length === 0) {
            fileList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-folder-open fa-3x mb-3"></i>
                    <p>暂无已处理的PDF文件</p>
                </div>
            `;
            return;
        }
        
        fileList.innerHTML = '';
        
        files.forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'file-item mb-3';
            fileDiv.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="card-title mb-2">
                                    <i class="fas fa-file-pdf text-danger me-2"></i>
                                    ${file.pdf_name}
                                </h6>
                                <div class="row text-muted small">
                                    <div class="col-md-4">
                                        <i class="fas fa-image me-1"></i>
                                        图片: ${file.image_count} 张
                                    </div>
                                    <div class="col-md-4">
                                        <i class="fas fa-file-alt me-1"></i>
                                        分析: ${file.explanation_count} 个
                                    </div>
                                    <div class="col-md-4">
                                        <i class="fas fa-folder me-1"></i>
                                        状态: ${file.explanation_count > 0 ? '已完成' : '仅图片'}
                                    </div>
                                </div>
                            </div>
                            <div class="btn-group" role="group">
                                <button class="btn btn-outline-primary btn-sm" onclick="app.viewFileDetails('${file.pdf_name}')">
                                    <i class="fas fa-eye me-1"></i>查看
                                </button>
                                <button class="btn btn-outline-info btn-sm" onclick="app.previewFile('${file.pdf_name}')">
                                    <i class="fas fa-search me-1"></i>预览
                                </button>
                                <button class="btn btn-outline-success btn-sm" onclick="app.downloadAllFiles('${file.pdf_name}')">
                                    <i class="fas fa-download me-1"></i>下载
                                </button>
                                <button class="btn btn-outline-danger btn-sm" onclick="app.deleteFile('${file.pdf_name}')">
                                    <i class="fas fa-trash me-1"></i>删除
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            fileList.appendChild(fileDiv);
        });
    }

    async viewFileDetails(pdfName) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/files/${pdfName}`);
            const data = await response.json();
            
            if (data.success) {
                this.showFileDetailsModal(data);
            } else {
                this.showAlert('获取文件详情失败：' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('获取文件详情失败：' + error.message, 'danger');
        }
    }

    showFileDetailsModal(fileData) {
        // 创建模态框
        const modalHtml = `
            <div class="modal fade" id="fileDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-file-pdf text-danger me-2"></i>
                                ${fileData.pdf_name} - 文件详情
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-image me-2"></i>图片文件 (${fileData.images.length} 张)</h6>
                                    <div class="list-group" style="max-height: 300px; overflow-y: auto;">
                                        ${fileData.images.map(img => `
                                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                                <span>${img.filename}</span>
                                                <button class="btn btn-sm btn-outline-primary" onclick="app.viewImage('${img.path}')">
                                                    <i class="fas fa-eye"></i>
                                                </button>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fas fa-file-alt me-2"></i>分析结果 (${fileData.explanations.length} 个)</h6>
                                    <div class="list-group" style="max-height: 300px; overflow-y: auto;">
                                        ${fileData.explanations.map(exp => `
                                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                                <span>${exp.filename}</span>
                                                <div>
                                                    <button class="btn btn-sm btn-outline-primary me-1" onclick="app.viewExplanation('${exp.path}')">
                                                        <i class="fas fa-eye"></i>
                                                    </button>
                                                    <button class="btn btn-sm btn-outline-success" onclick="app.downloadFile('${exp.path}', '${exp.filename}')">
                                                        <i class="fas fa-download"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-success" onclick="app.downloadAllFiles('${fileData.pdf_name}')">
                                <i class="fas fa-download me-2"></i>下载所有文件
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除现有模态框
        const existingModal = document.getElementById('fileDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('fileDetailsModal'));
        modal.show();
    }

    viewImage(imagePath) {
        // 在新窗口中打开图片
        window.open(`file:///${imagePath.replace(/\\/g, '/')}`, '_blank');
    }

    async viewExplanation(explanationPath) {
        try {
            // 这里可以实现查看分析结果的功能
            this.showAlert('查看分析结果功能开发中...', 'info');
        } catch (error) {
            this.showAlert('查看失败：' + error.message, 'danger');
        }
    }

    async downloadFile(filePath, filename) {
        try {
            // 这里可以实现下载单个文件的功能
            this.showAlert('下载功能开发中...', 'info');
        } catch (error) {
            this.showAlert('下载失败：' + error.message, 'danger');
        }
    }

    async downloadAllFiles(pdfName) {
        try {
            this.showAlert('正在生成ZIP文件，请稍候...', 'info');
            
            const response = await fetch(`${this.apiBaseUrl}/files/${pdfName}/download`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${pdfName}_explanations.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.showAlert('ZIP文件下载成功！', 'success');
            } else {
                const errorData = await response.json();
                this.showAlert('下载失败：' + (errorData.message || '未知错误'), 'danger');
            }
        } catch (error) {
            this.showAlert('下载失败：' + error.message, 'danger');
        }
    }

    async refreshFileList() {
        await this.loadFileList();
        this.showAlert('文件列表已刷新', 'success');
    }

    async previewFile(pdfName) {
        try {
            this.showAlert('正在加载预览数据...', 'info');
            
            const response = await fetch(`${this.apiBaseUrl}/files/${pdfName}/preview`);
            const data = await response.json();
            
            if (data.success) {
                // 打开预览页面
                const previewUrl = `preview.html?pdf=${encodeURIComponent(pdfName)}`;
                window.open(previewUrl, '_blank');
            } else {
                this.showAlert('加载预览数据失败：' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('加载预览数据失败：' + error.message, 'danger');
        }
    }

    async deleteFile(pdfName) {
        // 显示确认对话框
        const confirmed = confirm(`确定要删除文件 "${pdfName}" 吗？\n\n这将删除：\n- 原始PDF文件\n- 所有转换的图片\n- 所有分析结果\n\n此操作不可撤销！`);
        
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/files/${pdfName}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`文件 ${pdfName} 已成功删除`, 'success');
                // 刷新文件列表
                await this.loadFileList();
            } else {
                this.showAlert(`删除失败：${data.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`删除失败：${error.message}`, 'danger');
        }
    }
}

// 初始化应用
const app = new PDFAnalyzer();

// 全局函数供HTML调用
window.resetFileInput = function() {
    app.resetFileInput();
};

window.cancelTask = function() {
    app.cancelTask();
};

