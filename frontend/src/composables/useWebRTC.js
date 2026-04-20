import { ref } from 'vue';

export function useWebRTC(sendSignal, getLocalStream) {
    const peerConnections = ref(new Map());
    const videoStreams = ref(new Map());

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
            videoStreams.value.set(userId, event.streams[0]);
        };

        peerConnections.value.set(userId, pc);
        return pc;
    }

    async function handleUserJoin(userId) {
        const pc = createPeerConnection(userId);
        const local = getLocalStream?.();
        if (local) {
            local.getTracks().forEach(track => pc.addTrack(track, local));
        }
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        sendSignal?.({ type: 'offer', target_user_id: userId, data: offer });
    }

    async function handleOffer(userId, offer) {
        const pc = createPeerConnection(userId);
        const local = getLocalStream?.();
        if (local) local.getTracks().forEach(track => pc.addTrack(track, local));
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        sendSignal?.({ type: 'answer', target_user_id: userId, data: answer });
    }

    async function handleAnswer(userId, answer) {
        const pc = peerConnections.value.get(userId);
        if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
        }
    }

    async function handleIceCandidate(userId, candidate) {
        const pc = peerConnections.value.get(userId);
        if (pc) {
            await pc.addIceCandidate(new RTCIceCandidate(candidate));
        }
    }

    function cleanupPeerConnections() {
        peerConnections.value.forEach(pc => pc.close());
        peerConnections.value.clear();
        videoStreams.value.clear();
    }

    return {
        peerConnections,
        videoStreams,
        createPeerConnection,
        handleUserJoin,
        handleOffer,
        handleAnswer,
        handleIceCandidate,
        cleanupPeerConnections,
    };
}
