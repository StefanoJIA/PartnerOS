<template>
  <svg
    class="io-mark"
    viewBox="0 0 64 64"
    role="img"
    aria-label="IntelliOpus"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <linearGradient id="io-blue-field" x1="10" x2="54" y1="8" y2="58" gradientUnits="userSpaceOnUse">
        <stop stop-color="#1D4ED8" />
        <stop offset="0.58" stop-color="#0F62FE" />
        <stop offset="1" stop-color="#0B2F6B" />
      </linearGradient>
      <linearGradient id="io-signal" x1="14" x2="51" y1="46" y2="16" gradientUnits="userSpaceOnUse">
        <stop stop-color="#DBEAFE" />
        <stop offset="0.48" stop-color="#7DD3FC" />
        <stop offset="1" stop-color="#FFFFFF" />
      </linearGradient>
    </defs>
    <rect width="64" height="64" rx="16" fill="url(#io-blue-field)" />
    <path
      d="M13 42C22 31 31 25 48 20"
      fill="none"
      stroke="url(#io-signal)"
      stroke-width="4.5"
      stroke-linecap="round"
    />
    <path
      d="M15 49C27 40 39 37 52 37"
      fill="none"
      stroke="#93C5FD"
      stroke-width="3.4"
      stroke-linecap="round"
      opacity="0.9"
    />
    <circle cx="14" cy="42" r="4.2" fill="#EFF6FF" />
    <circle cx="32" cy="28" r="4.2" fill="#BFDBFE" />
    <circle cx="50" cy="20" r="4.2" fill="#FFFFFF" />
    <path d="M31.5 15V49" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" />
    <path d="M22 16H41" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" />
    <path d="M42 31C47 31 51 35 51 40C51 45 47 49 42 49C37 49 33 45 33 40" fill="none" stroke="#DBEAFE" stroke-width="4" stroke-linecap="round" />
  </svg>
</template>

<style scoped>
.io-mark {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
