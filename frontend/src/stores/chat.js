import { defineStore } from "pinia";
import { ref } from "vue";
import { apiClient, apiStream } from "../utils/api";

export const useChatStore = defineStore("chat", () => {
  const sessions = ref([]);
  const currentSessionId = ref(null);
  const messages = ref([]);

  async function loadSessions() {
    const res = await apiClient.get("/chat/sessions");
    if (res.code === 0) {
      sessions.value = res.data;
      if (!currentSessionId.value && sessions.value.length > 0) {
        currentSessionId.value = sessions.value[0].id;
      }
    }
  }

  async function createSession(name) {
    const res = await apiClient.post("/chat/sessions", { name });
    if (res.code === 0) {
      sessions.value.unshift(res.data);
      currentSessionId.value = res.data.id;
      messages.value = [];
    }
  }

  async function deleteSession(id) {
    await apiClient.delete(`/chat/sessions/${id}`);
    sessions.value = sessions.value.filter((s) => s.id !== id);
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value[0]?.id || null;
      messages.value = [];
    }
  }

  async function sendQuestion(payload, onToken) {
    if (!currentSessionId.value) {
      await createSession("新的对话");
    }
    const streamPayload = {
      ...payload,
      session_id: currentSessionId.value
    };
    await apiStream("/chat/stream", streamPayload, onToken);
  }

  return {
    sessions,
    currentSessionId,
    messages,
    loadSessions,
    createSession,
    deleteSession,
    sendQuestion
  };
});

