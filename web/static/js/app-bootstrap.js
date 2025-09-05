import { eventBus } from './core/eventBus.js';
import { createSocket } from './core/socket.js';

function bootstrap() {
    const socket = createSocket();
    window.__pdCore = { eventBus, socket };
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
} else {
    bootstrap();
}
