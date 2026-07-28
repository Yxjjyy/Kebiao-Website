<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  router.replace('/')
})
</script>

<template>
  <main class="flex min-h-screen items-center justify-center px-4 py-8">
    <p class="text-sm text-[var(--text-dim)]">正在跳转...</p>
  </main>
</template>
