/**
 * 信令服务 - 独立模块
 * 职责：WebSocket 连接管理、消息发送/接收、信令交换
 * 与 WebRTC、视频流管理完全解耦
 */

import { ref } from 'vue';

export function createSignalingService() {
    const ws = ref(null);
    const connected = ref(false);

    let onMessageCallback = null;
    let onOpenCallback = null;
    let onCloseCallback = null;
    let onErrorCallback = null;

    function connect(roomId, userId, callbacks = {}) {
        console.log('[Signaling] connect called, roomId:', roomId, 'userId:', userId);

        onMessageCallback = callbacks.onMessage;
        onOpenCallback = callbacks.onOpen;
        onCloseCallback = callbacks.onClose;
        onErrorCallback = callbacks.onError;

        if (ws.value && ws.value.readyState === WebSocket.OPEN) {
            console.log('[Signaling] existing WebSocket is OPEN, closing first');
            ws.value.close();
        }

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/room/${roomId}?user_id=${userId}`;
        console.log('[Signaling] creating WebSocket:', wsUrl);
        ws.value = new WebSocket(wsUrl);

        ws.value.onopen = () => {
            console.log('[Signaling] WebSocket onopen');
            connected.value = true;
            onOpenCallback?.();
        };

        ws.value.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('[Signaling] onmessage:', message.type, message.user_id);
                console.log('[Signaling] onmessage full:', JSON.stringify(message));
                console.log('[Signaling] ws.readyState:', ws.value?.readyState);
                console.log('[Signaling] connected.value:', connected.value);
                onMessageCallback?.(message);
            } catch (err) {
                console.error('[Signaling] parse error', err);
            }
        };

        ws.value.onclose = () => {
            console.log('[Signaling] WebSocket onclose');
            connected.value = false;
            console.log('[Signaling] calling onClose callback');
            onCloseCallback?.();
        };

        ws.value.onerror = (err) => {
            onErrorCallback?.(err);
        };
    }

    function send(message) {
        if (!ws.value || ws.value.readyState === WebSocket.CLOSING || ws.value.readyState === WebSocket.CLOSED) {
            return false;
        }
        try {
            ws.value.send(JSON.stringify(message));
            return true;
        } catch (err) {
            console.error('[Signaling] send error', err);
            return false;
        }
    }

    function sendOffer(targetUserId, offer) {
        return send({
            type: 'offer',
            target_user_id: targetUserId,
            data: offer
        });
    }

    function sendAnswer(targetUserId, answer) {
        return send({
            type: 'answer',
            target_user_id: targetUserId,
            data: answer
        });
    }

    function sendIceCandidate(targetUserId, candidate) {
        return send({
            type: 'ice_candidate',
            target_user_id: targetUserId,
            data: candidate
        });
    }

    function sendAiDetection(detectionData) {
        return send({
            type: 'ai_detection',
            data: detectionData
        });
    }

    function close() {
        if (ws.value) {
            try {
                ws.value.close();
            } catch (err) { }
        }
        ws.value = null;
        connected.value = false;
    }

    function isConnected() {
        return connected.value && ws.value?.readyState === WebSocket.OPEN;
    }

    return {
        ws,
        connected,
        connect,
        send,
        sendOffer,
        sendAnswer,
        sendIceCandidate,
        sendAiDetection,
        close,
        isConnected,
    };
}
