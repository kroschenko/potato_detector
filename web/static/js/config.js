class ConfigManager {
    constructor() {
        this.configData = {};
        this.originalConfig = {};
        this.videoFiles = [];
        
        this.initializeElements();
        this.initializeEventListeners();
        this.loadConfiguration();
        this.loadVideoFiles();
    }
    
    initializeElements() {
        this.elements = {
            form: document.getElementById('config-form'),
            sortBySizeToggle: document.getElementById('sort-by-size-toggle'),
            sortByDefectsToggle: document.getElementById('sort-by-defects-toggle'),
            sizeLimitInput: document.getElementById('size-limit-input'),
            confidenceThresholdInput: document.getElementById('confidence-threshold-input'),
            visibleWidthInput: document.getElementById('visible-width-input'),
            visibleHeightInput: document.getElementById('visible-height-input'),
            frameSizeDisplay: document.getElementById('frame-size-display'),
            cameraTypeDisplay: document.getElementById('camera-type-display'),
            videoFileItem: document.getElementById('video-file-item'),
            videoFileSelect: document.getElementById('video-file-select'),
            nozzleOpenTimeInput: document.getElementById('nozzle-open-time-input'),
            leftNozzleDelayInput: document.getElementById('left-nozzle-delay-input'),
            rightNozzleDelayInput: document.getElementById('right-nozzle-delay-input'),
            saveButton: document.getElementById('save-config'),
            resetButton: document.getElementById('reset-config')
        };
    }
    
    initializeEventListeners() {
        this.elements.saveButton.addEventListener('click', () => this.saveConfiguration());
        this.elements.resetButton.addEventListener('click', () => this.resetConfiguration());
        this.elements.videoFileSelect.addEventListener('change', () => this.onVideoFileChange());
        
        this.elements.form.addEventListener('input', () => this.onFormChange());
    }
    
    async loadConfiguration() {
        try {
            const response = await ApiClient.get('/config');
            this.configData = response;
            this.originalConfig = { ...response };
            this.updateForm();
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showError('Ошибка загрузки конфигурации');
        }
    }
    
    async loadVideoFiles() {
        try {
            const response = await ApiClient.get('/video-files');
            this.videoFiles = response.files || [];
            this.populateVideoSelect();
        } catch (error) {
            console.error('Error loading video files:', error);
        }
    }
    
    populateVideoSelect() {
        this.elements.videoFileSelect.innerHTML = '<option value="">Выберите видеофайл...</option>';
        
        this.videoFiles.forEach(filename => {
            const option = document.createElement('option');
            option.value = filename;
            option.textContent = filename;
            if (filename === this.configData.VIDEO_FILE) {
                option.selected = true;
            }
            this.elements.videoFileSelect.appendChild(option);
        });
    }
    
    updateForm() {
        this.elements.sortBySizeToggle.checked = this.configData.SORT_BY_POTATO_SIZE || false;
        this.elements.sortByDefectsToggle.checked = this.configData.SORT_BY_OUTER_DEFECTS || false;
        this.elements.sizeLimitInput.value = this.configData.POTATO_SIZE_LIMIT_CENTIMETERS || 4.0;
        this.elements.confidenceThresholdInput.value = this.configData.POTATO_DETECTION_CONFIDENCE_THRESHOLD || 0.85;
        this.elements.visibleWidthInput.value = this.configData.VISIBLE_AREA_WIDTH_CENTIMETERS || 43.0;
        this.elements.visibleHeightInput.value = this.configData.VISIBLE_AREA_HEIGHT_CENTIMETERS || 25.0;
        
        // Arduino timing parameters
        this.elements.nozzleOpenTimeInput.value = this.configData.NOZZLE_OPEN_TIME || 233;
        this.elements.leftNozzleDelayInput.value = this.configData.LEFT_NOZZLE_DELAY || 1401;
        this.elements.rightNozzleDelayInput.value = this.configData.RIGHT_NOZZLE_DELAY || 1950;
        
        const frameSize = this.configData.FRAME_SIZE;
        this.elements.frameSizeDisplay.textContent = Array.isArray(frameSize) 
            ? `${frameSize[0]} x ${frameSize[1]}` 
            : frameSize;
        
        const typeMap = {
            'AVI_CAMERA': 'Камера AVI файл',
            'DO3THINK_CAMERA': 'Промышленная камера DO3Think',
            'OPENCV_CAMERA': 'USB камера OpenCV'
        };
        this.elements.cameraTypeDisplay.textContent = typeMap[this.configData.CAMERA_TYPE] || this.configData.CAMERA_TYPE;
        
        if (this.configData.CAMERA_TYPE === 'AVI_CAMERA') {
            this.elements.videoFileItem.style.display = 'grid';
            this.populateVideoSelect();
        } else {
            this.elements.videoFileItem.style.display = 'none';
        }
    }
    
    onFormChange() {
        this.elements.saveButton.disabled = false;
        this.elements.resetButton.disabled = false;
    }
    
    onVideoFileChange() {
        const selectedFile = this.elements.videoFileSelect.value;
        if (selectedFile) {
            this.configData.VIDEO_FILE = selectedFile;
        }
    }
    
    async saveConfiguration() {
        try {
            this.elements.saveButton.disabled = true;
            this.elements.saveButton.textContent = 'Сохранение...';
            
            const formData = {
                SORT_BY_POTATO_SIZE: this.elements.sortBySizeToggle.checked,
                SORT_BY_OUTER_DEFECTS: this.elements.sortByDefectsToggle.checked,
                POTATO_SIZE_LIMIT_CENTIMETERS: parseFloat(this.elements.sizeLimitInput.value),
                POTATO_DETECTION_CONFIDENCE_THRESHOLD: parseFloat(this.elements.confidenceThresholdInput.value),
                VISIBLE_AREA_WIDTH_CENTIMETERS: parseFloat(this.elements.visibleWidthInput.value),
                VISIBLE_AREA_HEIGHT_CENTIMETERS: parseFloat(this.elements.visibleHeightInput.value),
                NOZZLE_OPEN_TIME: parseInt(this.elements.nozzleOpenTimeInput.value),
                LEFT_NOZZLE_DELAY: parseInt(this.elements.leftNozzleDelayInput.value),
                RIGHT_NOZZLE_DELAY: parseInt(this.elements.rightNozzleDelayInput.value)
            };
            
            if (this.configData.CAMERA_TYPE === 'AVI_CAMERA' && this.elements.videoFileSelect.value) {
                formData.VIDEO_FILE = this.elements.videoFileSelect.value;
            }
            
            const response = await ApiClient.post('/config', formData);
            
            if (response.status === 'success') {
                this.originalConfig = { ...this.configData };
                this.configData = { ...this.configData, ...formData };
                this.showSuccess('Настройки успешно сохранены');
                this.elements.saveButton.disabled = true;
                this.elements.resetButton.disabled = true;
            } else {
                this.showError('Ошибка сохранения настроек');
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showError('Ошибка сохранения настроек: ' + (error.message || 'Неизвестная ошибка'));
        } finally {
            this.elements.saveButton.textContent = 'Сохранить настройки';
        }
    }
    
    resetConfiguration() {
        this.configData = { ...this.originalConfig };
        this.updateForm();
        this.elements.saveButton.disabled = true;
        this.elements.resetButton.disabled = true;
        this.showInfo('Настройки сброшены к исходным значениям');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showInfo(message) {
        this.showNotification(message, 'info');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        if (type === 'success') {
            notification.style.backgroundColor = '#10b981';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#ef4444';
        } else {
            notification.style.backgroundColor = '#3b82f6';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .config-input {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        transition: border-color 0.2s ease;
    }
    
    .config-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .config-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => {
    window.configManager = new ConfigManager();
});