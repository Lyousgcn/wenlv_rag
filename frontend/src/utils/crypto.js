import CryptoJS from "crypto-js";

export function sha256(text) {
  return CryptoJS.SHA256(text).toString();
}

