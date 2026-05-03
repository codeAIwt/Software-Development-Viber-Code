/**
 * 房间管理器 - 整合模块
 * 职责：整合视频流管理、WebRTC、信令服务，提供统一的房间操作接口
 */

import { ref } from 'vue';
import { createVideoStreamManager } from './videoStreamManager';
import { createWebRTCConnection } from './webrtcConnection';
import { createSignalingService } from './signalingService';

export function createRoomManager() {
    const videoStreamManager = createVideoStreamManager();
    const webrtcConnection = createWebRTCConnection();
    const signalingService = createSignalingService();

    const aiDetectionResults = ref({});
    const connectionStates = ref({});

    function handleSignalingMessage(message) {
        const { type, user_id, data } = message || {};

        console.log('[RoomManager] handleSignalingMessage raw:', JSON.stringify(message));

        switch (type) {
            case 'user_join':
                console.log('[RoomManager] handling user_join for', user_id);
                handleUserJoin(user_id);
                break;
            case 'user_leave':
                console.log('[RoomManager] handling user_leave for', user_id);
                handleUserLeave(user_id);
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
            default:
                console.log('[RoomManager] unhandled message type:', type);
        }
    }

    function handleUserJoin(remoteUserId) {
        console.log('[RoomManager] handleUserJoin', remoteUserId);

        const localStream = videoStreamManager.getStreamForWebRTC();
        console.log('[RoomManager] localStream:', localStream?.id);

        webrtcConnection.createPeerConnection(remoteUserId, {
            onTrack: (userId, stream) => {
                console.log('[RoomManager] onTrack for', userId, 'stream id:', stream.id);
            },
            onConnectionStateChange: (userId, state) => {
                connectionStates.value = { ...connectionStates.value, [userId]: state };
                console.log('[RoomManager] connection state for', userId, ':', state);
            },
            onIceCandidate: (candidate) => {
                console.log('[RoomManager] sending ICE candidate to', remoteUserId);
                signalingService.sendIceCandidate(remoteUserId, candidate);
            }
        });

        if (localStream) {
            console.log('[RoomManager] adding tracks to PC');
            localStream.getTracks().forEach(track => {
                console.log('[RoomManager] adding track:', track.id, 'kind:', track.kind);
                webrtcConnection.addLocalTrack(remoteUserId, track, localStream);
            });
        } else {
            console.log('[RoomManager] ERROR: localStream is null!');
        }

        webrtcConnection.createOffer(remoteUserId).then(offer => {
            if (offer) {
                console.log('[RoomManager] sending offer to', remoteUserId, 'type:', offer.type);
                signalingService.sendOffer(remoteUserId, offer);
            } else {
                console.log('[RoomManager] ERROR: offer is null!');
            }
        });
    }

    function handleOffer(remoteUserId, offer) {
        console.log('[RoomManager] handleOffer from', remoteUserId);
        if (!offer) {
            console.error('[RoomManager] handleOffer: offer is null');
            return;
        }
        console.log('[RoomManager] offer type:', offer.type);

        const localStream = videoStreamManager.getStreamForWebRTC();

        webrtcConnection.createPeerConnection(remoteUserId, {
            onTrack: (userId, stream) => {
                console.log('[RoomManager] onTrack for', userId, 'stream id:', stream.id);
            },
            onConnectionStateChange: (userId, state) => {
                connectionStates.value = { ...connectionStates.value, [userId]: state };
            },
            onIceCandidate: (candidate) => {
                signalingService.sendIceCandidate(remoteUserId, candidate);
            }
        });

        if (localStream) {
            localStream.getTracks().forEach(track => {
                webrtcConnection.addLocalTrack(remoteUserId, track, localStream);
            });
        }

        webrtcConnection.setRemoteDescription(remoteUserId, offer).then(() => {
            return webrtcConnection.createAnswer(remoteUserId);
        }).then(answer => {
            if (answer) {
                console.log('[RoomManager] sending answer to', remoteUserId, 'type:', answer.type);
                signalingService.sendAnswer(remoteUserId, answer);
            }
        });
    }

    function handleAnswer(remoteUserId, answer) {
        console.log('[RoomManager] handleAnswer from', remoteUserId);
        if (!answer) {
            console.error('[RoomManager] handleAnswer: answer is null');
            return;
        }
        console.log('[RoomManager] answer type:', answer.type);
        webrtcConnection.setRemoteDescription(remoteUserId, answer);
    }

    function handleIceCandidate(remoteUserId, candidate) {
        console.log('[RoomManager] handleIceCandidate from', remoteUserId);
        webrtcConnection.addIceCandidate(remoteUserId, candidate);
    }

    function handleUserLeave(remoteUserId) {
        console.log('[RoomManager] handleUserLeave', remoteUserId);
        console.log('[RoomManager] remoteStreams before leave:', JSON.stringify(Object.keys(webrtcConnection.remoteStreams.value)));

        webrtcConnection.closePeerConnection(remoteUserId);

        console.log('[RoomManager] remoteStreams after leave:', JSON.stringify(Object.keys(webrtcConnection.remoteStreams.value)));

        const newResults = { ...aiDetectionResults.value };
        delete newResults[remoteUserId];
        aiDetectionResults.value = newResults;
    }

    async function connectRoom(roomId, userId, callbacks = {}) {
        await videoStreamManager.initCamera();

        return new Promise((resolve) => {
            signalingService.connect(roomId, userId, {
                onOpen: () => {
                    console.log('[RoomManager] WebSocket connected');
                    signalingService.send({ type: 'join', user_id: userId, room_id: roomId });
                    callbacks.onOpen?.();
                    resolve();
                },
                onMessage: (message) => {
                    handleSignalingMessage(message);
                },
                onClose: () => {
                    console.log('[RoomManager] WebSocket closed');
                    callbacks.onClose?.();
                },
                onError: (err) => {
                    console.error('[RoomManager] WebSocket error', err);
                    callbacks.onError?.(err);
                }
            });
        });
    }

    function sendAiDetection(detectionData) {
        signalingService.sendAiDetection(detectionData);
    }

    function disconnectRoom() {
        console.log('[RoomManager] disconnectRoom called');
        webrtcConnection.closeAll();
        signalingService.close();
        videoStreamManager.stopCamera();
        aiDetectionResults.value = {};
        connectionStates.value = {};
        console.log('[RoomManager] disconnectRoom completed');
    }

    return {
        // Video Stream Manager
        videoStreamManager,

        // WebRTC Connection
        webrtcConnection,

        // Signaling Service
        signalingService,

        // Shared State
        aiDetectionResults,
        connectionStates,

        // Remote Streams (for rendering)
        remoteStreams: webrtcConnection.remoteStreams,

        // Methods
        connectRoom,
        disconnectRoom,
        sendAiDetection,
        handleUserLeave,
    };
}
