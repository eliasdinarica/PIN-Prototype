<script setup>
import ProfileSetup from './components/ProfileSetup.vue'

async function handleComplete(answers) {
  try {
    await fetch('http://localhost:8000/api/profiles/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: answers.language,
        has_children: answers.hasChildren,
      }),
    })
  } catch (error) {
    console.error('Failed to create profile:', error)
  }
}
</script>

<template>
  <ProfileSetup @complete="handleComplete" />
</template>
