<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ProfileSetup from '@/components/ProfileSetup.vue'

const router = useRouter()
const ready = ref(false)
const initialAnswers = ref({})
const profileId = ref(localStorage.getItem('profileId'))

onMounted(async () => {
  if (profileId.value) {
    try {
      const res = await fetch(`http://localhost:8000/api/profiles/${profileId.value}/`)
      if (res.ok) {
        const profile = await res.json()
        initialAnswers.value = {
          language: profile.language,
          status: profile.status,
          hasChildren: profile.has_children,
        }
      } else {
        localStorage.removeItem('profileId')
        profileId.value = null
      }
    } catch {
      localStorage.removeItem('profileId')
      profileId.value = null
    }
  }
  ready.value = true
})

async function handleComplete(answers) {
  try {
    const isUpdate = !!profileId.value
    const res = await fetch(
      isUpdate
        ? `http://localhost:8000/api/profiles/${profileId.value}/`
        : 'http://localhost:8000/api/profiles/',
      {
        method: isUpdate ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: answers.language,
          status: answers.status,
          has_children: answers.hasChildren,
        }),
      }
    )
    if (res.ok) {
      const data = await res.json()
      localStorage.setItem('profileId', data.id)
    }
  } catch (error) {
    console.error('Failed to save profile:', error)
  }
  router.push('/categories')
}
</script>

<template>
  <ProfileSetup v-if="ready" :initial-answers="initialAnswers" @complete="handleComplete" />
</template>
