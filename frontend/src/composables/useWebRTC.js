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
            console.log('[WebRTC] ontrack triggered for', userId, 'streams:', event.streams);
            if (event.streams && event.streams[0] && event.streams[0].getAudioTracks) {
                console.log('[WebRTC] Setting video stream for', userId);
                const newStreams = { ...videoStreams.value, [userId]: event.streams[0] };
                console.log('[WebRTC] videoStreams before:', Object.keys(videoStreams.value));
                videoStreams.value = newStreams;
                console.log('[WebRTC] videoStreams after:', Object.keys(videoStreams.value));
            }
        };

        peerConnections.value = { ...peerConnections.value, [userId]: pc };
        return pc;
    }

    async function handleUserJoin(userId) {
        console.log('[WebRTC] handleUserJoin', userId);
        const pc = createPeerConnection(userId);
        const local = getLocalStream?.();
        console.log('[WebRTC] local stream:', local);
        if (local) {
            local.getTracks().forEach(track => pc.addTrack(track, local));
        }
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        console.log('[WebRTC] sending offer to', userId);
        sendSignal?.({ type: 'offer', target_user_id: userId, data: offer });
    }

    async function handleOffer(userId, offer) {
        console.log('[WebRTC] handleOffer from', userId);
        const pc = createPeerConnection(userId);
        const local = getLocalStream?.();
        if (local) local.getTracks().forEach(track => pc.addTrack(track, local));
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        console.log('[WebRTC] sending answer to', userId);
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
        console.log('[WebRTC] handleIceCandidate from', userId);
        const pc = peerConnections.value[userId];
        if (pc) {
            await pc.addIceCandidate(new IceCandidate(candidate));
        }
    }

    function cleanupPeerConnections() {
        Object.values(peerConnections.value).forEach(pc => pc.close());
        peerConnections.value = {};
        videoStreams.value = {};
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
