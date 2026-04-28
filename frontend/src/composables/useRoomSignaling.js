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
        console.log('[useRoomSignaling] message type:', type, 'user_id:', user_id);
        switch (type) {
            case 'user_join':
                console.debug('[useRoomSignaling] user_join', user_id);
                handleUserJoin(user_id);
                break;
            case 'user_leave': {
                console.debug('[useRoomSignaling] user_leave', user_id);
                const pc = peerConnections.value[user_id];
                if (pc) {
                    try { pc.close(); } catch (e) { }
                    delete peerConnections.value[user_id];
                }
                delete videoStreams.value[user_id];
                break;
            }
            case 'room_closed':
                console.debug('[useRoomSignaling] room_closed', data);
                break;
            case 'offer':
                console.log('[useRoomSignaling] receiving offer from', user_id);
                handleOffer(user_id, data);
                break;
            case 'answer':
                console.log('[useRoomSignaling] receiving answer from', user_id);
                handleAnswer(user_id, data);
                break;
            case 'ice_candidate':
                console.log('[useRoomSignaling] receiving ice_candidate from', user_id);
                handleIceCandidate(user_id, data);
                break;
            default:
            // noop
        }
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
                    try { handleMessage(message); } catch (e) { console.error('handleMessage', e); }
                    onRoomClosed?.(message);
                } else {
                    try { handleMessage(message); } catch (e) { console.error('handleMessage', e); }
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
