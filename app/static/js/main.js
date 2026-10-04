/**
 * DeepFake Detection System - Main JavaScript
 * Handles file upload, analysis, and results display
 */

class DeepFakeDetector {
    constructor() {
        this.currentFile = null;
        this.currentJobId = null;
        this.pollingInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkForJobId();
    }

    setupEventListeners() {
        // File upload elements
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const removeFileBtn = document.getElementById('removeFile');

        // Results elements
        const newAnalysisBtn = document.getElementById('newAnalysis');
        const downloadReportBtn = document.getElementById('downloadReport');
        const retryBtn = document.getElementById('retryBtn');

        // Upload area events
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));

        // File input change
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Button events
        if (analyzeBtn) analyzeBtn.addEventListener('click', this.startAnalysis.bind(this));
        if (removeFileBtn) removeFileBtn.addEventListener('click', this.removeFile.bind(this));
        if (newAnalysisBtn) newAnalysisBtn.addEventListener('click', this.resetAnalysis.bind(this));
        if (downloadReportBtn) downloadReportBtn.addEventListener('click', this.downloadReport.bind(this));
        if (retryBtn) retryBtn.addEventListener('click', this.retryAnalysis.bind(this));
    }

    checkForJobId() {
        // Check if we're on the results page with a job ID
        let jobIdValue = null;

        // Try to get jobId from global variable
        if (typeof jobId !== 'undefined' && jobId) {
            jobIdValue = jobId;
        }

        // Try to get from URL
        if (!jobIdValue || jobIdValue === '[object HTMLSpanElement]') {
            const pathParts = window.location.pathname.split('/');
            if (pathParts.length >= 3 && pathParts[1] === 'result') {
                jobIdValue = pathParts[2];
            }
        }

        // Validate jobId
        if (jobIdValue &&
            typeof jobIdValue === 'string' &&
            jobIdValue.length > 10 &&
            jobIdValue !== '[object HTMLSpanElement]') {
            this.currentJobId = jobIdValue;
            console.log('Loading results for job ID:', this.currentJobId);
            this.loadResults();
        } else if (window.location.pathname.includes('/result')) {
            // Home page has no job id — expected; avoid noisy console on "/"
            console.warn('No valid job ID found for this results URL');
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    handleFile(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }

        this.currentFile = file;
        this.showFilePreview(file);
        this.enableAnalyzeButton();
    }

    validateFile(file) {
        const maxSize = 500 * 1024 * 1024; // 500MB
        const allowedTypes = [
            'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/tiff',
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/wmv', 'video/flv', 'video/webm'
        ];

        if (file.size > maxSize) {
            this.showError('حجم الملف كبير جداً. الحد الأقصى 500 ميجابايت.');
            return false;
        }

        if (!allowedTypes.includes(file.type)) {
            this.showError('نوع الملف غير مدعوم. يرجى اختيار صورة أو فيديو.');
            return false;
        }

        return true;
    }

    showFilePreview(file) {
        const preview = document.getElementById('filePreview');
        const previewMedia = document.getElementById('previewMedia');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        // Show preview section
        preview.style.display = 'block';

        // Set file info
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        // Create preview element
        previewMedia.innerHTML = '';
        const element = document.createElement(file.type.startsWith('image/') ? 'img' : 'video');
        element.src = URL.createObjectURL(file);
        element.style.width = '100%';
        element.style.height = '100%';
        element.style.objectFit = 'cover';

        if (file.type.startsWith('video/')) {
            element.controls = true;
            element.muted = true;
        }

        previewMedia.appendChild(element);
    }

    removeFile() {
        this.currentFile = null;
        document.getElementById('filePreview').style.display = 'none';
        document.getElementById('fileInput').value = '';
        this.disableAnalyzeButton();
    }

    enableAnalyzeButton() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
        }
    }

    disableAnalyzeButton() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.disabled = true;
        }
    }

    async startAnalysis() {
        if (!this.currentFile) {
            this.showError('يرجى اختيار ملف أولاً.');
            return;
        }

        try {
            this.showLoadingState();
            this.disableAnalyzeButton();

            // Determine endpoint based on file type
            const endpoint = this.currentFile.type.startsWith('image/') ? '/api/upload-image' : '/api/upload-video';

            // Create form data
            const formData = new FormData();
            formData.append('file', this.currentFile);

            // Get advanced options
            const maxFrames = document.getElementById('maxFrames')?.value || 20;
            const sampleRate = document.getElementById('sampleRate')?.value || 1;
            const forensicsOnly = document.getElementById('forensicsOnly')?.checked || false;

            formData.append('max_frames', maxFrames);
            formData.append('sample_rate', sampleRate);
            formData.append('forensics_only', forensicsOnly);

            // Upload file
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.currentJobId = result.id;

            // Start polling for results
            this.startPolling();

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError('حدث خطأ أثناء رفع الملف. يرجى المحاولة مرة أخرى.');
            this.enableAnalyzeButton();
        }
    }

    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // Validate job ID before polling
        if (!this.currentJobId ||
            typeof this.currentJobId !== 'string' ||
            this.currentJobId === '[object HTMLSpanElement]') {
            console.error('Invalid job ID for polling:', this.currentJobId);
            return;
        }

        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/result/${this.currentJobId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();

                if (result.status === 'done') {
                    clearInterval(this.pollingInterval);
                    this.showResults(result);
                } else if (result.status === 'error') {
                    clearInterval(this.pollingInterval);
                    this.showError(result.error || 'حدث خطأ أثناء التحليل.');
                } else {
                    // Still processing, update progress
                    this.updateProgress();
                }

            } catch (error) {
                console.error('Polling error:', error);
                clearInterval(this.pollingInterval);
                this.showError('حدث خطأ أثناء جلب النتائج.');
            }
        }, 2000); // Poll every 2 seconds
    }

    async loadResults() {
        try {
            // Validate job ID
            if (!this.currentJobId ||
                typeof this.currentJobId !== 'string' ||
                this.currentJobId === '[object HTMLSpanElement]') {
                throw new Error('Invalid job ID');
            }

            this.showLoadingState();

            const response = await fetch(`/api/result/${this.currentJobId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.status === 'done') {
                this.showResults(result);
            } else if (result.status === 'error') {
                this.showError(result.error || 'حدث خطأ أثناء تحميل النتائج.');
            } else {
                // Still processing, start polling
                this.startPolling();
            }

        } catch (error) {
            console.error('Load results error:', error);
            this.showError('حدث خطأ أثناء تحميل النتائج.');
        }
    }

    showLoadingState() {
        const resultsSection = document.getElementById('resultsSection');
        const loadingState = document.getElementById('loadingState');
        const resultsContent = document.getElementById('resultsContent');
        const errorState = document.getElementById('errorState');

        if (resultsSection) resultsSection.style.display = 'block';
        if (loadingState) loadingState.style.display = 'block';
        if (resultsContent) resultsContent.style.display = 'none';
        if (errorState) errorState.style.display = 'none';

        // Scroll to results
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    showResults(result) {
        const loadingState = document.getElementById('loadingState');
        const resultsContent = document.getElementById('resultsContent');
        const errorState = document.getElementById('errorState');

        if (loadingState) loadingState.style.display = 'none';
        if (errorState) errorState.style.display = 'none';
        if (resultsContent) {
            resultsContent.style.display = 'block';
            resultsContent.classList.add('fade-in');
        }

        // Update job ID display
        const jobIdElement = document.getElementById('jobId');
        if (jobIdElement) {
            jobIdElement.textContent = this.currentJobId;
        }

        // Update score display
        this.updateScoreDisplay(result.summary);

        // Update explanations
        this.updateExplanations(result.summary.explanations || []);

        // Update frame analysis (for videos)
        if (result.summary.frame_level) {
            this.updateFrameAnalysis(result.summary.frame_level);
        }

        // Update advanced analysis
        if (result.advanced_analysis) {
            this.displayAdvancedAnalysis(result.advanced_analysis);
        }

        // Update artifacts
        if (result.artifacts && Object.keys(result.artifacts).length > 0) {
            this.updateArtifacts(result.artifacts);
        }
    }

    showError(message) {
        const loadingState = document.getElementById('loadingState');
        const resultsContent = document.getElementById('resultsContent');
        const errorState = document.getElementById('errorState');
        const errorMessage = document.getElementById('errorMessage');

        if (loadingState) loadingState.style.display = 'none';
        if (resultsContent) resultsContent.style.display = 'none';
        if (errorState) errorState.style.display = 'block';
        if (errorMessage) errorMessage.textContent = message;

        // Scroll to error
        if (errorState) {
            errorState.scrollIntoView({ behavior: 'smooth' });
        }
    }

    updateScoreDisplay(summary) {
        const realScore = summary.real_score || 0;
        const fakeScore = summary.fake_score || 0;

        // Update score circle
        const scoreCircle = document.querySelector('.score-circle');
        const scoreValue = document.getElementById('realScore');
        const realBar = document.getElementById('realBar');
        const fakeBar = document.getElementById('fakeBar');
        const realValue = document.getElementById('realValue');
        const fakeValue = document.getElementById('fakeValue');

        if (scoreValue) {
            scoreValue.textContent = `${(realScore * 100).toFixed(1)}%`;
        }

        if (realBar) {
            realBar.style.width = `${realScore * 100}%`;
        }

        if (fakeBar) {
            fakeBar.style.width = `${fakeScore * 100}%`;
        }

        if (realValue) {
            realValue.textContent = `${(realScore * 100).toFixed(1)}%`;
        }

        if (fakeValue) {
            fakeValue.textContent = `${(fakeScore * 100).toFixed(1)}%`;
        }

        // Update score circle background
        if (scoreCircle) {
            const angle = realScore * 360;
            scoreCircle.style.background = `conic-gradient(var(--accent-primary) ${angle}deg, var(--bg-tertiary) ${angle}deg)`;
        }
    }

    updateExplanations(explanations) {
        const explanationsList = document.getElementById('explanationsList');
        if (!explanationsList) return;

        explanationsList.innerHTML = '';

        explanations.forEach(explanation => {
            const item = document.createElement('div');
            item.className = 'explanation-item';

            const type = document.createElement('div');
            type.className = 'explanation-type';
            type.innerHTML = this.getExplanationTypeLabel(explanation.type);

            const detail = document.createElement('div');
            detail.className = 'explanation-detail';
            detail.textContent = explanation.detail;

            item.appendChild(type);
            item.appendChild(detail);
            explanationsList.appendChild(item);
        });
    }

    updateFrameAnalysis(frameLevel) {
        const frameAnalysisCard = document.getElementById('frameAnalysisCard');
        const frameChart = document.getElementById('frameChart');

        if (frameAnalysisCard && frameChart) {
            frameAnalysisCard.style.display = 'block';

            // Create simple bar chart
            frameChart.innerHTML = '';
            const chartContainer = document.createElement('div');
            chartContainer.style.display = 'flex';
            chartContainer.style.gap = '2px';
            chartContainer.style.height = '100%';
            chartContainer.style.alignItems = 'end';

            frameLevel.forEach((frame, index) => {
                const bar = document.createElement('div');
                bar.style.width = `${100 / frameLevel.length}%`;
                bar.style.height = `${frame.score * 100}%`;
                bar.style.background = frame.score > 0.5 ? 'var(--success)' : 'var(--error)';
                bar.style.borderRadius = '2px';
                bar.style.minHeight = '4px';
                bar.title = `Frame ${frame.frame}: ${(frame.score * 100).toFixed(1)}% real`;
                chartContainer.appendChild(bar);
            });

            frameChart.appendChild(chartContainer);
        }
    }

    updateArtifacts(artifacts) {
        const artifactsCard = document.getElementById('artifactsCard');
        const artifactsGrid = document.getElementById('artifactsGrid');

        if (artifactsCard && artifactsGrid) {
            artifactsCard.style.display = 'block';
            artifactsGrid.innerHTML = '';

            Object.entries(artifacts).forEach(([key, url]) => {
                const item = document.createElement('div');
                item.className = 'artifact-item';

                const image = document.createElement('img');
                image.className = 'artifact-image';
                image.src = url;
                image.alt = this.getArtifactLabel(key);

                const info = document.createElement('div');
                info.className = 'artifact-info';

                const title = document.createElement('div');
                title.className = 'artifact-title';
                title.textContent = this.getArtifactLabel(key);

                const description = document.createElement('div');
                description.className = 'artifact-description';
                description.textContent = this.getArtifactDescription(key);

                info.appendChild(title);
                info.appendChild(description);
                item.appendChild(image);
                item.appendChild(info);
                artifactsGrid.appendChild(item);
            });
        }
    }

    displayAdvancedAnalysis(advancedData) {
        const advancedCard = document.getElementById('advancedAnalysisCard');
        const advancedGrid = document.getElementById('advancedGrid');

        if (!advancedCard || !advancedGrid) return;

        advancedCard.style.display = 'block';
        advancedGrid.innerHTML = '';

        // Display different types of advanced analysis
        if (advancedData.eye_blinking) {
            this.createAdvancedItem(advancedGrid, {
                icon: 'fas fa-eye',
                title: 'تحليل رمش العين',
                content: this.formatEyeBlinkingAnalysis(advancedData.eye_blinking),
                stats: this.getEyeBlinkingStats(advancedData.eye_blinking)
            });
        }

        if (advancedData.lighting) {
            this.createAdvancedItem(advancedGrid, {
                icon: 'fas fa-lightbulb',
                title: 'تحليل الإضاءة',
                content: this.formatLightingAnalysis(advancedData.lighting),
                stats: this.getLightingStats(advancedData.lighting)
            });
        }

        if (advancedData.audio) {
            this.createAdvancedItem(advancedGrid, {
                icon: 'fas fa-volume-up',
                title: 'تحليل الصوت',
                content: this.formatAudioAnalysis(advancedData.audio),
                stats: this.getAudioStats(advancedData.audio)
            });
        }

        if (advancedData.frequency) {
            this.createAdvancedItem(advancedGrid, {
                icon: 'fas fa-wave-square',
                title: 'تحليل الترددات',
                content: this.formatFrequencyAnalysis(advancedData.frequency),
                stats: this.getFrequencyStats(advancedData.frequency)
            });
        }

        if (advancedData.quality) {
            this.createAdvancedItem(advancedGrid, {
                icon: 'fas fa-award',
                title: 'جودة الصورة',
                content: this.formatQualityAnalysis(advancedData.quality),
                stats: this.getQualityStats(advancedData.quality)
            });
        }

        if (advancedData.face_analysis) {
            this.createAdvancedItem(advancedGrid, {
                icon: 'fas fa-user',
                title: 'تحليل الوجوه',
                content: this.formatFaceAnalysis(advancedData.face_analysis),
                stats: this.getFaceAnalysisStats(advancedData.face_analysis)
            });
        }
    }

    createAdvancedItem(container, data) {
        const item = document.createElement('div');
        item.className = 'advanced-item';

        const header = document.createElement('div');
        header.className = 'advanced-item-header';

        const icon = document.createElement('i');
        icon.className = `advanced-item-icon ${data.icon}`;

        const title = document.createElement('h4');
        title.className = 'advanced-item-title';
        title.textContent = data.title;

        header.appendChild(icon);
        header.appendChild(title);

        const content = document.createElement('div');
        content.className = 'advanced-item-content';
        content.innerHTML = data.content;

        const stats = document.createElement('div');
        stats.className = 'advanced-item-stats';

        data.stats.forEach(stat => {
            const statDiv = document.createElement('div');
            statDiv.className = 'advanced-stat';

            const value = document.createElement('div');
            value.className = 'advanced-stat-value';
            value.textContent = stat.value;

            const label = document.createElement('div');
            label.className = 'advanced-stat-label';
            label.textContent = stat.label;

            statDiv.appendChild(value);
            statDiv.appendChild(label);
            stats.appendChild(statDiv);
        });

        item.appendChild(header);
        item.appendChild(content);
        item.appendChild(stats);
        container.appendChild(item);
    }

    formatEyeBlinkingAnalysis(data) {
        let content = '';
        if (data.blink_analysis) {
            content += `<p>معدل الرمش: ${data.blink_analysis.blink_rate?.toFixed(1) || 'غير محدد'} رمشة/دقيقة</p>`;
            content += `<p>انتظام الرمش: ${(data.blink_analysis.blink_regularity * 100)?.toFixed(1) || 'غير محدد'}%</p>`;
            if (data.blink_analysis.anomalies?.length > 0) {
                content += `<p class="warning">تحذيرات: ${data.blink_analysis.anomalies.join(', ')}</p>`;
            }
        }
        return content;
    }

    formatLightingAnalysis(data) {
        let content = '';
        if (data.lighting_analysis) {
            content += `<p>اتساق اتجاه الإضاءة: ${(data.lighting_analysis.lighting_direction?.consistency_score * 100)?.toFixed(1) || 'غير محدد'}%</p>`;
            content += `<p>اتساق الظلال: ${(data.lighting_analysis.shadow_consistency?.consistency_score * 100)?.toFixed(1) || 'غير محدد'}%</p>`;
        }
        return content;
    }

    formatAudioAnalysis(data) {
        let content = '';
        if (data.audio_analyses) {
            content += `<p>تحليل الطيف: ${data.audio_analyses.spectral_analysis?.anomalies?.length || 0} تحذيرات</p>`;
            content += `<p>تحليل الضوضاء: ${data.audio_analyses.noise_analysis?.anomalies?.length || 0} تحذيرات</p>`;
        }
        return content;
    }

    formatFrequencyAnalysis(data) {
        let content = '';
        if (data.frequency_ratios) {
            content += `<p>الترددات المنخفضة: ${(data.frequency_ratios.low * 100)?.toFixed(1) || 'غير محدد'}%</p>`;
            content += `<p>الترددات العالية: ${(data.frequency_ratios.high * 100)?.toFixed(1) || 'غير محدد'}%</p>`;
        }
        return content;
    }

    getEyeBlinkingStats(data) {
        return [
            { value: data.total_blinks || 0, label: 'إجمالي الرمشات' },
            { value: `${(data.blink_analysis?.blink_rate || 0).toFixed(1)}/دقيقة`, label: 'معدل الرمش' }
        ];
    }

    getLightingStats(data) {
        return [
            { value: `${(data.lighting_analysis?.lighting_direction?.consistency_score * 100 || 0).toFixed(0)}%`, label: 'اتساق الإضاءة' },
            { value: `${(data.lighting_analysis?.shadow_consistency?.consistency_score * 100 || 0).toFixed(0)}%`, label: 'اتساق الظلال' }
        ];
    }

    getAudioStats(data) {
        return [
            { value: data.audio_stats?.duration?.toFixed(1) || '0', label: 'مدة الصوت (ثانية)' },
            { value: `${(data.audio_stats?.rms_energy * 100 || 0).toFixed(1)}%`, label: 'طاقة الصوت' }
        ];
    }

    getFrequencyStats(data) {
        return [
            { value: `${(data.frequency_ratios?.low * 100 || 0).toFixed(0)}%`, label: 'ترددات منخفضة' },
            { value: `${(data.frequency_ratios?.high * 100 || 0).toFixed(0)}%`, label: 'ترددات عالية' }
        ];
    }

    formatQualityAnalysis(data) {
        let content = '';
        content += `<p>نقاط الجودة: ${(data.real_score * 100).toFixed(1)}%</p>`;
        content += `<p>تحليل شامل لجودة الصورة والوضوح</p>`;
        return content;
    }

    formatFaceAnalysis(data) {
        let content = '';
        content += `<p>عدد الوجوه المكتشفة: ${data.faces_detected}</p>`;
        if (data.face_scores && data.face_scores.length > 0) {
            const avgScore = data.face_scores.reduce((a, b) => a + b, 0) / data.face_scores.length;
            content += `<p>متوسط نقاط الوجوه: ${(avgScore * 100).toFixed(1)}%</p>`;
        }
        return content;
    }

    getQualityStats(data) {
        return [
            { value: `${(data.real_score * 100).toFixed(0)}%`, label: 'نقاط الجودة' },
            { value: `${(data.fake_score * 100).toFixed(0)}%`, label: 'احتمال التلاعب' }
        ];
    }

    getFaceAnalysisStats(data) {
        const avgScore = data.face_scores ?
            (data.face_scores.reduce((a, b) => a + b, 0) / data.face_scores.length) : 0;
        return [
            { value: data.faces_detected, label: 'عدد الوجوه' },
            { value: `${(avgScore * 100).toFixed(0)}%`, label: 'متوسط النقاط' }
        ];
    }

    updateProgress() {
        const progressFill = document.getElementById('progressFill');
        if (progressFill) {
            // Simulate progress (in real implementation, this would come from the server)
            const currentWidth = parseInt(progressFill.style.width) || 0;
            const newWidth = Math.min(currentWidth + Math.random() * 10, 90);
            progressFill.style.width = `${newWidth}%`;
        }
    }

    getExplanationTypeLabel(type) {
        const labels = {
            'model_ensemble': '<i class="fas fa-brain"></i> نموذج الذكاء الاصطناعي',
            'forensics': '<i class="fas fa-search"></i> التحليل الجنائي',
            'metadata': '<i class="fas fa-info-circle"></i> البيانات الوصفية',
            'temporal_consistency': '<i class="fas fa-clock"></i> الاتساق الزمني',
            'face_detection': '<i class="fas fa-user"></i> اكتشاف الوجوه',
            'frame_analysis': '<i class="fas fa-film"></i> تحليل الإطارات',
            'eye_blinking': '<i class="fas fa-eye"></i> تحليل رمش العين',
            'lighting': '<i class="fas fa-lightbulb"></i> تحليل الإضاءة',
            'audio': '<i class="fas fa-volume-up"></i> تحليل الصوت',
            'frequency': '<i class="fas fa-wave-square"></i> تحليل الترددات',
            'quality': '<i class="fas fa-award"></i> جودة الصورة',
            'error': '<i class="fas fa-exclamation-triangle"></i> خطأ'
        };
        return labels[type] || type;
    }

    getArtifactLabel(key) {
        const labels = {
            'preview_image': 'معاينة الصورة',
            'heatmap': 'خريطة الحرارة',
            'frame_montage': 'مجموعة الإطارات',
            'eye_blinking_analysis': 'تحليل رمش العين',
            'lighting_analysis': 'تحليل الإضاءة',
            'audio_analysis': 'تحليل الصوت',
            'frequency_analysis': 'تحليل الترددات'
        };
        return labels[key] || key;
    }

    getArtifactDescription(key) {
        const descriptions = {
            'preview_image': 'معاينة الصورة مع تحديد الوجوه المكتشفة',
            'heatmap': 'خريطة الحرارة تظهر مناطق التركيز في التحليل',
            'frame_montage': 'مجموعة من الإطارات المستخرجة من الفيديو',
            'eye_blinking_analysis': 'تحليل أنماط رمش العين الطبيعية مقابل الاصطناعية',
            'lighting_analysis': 'تحليل تناسق الإضاءة والظلال في الصورة',
            'audio_analysis': 'تحليل الصوت للكشف عن التلاعب والتشويه',
            'frequency_analysis': 'تحليل الترددات للكشف عن ضغط وتشويه الصورة'
        };
        return descriptions[key] || 'مرئي إضافي من التحليل';
    }

    async downloadReport() {
        if (!this.currentJobId ||
            typeof this.currentJobId !== 'string' ||
            this.currentJobId === '[object HTMLSpanElement]') {
            this.showError('لا يوجد تقرير صالح للتحميل.');
            return;
        }

        try {
            const response = await fetch(`/api/result/${this.currentJobId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            // Create downloadable JSON
            const report = {
                job_id: this.currentJobId,
                timestamp: new Date().toISOString(),
                results: result
            };

            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `deepfake-analysis-${this.currentJobId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            console.error('Download error:', error);
            this.showError('حدث خطأ أثناء تحميل التقرير.');
        }
    }

    resetAnalysis() {
        // Reset to initial state
        this.currentFile = null;
        this.currentJobId = null;

        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // Hide results section
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }

        // Reset file preview
        this.removeFile();

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    retryAnalysis() {
        if (this.currentJobId &&
            typeof this.currentJobId === 'string' &&
            this.currentJobId !== '[object HTMLSpanElement]') {
            this.loadResults();
        } else {
            this.resetAnalysis();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DeepFakeDetector();
});

// Handle page visibility changes to pause/resume polling
document.addEventListener('visibilitychange', () => {
    const detector = window.deepFakeDetector;
    if (detector && detector.pollingInterval) {
        if (document.hidden) {
            // Page is hidden, could pause polling
            console.log('Page hidden - polling continues');
        } else {
            // Page is visible, ensure polling is active
            console.log('Page visible - polling active');
        }
    }
});
