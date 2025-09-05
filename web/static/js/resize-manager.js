class ResizeManager {
    constructor() {
        this.resizeHandle = null;
        this.cameraPanel = null;
        this.logsPanel = null;
        this.container = null;
        
        this.isResizing = false;
        this.startX = 0;
        this.startWidth = 0;
        this.minCameraWidth = 300;
        this.minLogsWidth = 200;
        this.defaultLogsWidth = 360;
        
        this.initializeElements();
    }
    
    initializeElements() {
        this.resizeHandle = document.getElementById('resize-handle');
        this.cameraPanel = document.querySelector('.camera-panel');
        this.logsPanel = document.querySelector('.logs-panel');
        this.container = document.querySelector('.camera-logs-container');
        
        if (this.resizeHandle && this.cameraPanel && this.logsPanel && this.container) {
            this.initializeResizeHandler();
            this.setupResponsiveBehavior();
        } else {
            setTimeout(() => this.initializeElements(), 100);
        }
    }
    
    initializeResizeHandler() {
        if (!this.resizeHandle || !this.cameraPanel || !this.logsPanel) {
            console.warn('Resize elements not found');
            return;
        }
        
        this.resizeHandle.addEventListener('mousedown', (e) => this.startResize(e));
        document.addEventListener('mousemove', (e) => this.handleResize(e));
        document.addEventListener('mouseup', () => this.stopResize());
        
        this.resizeHandle.addEventListener('touchstart', (e) => this.startResize(e.touches[0]));
        document.addEventListener('touchmove', (e) => this.handleResize(e.touches[0]));
        document.addEventListener('touchend', () => this.stopResize());
    }
    
    startResize(e) {
        this.isResizing = true;
        this.startX = e.clientX;
        this.startWidth = this.logsPanel.offsetWidth;
        
        document.body.style.cursor = this.getCursorStyle();
        document.body.style.userSelect = 'none';
        
        e.preventDefault();
    }
    
    handleResize(e) {
        if (!this.isResizing) return;
        
        const deltaX = e.clientX - this.startX;
        const containerWidth = this.container.offsetWidth;
        const newLogsWidth = this.startWidth - deltaX;
        const newCameraWidth = containerWidth - newLogsWidth - this.resizeHandle.offsetWidth;
        
        if (newLogsWidth >= this.minLogsWidth && newCameraWidth >= this.minCameraWidth) {
            this.logsPanel.style.width = `${newLogsWidth}px`;
            this.cameraPanel.style.flex = 'none';
            this.cameraPanel.style.width = `${newCameraWidth}px`;
        }
        
        e.preventDefault();
    }
    
    stopResize() {
        if (!this.isResizing) return;
        
        this.isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    }
    
    getCursorStyle() {
        const isMobile = window.innerWidth <= 768;
        return isMobile ? 'row-resize' : 'col-resize';
    }
    
    setupResponsiveBehavior() {
        const handleResize = () => {
            if (window.innerWidth <= 768) {
                this.logsPanel.style.width = '';
                this.cameraPanel.style.width = '';
                this.cameraPanel.style.flex = '';
            } else {
                if (!this.logsPanel.style.width) {
                    this.logsPanel.style.width = '360px';
                }
            }
        };
        
        window.addEventListener('resize', handleResize);
        handleResize();
    }
    
    resetLayout() {
        this.logsPanel.style.width = '360px';
        this.cameraPanel.style.flex = '1';
        this.cameraPanel.style.width = '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.resizeManager = new ResizeManager();
});
