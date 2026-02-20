import { defineStore } from "pinia";
import { ref } from "vue";
import { apiClient } from "../utils/api";

export const useKnowledgeStore = defineStore("knowledge", () => {
  const bases = ref([]);
  const documents = ref([]);
  const currentBaseId = ref(null);

  async function loadBases() {
    const res = await apiClient.get("/knowledge/bases");
    if (res.code === 0) {
      bases.value = res.data;
    }
  }

  async function createBase(name, description) {
    const res = await apiClient.post("/knowledge/bases", {
      name,
      description
    });
    if (res.code === 0) {
      bases.value.push(res.data);
    }
  }

  async function deleteBase(id) {
    await apiClient.delete(`/knowledge/bases/${id}`);
    bases.value = bases.value.filter((b) => b.id !== id);
  }

  async function loadDocuments(kbId) {
    const res = await apiClient.get(`/knowledge/bases/${kbId}/documents`);
    if (res.code === 0) {
      documents.value = res.data;
      currentBaseId.value = kbId;
    }
  }

  return {
    bases,
    documents,
    currentBaseId,
    loadBases,
    createBase,
    deleteBase,
    loadDocuments
  };
});

