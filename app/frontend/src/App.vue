<script setup lang="ts">
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()

onMounted(async () => {
  settings.applyTheme()
  await settings.refresh()
})
</script>

<template>
  <RouterView />
</template>
