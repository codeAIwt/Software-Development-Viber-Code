import { ref } from 'vue';

export function useWebSocket() {
    const ws = ref(null);

    function connect(roomId, userId, handlers = {}) {
        const { onOpen, onMessage, onClose, onError } = handlers;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/room/${roomId}?user_id=${userId}`;
        ws.value = new WebSocket(wsUrl);

        ws.value.onopen = () => {
            onOpen?.();
        };

        ws.value.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                onMessage?.(message);
            } catch (err) {
                console.error('WS parse error', err);
            }
        };

        ws.value.onclose = () => {
            onClose?.();
        };

        ws.value.onerror = (err) => {
            onError?.(err);
        };
    }

    function send(obj) {
        if (!ws.value) return;
        try {
            ws.value.send(JSON.stringify(obj));
        } catch (err) {
            console.error('WS send error', err);
        }
    }

    function close() {
        if (ws.value) {
            try { ws.value.close(); } catch (err) { }
            ws.value = null;
        }
    }

    return { ws, connect, send, close };
}
