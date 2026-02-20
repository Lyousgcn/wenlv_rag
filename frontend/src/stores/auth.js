import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { apiClient } from "../utils/api";
import { sha256 } from "../utils/crypto";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token") || "");
  const username = ref(localStorage.getItem("username") || "");

  const isLoggedIn = computed(() => !!token.value);

  function setAuth(t, u) {
    token.value = t;
    username.value = u;
    localStorage.setItem("token", t);
    localStorage.setItem("username", u);
  }

  function clearAuth() {
    token.value = "";
    username.value = "";
    localStorage.removeItem("token");
    localStorage.removeItem("username");
  }

  async function fetchCaptcha() {
    const res = await apiClient.get("/auth/captcha");
    if (res.code !== 0) {
      throw new Error(res.message || "获取验证码失败");
    }
    return res.data;
  }

  async function login(form) {
    const encryptedPassword = sha256(form.password);
    const res = await apiClient.post("/auth/login", {
      username: form.username,
      password: encryptedPassword,
      captcha_id: form.captchaId,
      captcha_code: form.captchaCode
    });
    if (res.code !== 0) {
      throw new Error(res.message || "登录失败");
    }
    setAuth(res.data.token, form.username);
  }

  async function register(form) {
    const encryptedPassword = sha256(form.password);
    const res = await apiClient.post("/auth/register", {
      username: form.username,
      password: encryptedPassword
    });
    if (res.code !== 0) {
      throw new Error(res.message || "注册失败");
    }
  }

  return {
    token,
    username,
    isLoggedIn,
    setAuth,
    clearAuth,
    fetchCaptcha,
    login,
    register
  };
});

