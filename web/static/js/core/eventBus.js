export const eventBus = {
    handlers: new Map(),
    on(event, handler) {
        const list = this.handlers.get(event) || [];
        list.push(handler);
        this.handlers.set(event, list);
    },
    off(event, handler) {
        const list = this.handlers.get(event) || [];
        this.handlers.set(event, list.filter(h => h !== handler));
    },
    emit(event, payload) {
        const list = this.handlers.get(event) || [];
        list.forEach(h => h(payload));
    }
};


