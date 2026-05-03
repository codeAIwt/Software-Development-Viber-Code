/**
 * WebRTC 连接管理器 - 独立模块
 * 职责：WebRTC 连接建立、轨道管理、连接状态监控
 * 与信令、视频流管理完全解耦
 */

import { ref } from 'vue';

export function createWebRTCConnection() {
    const peerConnections = ref({});
    const remoteStreams = ref({});

    function createPeerConnection(userId, callbacks) {
        const { onTrack, onConnectionStateChange, onIceCandidate } = callbacks || {};

        const pc = new RTCPeerConnection({
            iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]
        });

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                console.log('[WebRTC] ICE candidate for', userId, ':', event.candidate.type);
                onIceCandidate?.(event.candidate);
            }
        };

        pc.ontrack = (event) => {
            console.log('[WebRTC] ontrack event for', userId, 'streams:', event.streams?.length);
            if (event.streams && event.streams[0]) {
                const newStream = event.streams[0];
                console.log('[WebRTC] ontrack stream id:', newStream.id, 'active:', newStream.active, 'video tracks:', newStream.getVideoTracks().length);
                const currentStream = remoteStreams.value[userId];
                console.log('[WebRTC] currentStream for', userId, ':', currentStream?.id);
                if (currentStream !== newStream) {
                    console.log('[WebRTC] updating remoteStreams for', userId);
                    const newStreams = { ...remoteStreams.value };
                    newStreams[userId] = newStream;
                    remoteStreams.value = newStreams;
                    console.log('[WebRTC] remoteStreams.value after update:', JSON.stringify(Object.keys(remoteStreams.value)));
                    onTrack?.(userId, newStream);
                } else {
                    console.log('[WebRTC] same stream, skipping update');
                }
            } else {
                console.log('[WebRTC] no streams in ontrack event');
            }
        };

        pc.onconnectionstatechange = () => {
            onConnectionStateChange?.(userId, pc.connectionState);
        };

        peerConnections.value = { ...peerConnections.value, [userId]: pc };
        return pc;
    }

    function addLocalTrack(userId, track, localStream) {
        const pc = peerConnections.value[userId];
        if (pc && track) {
            pc.addTrack(track, localStream);
        }
    }

    async function createOffer(userId) {
        const pc = peerConnections.value[userId];
        if (pc) {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            return pc.localDescription;
        }
        return null;
    }

    async function createAnswer(userId) {
        const pc = peerConnections.value[userId];
        if (pc) {
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            return pc.localDescription;
        }
        return null;
    }

    async function setRemoteDescription(userId, description) {
        if (!description) {
            console.error('[WebRTC] setRemoteDescription: description is null or undefined');
            return;
        }
        if (!description.type || !description.sdp) {
            console.error('[WebRTC] setRemoteDescription: invalid description', description);
            return;
        }
        const pc = peerConnections.value[userId];
        if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(description));
        }
    }

    async function addIceCandidate(userId, candidate) {
        if (!candidate) {
            console.error('[WebRTC] addIceCandidate: candidate is null');
            return;
        }
        const pc = peerConnections.value[userId];
        if (pc) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(candidate));
            } catch (err) {
                console.error('[WebRTC] addIceCandidate error', err);
            }
        }
    }

    function closePeerConnection(userId) {
        const pc = peerConnections.value[userId];
        if (pc) {
            pc.close();
            delete peerConnections.value[userId];
            delete remoteStreams.value[userId];
            remoteStreams.value = { ...remoteStreams.value };
        }
    }

    function closeAll() {
        Object.values(peerConnections.value).forEach(pc => pc.close());
        peerConnections.value = {};
        remoteStreams.value = {};
    }

    function getConnection(userId) {
        return peerConnections.value[userId];
    }

    function getRemoteStream(userId) {
        return remoteStreams.value[userId];
    }

    function getConnectionState(userId) {
        const pc = peerConnections.value[userId];
        return pc?.connectionState || 'unknown';
    }

    return {
        peerConnections,
        remoteStreams,
        createPeerConnection,
        addLocalTrack,
        createOffer,
        createAnswer,
        setRemoteDescription,
        addIceCandidate,
        closePeerConnection,
        closeAll,
        getConnection,
        getRemoteStream,
        getConnectionState,
    };
}
