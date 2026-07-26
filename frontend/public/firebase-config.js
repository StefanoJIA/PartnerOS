// Local PartnerOS customer-site compatibility placeholder.
// Real customer authentication will be wired through PartnerOS later. Do not
// place Firebase secrets or raw tokens in this public frontend file.
window.FIREBASE_API_KEY = window.FIREBASE_API_KEY || "local-placeholder";
window.FIREBASE_AUTH_DOMAIN = window.FIREBASE_AUTH_DOMAIN || "local-placeholder";
window.FIREBASE_PROJECT_ID = window.FIREBASE_PROJECT_ID || "local-placeholder";
window.FIREBASE_STORAGE_BUCKET = window.FIREBASE_STORAGE_BUCKET || "local-placeholder";
window.FIREBASE_MESSAGING_SENDER_ID = window.FIREBASE_MESSAGING_SENDER_ID || "local-placeholder";
window.FIREBASE_APP_ID = window.FIREBASE_APP_ID || "local-placeholder";
window.FIREBASE_MEASUREMENT_ID = window.FIREBASE_MEASUREMENT_ID || "local-placeholder";

const firebaseConfig = {
  apiKey: window.FIREBASE_API_KEY,
  authDomain: window.FIREBASE_AUTH_DOMAIN,
  projectId: window.FIREBASE_PROJECT_ID,
  storageBucket: window.FIREBASE_STORAGE_BUCKET,
  messagingSenderId: window.FIREBASE_MESSAGING_SENDER_ID,
  appId: window.FIREBASE_APP_ID,
  measurementId: window.FIREBASE_MEASUREMENT_ID,
};

const isFirebaseConfigured = () => false;

if (typeof module !== "undefined" && module.exports) {
  module.exports = { firebaseConfig, isFirebaseConfigured };
}
