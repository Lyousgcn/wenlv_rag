<template>
  <div class="page">
    <h2>知识库管理</h2>
    <div class="card form-card">
      <div class="row">
        <label>新建知识库名称</label>
        <input v-model="name" class="input" placeholder="请输入知识库名称" />
      </div>
      <div class="row">
        <label>描述</label>
        <input
          v-model="description"
          class="input"
          placeholder="请输入简介，可选"
        />
      </div>
      <button class="btn-primary" @click="create">创建知识库</button>
    </div>
    <div class="card list-card">
      <h3>已创建知识库</h3>
      <div v-if="knowledge.bases.length === 0" class="empty">暂无知识库</div>
      <div
        v-for="b in knowledge.bases"
        :key="b.id"
        class="kb-item"
        @click="openDocs(b)"
      >
        <div class="info">
          <div class="name">{{ b.name }}</div>
          <div class="desc">{{ b.description || "暂无描述" }}</div>
        </div>
        <div class="actions">
          <span class="link" @click.stop="openDocs(b)">文档列表</span>
          <span class="link danger" @click.stop="remove(b.id)">删除</span>
        </div>
      </div>
      <div v-if="docs.length > 0" class="doc-list">
        <h3>文档列表 - {{ currentBaseName }}</h3>
        <div
          v-for="d in docs"
          :key="d.id"
          class="doc-item"
          @click="preview(d.id)"
        >
          <div>{{ d.filename }}</div>
          <div class="status">{{ d.status }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useKnowledgeStore } from "../stores/knowledge";

const router = useRouter();
const knowledge = useKnowledgeStore();

const name = ref("");
const description = ref("");
const docs = ref([]);
const currentBaseName = ref("");

async function create() {
  if (!name.value) return;
  await knowledge.createBase(name.value, description.value);
  name.value = "";
  description.value = "";
}

async function remove(id) {
  await knowledge.deleteBase(id);
}

async function openDocs(kb) {
  await knowledge.loadDocuments(kb.id);
  docs.value = knowledge.documents;
  currentBaseName.value = kb.name;
}

function preview(docId) {
  router.push({ name: "knowledge-preview", params: { docId } });
}

onMounted(async () => {
  await knowledge.loadBases();
});
</script>

<style scoped>
.page {
  padding: 10px 4px;
}

.form-card {
  max-width: 520px;
  margin-bottom: 16px;
}

.row {
  margin-bottom: 10px;
}

label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
}

.list-card h3 {
  margin-top: 0;
}

.kb-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eef0ff;
  cursor: pointer;
}

.kb-item:hover {
  background: #f7f8ff;
}

.info .name {
  font-weight: 600;
}

.info .desc {
  font-size: 13px;
  color: #7b8ba8;
}

.actions {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.danger {
  color: #ff4d4f;
}

.empty {
  font-size: 13px;
  color: #7b8ba8;
}

.doc-list {
  margin-top: 16px;
}

.doc-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eef0ff;
  cursor: pointer;
  font-size: 14px;
}

.status {
  font-size: 12px;
  color: #7b8ba8;
}
</style>

