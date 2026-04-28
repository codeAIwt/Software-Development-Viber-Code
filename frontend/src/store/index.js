import { defineStore } from "pinia";

export const useUiStore = defineStore("ui", {
  state: () => ({
    toast: { message: "", visible: false },
    pendingDuration: null,
  }),
  actions: {
    showToast(message) {
      this.toast = { message, visible: true };
      window.setTimeout(() => {
        this.toast.visible = false;
      }, 2400);
    },
    setPendingDuration(duration) {
      this.pendingDuration = duration;
    },
    clearPendingDuration() {
      this.pendingDuration = null;
    },
  },
});
