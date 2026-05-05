/**
 * 事件总线 - 房间成员变化事件管理
 * 职责：解耦房间成员变化与视频连接管理
 */

const EventTypes = {
    MEMBER_JOINED: 'member_joined',
    MEMBER_LEFT: 'member_left',
    ROOM_CLOSED: 'room_closed'
};

class RoomMemberEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event).add(callback);
        console.log('[RoomMemberEventBus] listener registered for', event, 'total listeners:', this.listeners.get(event).size);
        return () => this.off(event, callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).delete(callback);
            console.log('[RoomMemberEventBus] listener removed for', event, 'remaining:', this.listeners.get(event).size);
        }
    }

    emit(event, data) {
        console.log('[RoomMemberEventBus] emit:', event, 'data:', JSON.stringify(data));
        console.log('[RoomMemberEventBus] listeners for', event, ':', this.listeners.get(event)?.size || 0);
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (err) {
                    console.error('[RoomMemberEventBus] callback error:', err);
                }
            });
        } else {
            console.log('[RoomMemberEventBus] no listeners for event:', event);
        }
    }
}

const roomMemberEventBus = new RoomMemberEventBus();

export { EventTypes, roomMemberEventBus };
