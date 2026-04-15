import { defineStore } from "pinia";

export const useUiStore = defineStore("ui", {
  state: () => ({ toast: { message: "", visible: false } }),
  actions: {
    showToast(message) {
      this.toast = { message, visible: true };
      window.setTimeout(() => {
        this.toast.visible = false;
      }, 2400);
    },
  },
});
