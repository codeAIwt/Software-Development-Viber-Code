import { useWebSocket } from './useWebSocket';
import { useWebRTC } from './useWebRTC';

export function useRoomSignaling(getLocalStream) {
    const { ws, connect, send, close } = useWebSocket();
    const {
        peerConnections,
        videoStreams,
        handleUserJoin,
        handleOffer,
        handleAnswer,
        handleIceCandidate,
        cleanupPeerConnections,
    } = useWebRTC((signal) => send(signal), getLocalStream);

    function handleMessage(message) {
        const { type, user_id, data } = message || {};
        switch (type) {
            case 'user_join':
                handleUserJoin(user_id);
                break;
            case 'user_leave': {
                const pc = peerConnections.value.get(user_id);
                if (pc) {
                    try { pc.close(); } catch (e) { }
                    peerConnections.value.delete(user_id);
                }
                videoStreams.value.delete(user_id);
                break;
            }
            case 'offer':
                handleOffer(user_id, data);
                break;
            case 'answer':
                handleAnswer(user_id, data);
                break;
            case 'ice_candidate':
                handleIceCandidate(user_id, data);
                break;
            default:
            // noop
        }
    }

    function connectRoom(roomId, userId, handlers = {}) {
        const { onOpen, onMessage, onClose, onError } = handlers;
        connect(roomId, userId, {
            onOpen: () => {
                try { send({ type: 'join', user_id: userId, room_id: roomId }); } catch (e) { }
                onOpen?.();
            },
            onMessage: (message) => {
                try { handleMessage(message); } catch (e) { console.error('handleMessage', e); }
                onMessage?.(message);
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
    }

    return {
        ws,
        videoStreams,
        peerConnections,
        connectRoom,
        closeRoom,
        sendSignal: send,
        cleanupPeerConnections,
    };
}
