<template>
  <div class="auth-page">
    <div class="auth-panel card">
      <h1 class="title">文旅智能问答系统</h1>
      <p class="subtitle">面向文旅行业的多模态知识问答助手</p>
      <form class="form" @submit.prevent="onSubmit">
        <div class="form-item">
          <label>账号</label>
          <input v-model="form.username" class="input" placeholder="请输入账号" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input
            v-model="form.password"
            class="input"
            type="password"
            placeholder="请输入密码"
          />
        </div>
        <div class="form-item captcha-row">
          <div class="captcha-input">
            <label>验证码</label>
            <input
              v-model="form.captchaCode"
              class="input"
              placeholder="请输入验证码"
            />
          </div>
          <div class="captcha-image" @click="loadCaptcha">
            <img v-if="captchaImage" :src="captchaImage" alt="验证码" />
            <span v-else>点击获取验证码</span>
          </div>
        </div>
        <div class="form-item">
          <button class="btn-primary" type="submit" :disabled="loading">
            {{ loading ? "登录中..." : "登录" }}
          </button>
        </div>
        <div class="form-footer">
          还没有账号？
          <span class="link" @click="goRegister">立即注册</span>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const form = reactive({
  username: "",
  password: "",
  captchaId: "",
  captchaCode: ""
});

const captchaImage = ref("");
const loading = ref(false);
const error = ref("");

async function loadCaptcha() {
  try {
    const data = await auth.fetchCaptcha();
    form.captchaId = data.captcha_id;
    captchaImage.value = `data:image/png;base64,${data.image_base64}`;
  } catch (e) {
    error.value = e.message || "获取验证码失败";
  }
}

async function onSubmit() {
  error.value = "";
  if (!form.username || !form.password || !form.captchaCode) {
    error.value = "请填写完整信息";
    return;
  }
  loading.value = true;
  try {
    await auth.login(form);
    router.push({ name: "chat" });
  } catch (e) {
    error.value = e.message;
    await loadCaptcha();
  } finally {
    loading.value = false;
  }
}

function goRegister() {
  router.push({ name: "register" });
}

onMounted(() => {
  loadCaptcha();
});
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 16px;
}

.auth-panel {
  max-width: 420px;
  width: 100%;
}

.title {
  margin: 0;
  font-size: 26px;
}

.subtitle {
  margin: 6px 0 24px;
  color: #5b6c8f;
  font-size: 14px;
}

.form-item {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
}

.captcha-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.captcha-input {
  flex: 1;
}

.captcha-image {
  width: 120px;
  height: 40px;
  border-radius: 12px;
  background: #f3f6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  color: #0b66ff;
}

.captcha-image img {
  max-width: 100%;
  border-radius: 12px;
}

.form-footer {
  font-size: 13px;
  color: #5b6c8f;
}

.error {
  color: #ff4d4f;
  font-size: 13px;
}
</style>

