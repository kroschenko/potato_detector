class TabManager {
    constructor() {
        this.activeTab = 'statistics';
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabContents = document.querySelectorAll('.tab-content');
        this.socket = null;
        
        this.initializeTabs();
        this.initializeWebSocket();
    }
    
    initializeTabs() {
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.currentTarget.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
    }
    
    switchTab(tabName) {
        this.tabButtons.forEach(button => {
            button.classList.remove('active');
            const isActive = button.getAttribute('data-tab') === tabName;
            button.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        this.tabContents.forEach(content => {
            content.classList.remove('active');
            content.toggleAttribute('hidden', content.id !== `${tabName}-tab`);
        });

        const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
        const activeContent = document.getElementById(`${tabName}-tab`);
        
        if (activeButton && activeContent) {
            activeButton.classList.add('active');
            activeContent.classList.add('active');
            activeContent.removeAttribute('hidden');
            this.activeTab = tabName;
            
            this.handleTabChange(tabName);
        }
    }
    
    handleTabChange(tabName) {
        switch (tabName) {
            case 'statistics':
                if (window.statisticsManager) {
                    window.statisticsManager.refresh();
                }
                ApiClient.post('/annotations/enabled', { enabled: false }).catch(() => {});
                break;
            case 'camera':
                if (window.cameraManager) {
                    window.cameraManager.refresh();
                }
                if (window.logsManager) {
                    window.logsManager.refresh();
                }
                ApiClient.post('/annotations/enabled', { enabled: true }).catch(() => {});
                break;
            case 'configuration':
                if (window.configManager) {
                    window.configManager.loadConfiguration();
                }
                break;
        }
    }
    
    initializeWebSocket() {
        try {
            const { eventBus } = window.__pdCore || {};
            const { socket } = window.__pdCore || {};
            if (!eventBus || !socket) return;
            this.socket = socket;
            eventBus.on('stats:update', data => {
                if (window.statisticsManager) window.statisticsManager.updateStatistics(data);
            });
            eventBus.on('logs:add', data => {
                if (window.logsManager) window.logsManager.addLogEntry(data);
            });
            eventBus.on('system:status', s => this.updateSystemStatus(s.online ? 'Online' : 'Offline'));
            eventBus.on('camera:status', d => this.updateCameraStatus(d.active ? 'Connected' : 'Disconnected'));
        } catch (e) {
            console.error('WebSocket init failed', e);
        }
    }
    
    updateSystemStatus(status) {
        console.log(`System Status: ${status}`);
    }
    
    updateCameraStatus(status) {
        console.log(`Camera Status: ${status}`);
    }
    
    getSocket() {
        return this.socket;
    }
}

class ApiClient {
    static async get(endpoint) {
        try {
            const response = await fetch(`/api${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API GET error:', error);
            throw error;
        }
    }
    
    static async post(endpoint, data = {}) {
        try {
            const response = await fetch(`/api${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API POST error:', error);
            throw error;
        }
    }
}


const initializeApplication = () => {
    window.tabManager = new TabManager();
    window.ApiClient = ApiClient;
    const setEnabled = () => ApiClient.post('/annotations/enabled', { enabled: document.visibilityState === 'visible' && window.tabManager.activeTab === 'camera' }).catch(() => {});
    document.addEventListener('visibilitychange', setEnabled);
    setEnabled();
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApplication);
} else {
    initializeApplication();
}
