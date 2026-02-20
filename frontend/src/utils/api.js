import axios from "axios";
import { useAuthStore } from "../stores/auth";

const baseURL = import.meta.env.VITE_API_BASE || "/api";

const instance = axios.create({
  baseURL,
  timeout: 20000
});

instance.interceptors.request.use(
  (config) => {
    const auth = useAuthStore();
    if (auth.token) {
      config.headers.Authorization = `Bearer ${auth.token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let message = "请求失败，请稍后重试";
    if (error.response?.data?.message) {
      message = error.response.data.message;
    }
    return Promise.reject(new Error(message));
  }
);

export const apiClient = {
  get(url, params) {
    return instance.get(url, { params });
  },
  post(url, data) {
    return instance.post(url, data);
  },
  delete(url) {
    return instance.delete(url);
  },
  put(url, data) {
    return instance.put(url, data);
  }
};

export async function apiStream(url, data, onToken) {
  const fullUrl = `${baseURL}${url}`;
  const auth = useAuthStore();
  const headers = { "Content-Type": "application/json" };
  if (auth.token) {
    headers.Authorization = `Bearer ${auth.token}`;
  }
  const response = await fetch(fullUrl, {
    method: "POST",
    headers,
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`服务异常：${response.status}`);
  }

  // 非流式或环境不支持 ReadableStream 时，整体读取一次
  if (!response.body || !response.body.getReader) {
    const text = await response.text();
    if (onToken && text) {
      onToken(text);
    }
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let hasToken = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split(/\n\n/);
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const content = line.replace(/^data:\s*/, "");
      if (content === "[DONE]") {
        return;
      }
      hasToken = true;
      if (onToken) {
        onToken(content);
      }
    }
  }

  // 如果没有收到任何 token，但响应有文本内容，作为兜底展示
  if (!hasToken && buffer && onToken) {
    onToken(buffer);
  }
}
