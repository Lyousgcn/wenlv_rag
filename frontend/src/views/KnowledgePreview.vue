<template>
  <div class="page">
    <h2>知识库预览</h2>
    <div class="toolbar">
      <input
        v-model="keyword"
        class="input"
        placeholder="输入关键词搜索文档块"
      />
      <button class="btn-primary" @click="load">搜索</button>
    </div>
    <div class="card">
      <div class="chunk" v-for="c in chunks" :key="c.id">
        <div class="chunk-header">
          <span>#{{ c.chunk_index }}</span>
          <span class="link small" @click="remove(c.id)">删除</span>
        </div>
        <textarea v-model="c.content" @blur="update(c)" />
      </div>
      <div v-if="chunks.length === 0" class="empty">暂无文档块</div>
      <div class="pager">
        <button :disabled="page <= 1" @click="page--; load()">上一页</button>
        <span>第 {{ page }} 页</span>
        <button :disabled="page * pageSize >= total" @click="page++; load()">
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { apiClient } from "../utils/api";

const route = useRoute();
const docId = Number(route.params.docId);

const keyword = ref("");
const chunks = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);

async function load() {
  const res = await apiClient.get(`/knowledge/documents/${docId}/chunks`, {
    page: page.value,
    page_size: pageSize.value,
    keyword: keyword.value
  });
  if (res.code === 0) {
    total.value = res.data.total;
    chunks.value = res.data.items;
  }
}

async function update(c) {
  await apiClient.put(`/knowledge/chunks/${c.id}`, { content: c.content });
}

async function remove(id) {
  await apiClient.delete(`/knowledge/chunks/${id}`);
  await load();
}

onMounted(load);
</script>

<style scoped>
.page {
  padding: 10px 4px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.card {
  max-height: 560px;
  overflow-y: auto;
}

.chunk {
  padding: 10px 0;
  border-bottom: 1px solid #eef0ff;
}

.chunk textarea {
  width: 100%;
  min-height: 80px;
  border-radius: 12px;
  border: 1px solid #dde3ff;
  padding: 8px 10px;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
  color: #7b8ba8;
}

.small {
  font-size: 12px;
}

.empty {
  text-align: center;
  margin: 24px 0;
  color: #7b8ba8;
}

.pager {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  font-size: 13px;
}

.pager button {
  padding: 6px 10px;
  border-radius: 999px;
  border: none;
  background: #eef3ff;
  cursor: pointer;
}
</style>

