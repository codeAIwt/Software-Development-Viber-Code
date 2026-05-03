import { ref } from 'vue';
import { useWebSocket } from './useWebSocket';
import { useWebRTC } from './useWebRTC';

export function useRoomSignaling(getProcessedStream) {
    const { ws, connect, send, close } = useWebSocket();
    const {
        peerConnections,
        videoStreams,
        handleUserJoin,
        handleOffer,
        handleAnswer,
        handleIceCandidate,
        cleanupPeerConnections,
    } = useWebRTC((signal) => send(signal), getProcessedStream);

    const aiDetectionResults = ref({});

    function handleMessage(message) {
        const { type, user_id, data } = message || {};
        switch (type) {
            case 'user_join':
                handleUserJoin(user_id);
                break;
            case 'user_leave': {
                const pc = peerConnections.value[user_id];
                if (pc) {
                    try { pc.close(); } catch (e) { }
                    delete peerConnections.value[user_id];
                }
                delete videoStreams.value[user_id];
                delete aiDetectionResults.value[user_id];
                break;
            }
            case 'room_closed':
                break;
            case 'offer':
                handleOffer(user_id, data);
                break;
            case 'answer':
                handleAnswer(user_id, data);
                break;
            case 'ice_candidate':
                handleIceCandidate(user_id, data);
                break;
            case 'ai_detection':
                if (user_id) {
                    aiDetectionResults.value = {
                        ...aiDetectionResults.value,
                        [user_id]: data
                    };
                }
                break;
        }
    }

    function sendAiDetection(detectionData) {
        send({
            type: 'ai_detection',
            data: detectionData
        });
    }

    function connectRoom(roomId, userId, handlers = {}) {
        const { onOpen, onMessage, onClose, onError, onRoomClosed } = handlers;
        connect(roomId, userId, {
            onOpen: () => {
                try { send({ type: 'join', user_id: userId, room_id: roomId }); } catch (e) { }
                onOpen?.();
            },
            onMessage: (message) => {
                if (message?.type === 'room_closed') {
                    try { handleMessage(message); } catch (e) { }
                    onRoomClosed?.(message);
                } else {
                    try { handleMessage(message); } catch (e) { }
                    onMessage?.(message);
                }
            },
            onClose: () => {
                try { cleanupPeerConnections(); } catch (e) { }
                onClose?.();
            },
            onError: (err) => onError?.(err),
        });
    }

    function closeRoom() {
        try { close(); } catch (e) { }
        try { cleanupPeerConnections(); } catch (e) { }
        aiDetectionResults.value = {};
    }

    return {
        ws,
        videoStreams,
        peerConnections,
        aiDetectionResults,
        connectRoom,
        closeRoom,
        sendSignal: send,
        sendAiDetection,
        cleanupPeerConnections,
    };
}
