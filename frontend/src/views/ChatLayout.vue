<template>
  <div class="layout">
    <aside class="sidebar card">
      <div class="logo">
        <span class="logo-dot" />
        <span class="logo-text">文旅智能问答</span>
      </div>
      <button class="btn-primary new-session" @click="createSession">
        新建会话
      </button>
      <div class="session-list">
        <div
          v-for="s in chat.sessions"
          :key="s.id"
          :class="['session-item', s.id === chat.currentSessionId ? 'active' : '']"
          @click="selectSession(s.id)"
        >
          <span class="name">{{ s.name }}</span>
          <span class="delete" @click.stop="deleteSession(s.id)">✕</span>
        </div>
      </div>
      <div class="nav">
        <div class="nav-title">知识库</div>
        <div class="nav-link" @click="goKnowledgeManage">知识库管理</div>
        <div class="nav-link" @click="goKnowledgeParse">解析上传</div>
      </div>
      <div class="user">
        <span class="username">{{ auth.username }}</span>
        <span class="link" @click="logout">退出</span>
      </div>
    </aside>
    <main class="main card">
      <section class="chat-area">
        <div class="chat-header">
          <div>
            <h2>对话中心</h2>
            <p>支持基于企业文旅知识库的精准问答</p>
          </div>
          <div class="model-config">
            <label>温度</label>
            <input
              v-model.number="params.temperature"
              class="input small"
              type="number"
              step="0.1"
              min="0"
              max="1"
            />
            <label>TopP</label>
            <input
              v-model.number="params.topP"
              class="input small"
              type="number"
              step="0.1"
              min="0"
              max="1"
            />
            <label>最长输出</label>
            <input
              v-model.number="params.maxTokens"
              class="input small"
              type="number"
            />
            <label>历史轮次</label>
            <input
              v-model.number="params.historyRounds"
              class="input small"
              type="number"
              min="0"
            />
          </div>
        </div>
        <div class="kb-selector">
          <span class="kb-label">选择参与检索的知识库：</span>
          <div class="kb-tags">
            <label
              v-for="b in knowledge.bases"
              :key="b.id"
              class="kb-tag"
            >
              <input
                v-model="selectedKbIds"
                type="checkbox"
                :value="b.id"
              />
              <span>{{ b.name }}</span>
            </label>
          </div>
        </div>
        <div class="chat-body">
          <div v-if="chatMessages.length === 0" class="empty">
            从左侧新建会话，或直接开始提问
          </div>
          <div
            v-for="(m, idx) in chatMessages"
            :key="idx"
            :class="['msg', m.role]"
          >
            <div class="avatar">
              {{ m.role === "user" ? "我" : "助" }}
            </div>
            <div class="bubble">
              {{ m.content }}
            </div>
          </div>
        </div>
        <div class="chat-input">
          <textarea
            v-model="question"
            placeholder="请输入你想咨询的文旅问题，比如“帮我规划一条苏州两日游路线”"
          />
          <button class="btn-primary" :disabled="sending" @click="send">
            {{ sending ? "生成中..." : "发送" }}
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useChatStore } from "../stores/chat";
import { useKnowledgeStore } from "../stores/knowledge";

const auth = useAuthStore();
const chat = useChatStore();
const knowledge = useKnowledgeStore();
const router = useRouter();

const params = reactive({
  temperature: 0.8,
  topP: 0.8,
  maxTokens: 1024,
  historyRounds: 5
});

const question = ref("");
const sending = ref(false);
const chatMessages = computed(() => chat.messages);
const selectedKbIds = ref([]);

async function createSession() {
  const name = `会话 ${chat.sessions.length + 1}`;
  await chat.createSession(name);
}

function selectSession(id) {
  chat.currentSessionId = id;
}

async function deleteSession(id) {
  await chat.deleteSession(id);
}

async function send() {
  if (!question.value.trim()) return;
  const userMsg = { role: "user", content: question.value };
  chat.messages.push(userMsg);
  const answerMsg = { role: "assistant", content: "" };
  chat.messages.push(answerMsg);
  const payload = {
    kb_ids: selectedKbIds.value,
    question: question.value,
    temperature: params.temperature,
    top_p: params.topP,
    max_tokens: params.maxTokens,
    history_rounds: params.historyRounds
  };
  question.value = "";
  sending.value = true;
  try {
    await chat.sendQuestion(payload, (token) => {
      answerMsg.content += token;
    });
  } catch (e) {
    answerMsg.content =
      e && e.message ? `对话服务异常：${e.message}` : "对话服务异常，请稍后重试";
  } finally {
    sending.value = false;
  }
}

function goKnowledgeManage() {
  router.push({ name: "knowledge-manage" });
}

function goKnowledgeParse() {
  router.push({ name: "knowledge-parse" });
}

function logout() {
  auth.clearAuth();
  router.push({ name: "login" });
}

onMounted(async () => {
  await chat.loadSessions();
  await knowledge.loadBases();
});
</script>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
  padding: 20px;
  min-height: 100vh;
  box-sizing: border-box;
}

.sidebar {
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.logo-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 20%, #ffffff, #0b66ff);
}

.logo-text {
  font-weight: 700;
}

.new-session {
  width: 100%;
  margin-bottom: 12px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
}

.session-item:hover {
  background: #f3f6ff;
}

.session-item.active {
  background: #0b66ff;
  color: #ffffff;
}

.session-item .delete {
  font-size: 12px;
  opacity: 0.7;
}

.nav {
  margin-bottom: 16px;
}

.nav-title {
  font-size: 13px;
  margin-bottom: 6px;
  color: #7b8ba8;
}

.nav-link {
  font-size: 14px;
  padding: 6px 0;
  cursor: pointer;
}

.nav-link:hover {
  color: #0b66ff;
}

.user {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #7b8ba8;
}

.main {
  display: flex;
}

.chat-area {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chat-header h2 {
  margin: 0;
}

.chat-header p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #687797;
}

.model-config {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.model-config .small {
  width: 64px;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f5f7ff;
  border-radius: 12px;
}

.kb-selector {
  margin-bottom: 8px;
  font-size: 13px;
  color: #5b6c8f;
}

.kb-label {
  margin-right: 8px;
}

.kb-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.kb-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef3ff;
  cursor: pointer;
}

.empty {
  text-align: center;
  margin-top: 40px;
  color: #7b8ba8;
  font-size: 14px;
}

.msg {
  display: flex;
  margin-bottom: 12px;
}

.msg.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #0b66ff;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  margin: 0 8px;
}

.msg.assistant .avatar {
  background: #00c2ff;
}

.bubble {
  max-width: 70%;
  background: #ffffff;
  border-radius: 14px;
  padding: 8px 12px;
  font-size: 14px;
}

.msg.user .bubble {
  background: #0b66ff;
  color: #ffffff;
}

.chat-input {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.chat-input textarea {
  flex: 1;
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid rgba(11, 102, 255, 0.2);
  resize: none;
  min-height: 80px;
}

@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    order: 2;
  }
}
</style>
