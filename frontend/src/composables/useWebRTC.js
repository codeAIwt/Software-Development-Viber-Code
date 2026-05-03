import { ref } from 'vue';

export function useWebRTC(sendSignal, getLocalStream) {
    const peerConnections = ref({});
    const videoStreams = ref({});

    function createPeerConnection(userId) {
        const pc = new RTCPeerConnection({
            iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]
        });

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                sendSignal?.({ type: 'ice_candidate', target_user_id: userId, data: event.candidate });
            }
        };

        pc.ontrack = (event) => {
            if (event.streams && event.streams[0]) {
                const newStream = event.streams[0];
                const currentStream = videoStreams.value[userId];
                if (currentStream !== newStream) {
                    console.log('[WebRTC] ontrack for', userId, 'stream id:', newStream.id, 'active:', newStream.active);
                    videoStreams.value = { ...videoStreams.value, [userId]: newStream };
                }
            }
        };

        pc.onconnectionstatechange = () => {
            console.log('[WebRTC] connection state for', userId, ':', pc.connectionState);
        };

        peerConnections.value = { ...peerConnections.value, [userId]: pc };
        return pc;
    }

    async function handleUserJoin(userId) {
        console.log('[WebRTC] handleUserJoin', userId, 'existing connections:', Object.keys(peerConnections.value).length);
        const pc = createPeerConnection(userId);
        const local = getLocalStream?.();
        console.log('[WebRTC] local stream for addTrack:', local?.id, 'active:', local?.active);
        if (local) {
            local.getTracks().forEach(track => {
                console.log('[WebRTC] adding track:', track.id, 'kind:', track.kind, 'enabled:', track.enabled);
                pc.addTrack(track, local);
            });
        }
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        sendSignal?.({ type: 'offer', target_user_id: userId, data: offer });
    }

    async function handleOffer(userId, offer) {
        console.log('[WebRTC] handleOffer from', userId);
        const pc = createPeerConnection(userId);
        const local = getLocalStream?.();
        console.log('[WebRTC] local stream for addTrack:', local?.id);
        if (local) local.getTracks().forEach(track => pc.addTrack(track, local));
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        sendSignal?.({ type: 'answer', target_user_id: userId, data: answer });
    }

    async function handleAnswer(userId, answer) {
        console.log('[WebRTC] handleAnswer from', userId);
        const pc = peerConnections.value[userId];
        if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
        }
    }

    async function handleIceCandidate(userId, candidate) {
        const pc = peerConnections.value[userId];
        if (pc) {
            await pc.addIceCandidate(new RTCIceCandidate(candidate));
        }
    }

    function cleanupPeerConnections() {
        console.log('[WebRTC] cleanupPeerConnections called, connections:', Object.keys(peerConnections.value).length);
        if (Object.keys(peerConnections.value).length === 0) {
            return;
        }
        Object.values(peerConnections.value).forEach(pc => pc.close());
        peerConnections.value = {};
        videoStreams.value = {};
    }

    return {
        peerConnections,
        videoStreams,
        handleUserJoin,
        handleOffer,
        handleAnswer,
        handleIceCandidate,
        cleanupPeerConnections,
    };
}
