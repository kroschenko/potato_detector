class CameraManager {
    constructor() {
        this.isStreaming = false;
        this.cameraType = 'unknown';
        this.streamElement = document.getElementById('camera-stream');
        this.toggleButton = document.getElementById('toggle-camera');
        this.fullscreenButton = document.getElementById('fullscreen-button');
        this.controlIcon = document.getElementById('control-icon');
        this.statusText = document.querySelector('.status-text');
        
        this.initializeEventListeners();
        this.renderControlIcon(false);
        this.checkCameraStatus();
        this.subscribeToEvents();
    }
    renderControlIcon(isActive) {
        if (!this.controlIcon) return;
        const playSvg = '<svg class="play-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
        const pauseSvg = '<svg class="pause-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
        this.controlIcon.innerHTML = isActive ? pauseSvg : playSvg;
    }

    
    initializeEventListeners() {
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => this.toggleCamera());
        }
        
        if (this.fullscreenButton) {
            this.fullscreenButton.addEventListener('click', () => this.toggleFullscreen());
        }
    }
    
    async checkCameraStatus() {
        try {
            const response = await ApiClient.get('/camera/status');
            this.updateCameraStatus(response.active);
            this.cameraType = response.camera_type;
            this.updateCameraType(response.camera_type);
            
            if (response.camera_type === 'DO3THINK_CAMERA') {
                if (response.active) {
                    this.startStream();
                }
            }
        } catch (error) {
            console.error('Error checking camera status:', error);
        }
    }
    
    async startCamera() {
        try {
            this.setButtonLoading(this.toggleButton, true);
            const response = await ApiClient.post('/camera/start');
            
            if (response.status === 'success') {
                this.updateCameraStatus(true);
                this.clearFrozenFrame();
                this.startStream();
                
            } else {
                
            }
        } catch (error) {
            console.error('Error starting camera:', error);
        } finally {
            this.setButtonLoading(this.toggleButton, false);
        }
    }
    
    async toggleCamera() {
        if (this.isStreaming) {
            await this.stopCamera();
        } else {
            await this.startCamera();
        }
    }
    
    async stopCamera() {
        try {
            this.setButtonLoading(this.toggleButton, true);
            const response = await ApiClient.post('/camera/stop');
            
            if (response.status === 'success') {
                this.updateCameraStatus(false);
                this.freezeLastFrame();
                
            } else {
                
            }
        } catch (error) {
            console.error('Error stopping camera:', error);
        } finally {
            this.setButtonLoading(this.toggleButton, false);
        }
    }
    
    startStream() {
        if (this.streamElement) {
            this.streamElement.src = '/api/camera/stream?' + new Date().getTime();
            this.streamElement.style.display = 'block';
            this.isStreaming = true;
            
            this.streamElement.onload = () => {
                console.log('Video stream started');
            };
            
            this.streamElement.onerror = () => {
                console.error('Video stream error');
                this.isStreaming = false;
            };
        }
    }
    
    stopStream() {
        if (this.streamElement) {
            this.streamElement.src = '';
            this.streamElement.style.display = 'none';
            this.isStreaming = false;
        }
    }

    freezeLastFrame() {
        if (!this.streamElement) return;
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const w = this.streamElement.naturalWidth || this.streamElement.width;
            const h = this.streamElement.naturalHeight || this.streamElement.height;
            if (!w || !h) {
                this.stopStream();
                return;
            }
            canvas.width = w;
            canvas.height = h;
            ctx.drawImage(this.streamElement, 0, 0, w, h);
            const dataUrl = canvas.toDataURL('image/jpeg');
            this.streamElement.src = dataUrl;
            this.streamElement.style.display = 'block';
            this.isStreaming = false;
        } catch (e) {
            console.error('freezeLastFrame error', e);
            this.stopStream();
        }
    }

    isFrozenFrame() {
        if (!this.streamElement) return false;
        const src = this.streamElement.getAttribute('src') || '';
        return src.startsWith('data:');
    }

    clearFrozenFrame() {
        if (!this.streamElement) return;
        if (this.isFrozenFrame()) {
            this.streamElement.src = '';
            this.streamElement.style.display = 'none';
        }
    }
    
    updateCameraStatus(isActive) {
        this.isStreaming = isActive;
        
        this.renderControlIcon(isActive);
        
        if (this.toggleButton) {
            this.toggleButton.title = isActive ? 'Остановить обработку' : 'Запустить обработку';
        }
        
        const statusDot = document.querySelector('.status-dot');
        if (statusDot) {
            statusDot.style.backgroundColor = isActive ? '#059669' : '#dc2626';
        }
        
        if (this.statusText) {
            this.statusText.textContent = isActive ? 'Онлайн трансляция' : 'Нет сигнала';
        }
    }
    
    updateCameraType(type) {
        this.cameraType = type;
    }

    subscribeToEvents() {
        const { eventBus } = window.__pdCore || {};
        if (!eventBus) return;
        eventBus.on('camera:status', data => this.updateCameraStatus(!!data.active));
    }
    
    setButtonLoading(button, isLoading) {
        if (!button) return;
        
        if (isLoading) {
            button.disabled = true;
            button.style.opacity = '0.6';
            button.style.cursor = 'not-allowed';
        } else {
            button.disabled = false;
            button.style.opacity = '1';
            button.style.cursor = 'pointer';
        }
    }
    
    refresh() {
        this.checkCameraStatus();
    }
    
    
    toggleFullscreen() {
        const videoContainer = document.querySelector('.video-container');
        if (!videoContainer) return;
        
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            videoContainer.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.cameraManager = new CameraManager();
});
