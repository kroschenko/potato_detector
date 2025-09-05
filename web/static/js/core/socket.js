import { eventBus } from './eventBus.js';

export function createSocket() {
    const socket = io();
    socket.on('connect', () => eventBus.emit('system:status', { online: true }));
    socket.on('disconnect', () => eventBus.emit('system:status', { online: false }));
    socket.on('statistics_update', data => eventBus.emit('stats:update', data));
    socket.on('log_entry', data => eventBus.emit('logs:add', data));
    return socket;
}


