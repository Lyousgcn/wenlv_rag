<template>
  <div class="page">
    <h2>知识库解析与上传</h2>
    <p class="tip">支持 PDF、PPT、Markdown、Word、PNG 等格式的文件上传与解析</p>
    <div class="card form-card">
      <div class="row">
        <label>目标知识库</label>
        <select v-model="kbId" class="input">
          <option disabled value="">请选择知识库</option>
          <option v-for="b in knowledge.bases" :key="b.id" :value="b.id">
            {{ b.name }}
          </option>
        </select>
      </div>
      <div class="row">
        <label>文本切块大小</label>
        <input v-model.number="chunkSize" class="input" type="number" />
      </div>
      <div class="row">
        <label>重叠大小</label>
        <input v-model.number="chunkOverlap" class="input" type="number" />
      </div>
      <div class="row">
        <label>检索模式</label>
        <div class="radio-group">
          <label>
            <input v-model="useHybrid" type="radio" :value="false" />
            稠密向量检索
          </label>
          <label>
            <input v-model="useHybrid" type="radio" :value="true" />
            混合检索
          </label>
        </div>
      </div>
      <div class="row">
        <label>选择文件</label>
        <input type="file" @change="onFileChange" />
      </div>
      <button class="btn-primary" :disabled="uploading" @click="upload">
        {{ uploading ? "上传中..." : "开始上传解析" }}
      </button>
      <p v-if="status" class="status">{{ status }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useKnowledgeStore } from "../stores/knowledge";
import { apiClient } from "../utils/api";

const knowledge = useKnowledgeStore();

const kbId = ref("");
const chunkSize = ref(500);
const chunkOverlap = ref(100);
const useHybrid = ref(false);
const file = ref(null);
const uploading = ref(false);
const status = ref("");

function onFileChange(e) {
  file.value = e.target.files[0];
}

async function upload() {
  if (!kbId.value || !file.value) {
    status.value = "请选择知识库并选择文件";
    return;
  }
  uploading.value = true;
  status.value = "上传中...";
  try {
    const formData = new FormData();
    formData.append("file", file.value);
    formData.append("chunk_size", chunkSize.value);
    formData.append("chunk_overlap", chunkOverlap.value);
    formData.append("use_hybrid", useHybrid.value ? "1" : "0");
    const res = await apiClient.post(
      `/knowledge/bases/${kbId.value}/documents`,
      formData
    );
    if (res.code === 0) {
      status.value = "上传并解析成功";
    } else {
      status.value = res.message || "上传失败";
    }
  } catch (e) {
    status.value = e.message;
  } finally {
    uploading.value = false;
  }
}

onMounted(async () => {
  await knowledge.loadBases();
});
</script>

<style scoped>
.page {
  padding: 10px 4px;
}

h2 {
  margin: 0 0 4px;
}

.tip {
  margin: 0 0 16px;
  font-size: 13px;
  color: #7b8ba8;
}

.form-card {
  max-width: 640px;
}

.row {
  margin-bottom: 12px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
}

.radio-group {
  display: flex;
  gap: 16px;
  font-size: 14px;
}

.status {
  margin-top: 12px;
  font-size: 13px;
  color: #5b6c8f;
}
</style>

