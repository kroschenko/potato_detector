class LogsManager {
    constructor() {
        this.logsContainer = document.getElementById('logs-output');
        this.clearButton = document.getElementById('clear-logs');
        this.exportButton = document.getElementById('export-logs');
        this.maxLogEntries = 1000;
        this.logEntries = [];
        
        this.initializeEventListeners();
        this.loadInitialLogs();
        this.subscribeToEvents();
    }
    
    initializeEventListeners() {
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => this.clearLogs());
        }
        
        if (this.exportButton) {
            this.exportButton.addEventListener('click', () => this.exportLogs());
        }
    }
    
    async loadInitialLogs() {
        try {
            if (this.logsContainer) {
                this.logsContainer.innerHTML = '';
            }
            const recentLogs = await window.ApiClient.get('/logs/recent');
            if (Array.isArray(recentLogs)) {
                recentLogs.forEach(log => this.addLogEntry(log));
            }
        } catch (error) {
            console.error('Error loading initial logs:', error);
        }
    }
    
    addLogEntry(logData) {
        const logEntry = this.createLogEntry(logData);
        this.logEntries.unshift(logData);
        
        if (this.logsContainer) {
            if (this.logsContainer.firstChild) {
                this.logsContainer.insertBefore(logEntry, this.logsContainer.firstChild);
            } else {
                this.logsContainer.appendChild(logEntry);
            }
            this.scrollToTop();
        }
        
        if (this.logEntries.length > this.maxLogEntries) {
            this.removeOldestEntry();
        }
    }
    
    createLogEntry(logData) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${logData.level || 'info'}`;
        
        const timestamp = this.formatTimestamp(logData.timestamp || new Date().toISOString());
        const message = this.escapeHtml(logData.message || '');
        
        logEntry.innerHTML = `
            <span class="log-time">${timestamp}</span>
            <span class="log-message">${message}</span>
        `;
        
        return logEntry;
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('ru-RU', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    removeOldestEntry() {
        if (this.logsContainer && this.logsContainer.lastChild) {
            this.logsContainer.removeChild(this.logsContainer.lastChild);
        }
        this.logEntries.pop();
    }
    
    clearLogs() {
        if (confirm('Вы уверены, что хотите очистить все логи?')) {
            if (this.logsContainer) {
                this.logsContainer.innerHTML = '';
            }
            this.logEntries = [];
            
            this.addLogEntry({
                level: 'info',
                message: 'Логи очищены пользователем',
                timestamp: new Date().toISOString()
            });
            
        }
    }
    
    exportLogs() {
        const logsData = {
            exportTimestamp: new Date().toISOString(),
            totalEntries: this.logEntries.length,
            logs: this.logEntries
        };
        
        const blob = new Blob([JSON.stringify(logsData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `potato-detector-logs-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
    }
    
    
    scrollToTop() {
        if (this.logsContainer) {
            this.logsContainer.scrollTop = 0;
        }
    }
    
    refresh() {
        
    }
    
    subscribeToEvents() {
        const { eventBus } = window.__pdCore || {};
        if (!eventBus) return;
        eventBus.on('logs:add', data => this.addLogEntry(data));
    }
    
}

document.addEventListener('DOMContentLoaded', () => {
    window.logsManager = new LogsManager();
});
