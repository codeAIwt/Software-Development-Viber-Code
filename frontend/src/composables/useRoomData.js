import { ref } from 'vue';
import * as studyRoomApi from '../api/studyRoom';
import * as userApi from '../api/user';

export function useRoomData() {
    const roomInfo = ref({
        creator_id: '',
        created_ts_ms: '',
        theme: '',
        max_people: 0,
        current_people: 0,
        status: '',
        tags: [],
        users: []
    });

    const userInfoMap = ref(new Map());
    const loadingUserInfo = ref(false);
    const creatorInfo = ref(null);
    const loadingCreatorInfo = ref(false);

    const roomInfoTimer = ref(null);

    async function getUserInfo(userId) {
        if (userInfoMap.value.has(userId)) return userInfoMap.value.get(userId);
        try {
            const { data } = await userApi.fetchUserInfo(userId);
            if (data.code === 200) {
                userInfoMap.value.set(userId, data.data);
                return data.data;
            }
        } catch (e) {
            console.error('getUserInfo failed', e);
        }
        return null;
    }

    async function fetchRoomInfo(roomId) {
        try {
            const { data } = await studyRoomApi.getRoomInfo(roomId);
            if (data.code === 200) {
                roomInfo.value = data.data;
                if (roomInfo.value.creator_id) {
                    loadingCreatorInfo.value = true;
                    const { data: creatorData } = await userApi.fetchUserInfo(roomInfo.value.creator_id);
                    if (creatorData.code === 200) creatorInfo.value = creatorData.data;
                    loadingCreatorInfo.value = false;
                }

                if (roomInfo.value.users && roomInfo.value.users.length > 0) {
                    loadingUserInfo.value = true;
                    for (const userId of roomInfo.value.users) {
                        await getUserInfo(userId);
                    }
                    loadingUserInfo.value = false;
                }
                return { ok: true, closed: roomInfo.value.status === 'closed' };
            }
            return { ok: false };
        } catch (e) {
            const status = e.response?.status;
            return { ok: false, status };
        }
    }

    function startPolling(roomId, intervalMs = 5000, onClosed, isLeavingGetter = null) {
        if (roomInfoTimer.value) clearInterval(roomInfoTimer.value);
        let consecutive404Count = 0;
        const MAX_404_BEFORE_CLOSED = 3;

        roomInfoTimer.value = setInterval(async () => {
            const res = await fetchRoomInfo(roomId);

            if (isLeavingGetter && isLeavingGetter()) {
                clearInterval(roomInfoTimer.value);
                roomInfoTimer.value = null;
                consecutive404Count = 0;
                return;
            }

            if (res.ok && res.closed) {
                clearInterval(roomInfoTimer.value);
                roomInfoTimer.value = null;
                consecutive404Count = 0;
                onClosed?.();
                return;
            }

            if (res.status === 404) {
                consecutive404Count++;
                if (consecutive404Count >= MAX_404_BEFORE_CLOSED) {
                    clearInterval(roomInfoTimer.value);
                    roomInfoTimer.value = null;
                    consecutive404Count = 0;
                    if (!isLeavingGetter || !isLeavingGetter()) {
                        onClosed?.();
                    }
                }
            } else {
                consecutive404Count = 0;
            }
        }, intervalMs);
    }

    function stopPolling() {
        if (roomInfoTimer.value) {
            clearInterval(roomInfoTimer.value);
            roomInfoTimer.value = null;
        }
    }

    async function leaveRoom(roomId) {
        return studyRoomApi.leaveRoom(roomId);
    }

    async function updateRoom(roomId, theme) {
        return studyRoomApi.updateRoom(roomId, theme);
    }

    async function destroyRoom(roomId) {
        return studyRoomApi.destroyRoom(roomId);
    }

    return {
        roomInfo,
        userInfoMap,
        loadingUserInfo,
        creatorInfo,
        loadingCreatorInfo,
        fetchRoomInfo,
        startPolling,
        stopPolling,
        leaveRoom,
        updateRoom,
        destroyRoom,
    };
}
