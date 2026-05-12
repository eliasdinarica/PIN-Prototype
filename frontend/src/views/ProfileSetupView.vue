<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProfileSetup from '@/components/ProfileSetup.vue'

const router = useRouter()
const { locale } = useI18n()
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
          otherLanguages: profile.other_languages ? profile.other_languages.split(',').filter(Boolean) : [],
          status: profile.status,
          hasChildren: profile.has_children,
          originSector: profile.origin_sector || '',
          arrivedOverYear: profile.arrived_over_year_ago,
          birthDate: profile.birth_date || '',
        }
        if (profile.language) {
          locale.value = profile.language
          localStorage.setItem('profileLanguage', profile.language)
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
    const body = {
      language: answers.language,
      other_languages: (answers.otherLanguages || []).join(','),
      status: answers.status,
      has_children: answers.hasChildren,
      origin_sector: answers.originSector || '',
      arrived_over_year_ago: answers.arrivedOverYear ?? null,
      birth_date: answers.birthDate || null,
    }
    const res = await fetch(
      isUpdate
        ? `http://localhost:8000/api/profiles/${profileId.value}/`
        : 'http://localhost:8000/api/profiles/',
      {
        method: isUpdate ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    )
    if (res.ok) {
      const data = await res.json()
      localStorage.setItem('profileId', data.id)
      if (answers.language) {
        localStorage.setItem('profileLanguage', answers.language)
        locale.value = answers.language
      }
    }
  } catch (error) {
    console.error('Failed to save profile:', error)
  }
  router.push('/categories')
}
</script>

<template>
  <ProfileSetup v-if="ready" :initial-answers="initialAnswers" :is-editing="!!profileId" @complete="handleComplete" @finish="handleComplete" />
</template>
