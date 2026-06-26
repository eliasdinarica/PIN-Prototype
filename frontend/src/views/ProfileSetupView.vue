<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProfileSetup from '@/components/ProfileSetup.vue'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const router = useRouter()
const { locale } = useI18n()
const ready = ref(false)
const initialAnswers = ref({})
const profileId = ref(localStorage.getItem('profileId'))

onMounted(async () => {
  const profileRes = profileId.value
    ? await fetch(`${API}/api/profiles/${profileId.value}/`)
    : null

  if (profileRes) {
    if (profileRes.ok) {
      const profile = await profileRes.json()
      initialAnswers.value = {
        language: profile.language,
        frenchLevel: profile.french_level || 'none',
        status: profile.status,
        hasChildren: profile.has_children,
        arrivedOverYear: profile.arrived_over_year_ago,
        birthDate: profile.birth_date || '',
        hasDrivingLicense: profile.has_driving_license ?? null,
        computerSkills: profile.computer_skills || 'none',
        educationLevel: profile.education_level || '',
        originSector: profile.origin_sector || '',
      }
      if (profile.language) {
        locale.value = profile.language
        localStorage.setItem('profileLanguage', profile.language)
      }
    } else {
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
      language: answers.language || 'en',
      french_level: answers.frenchLevel || 'none',
      status: answers.status || 'other',
      has_children: answers.hasChildren ?? null,
      arrived_over_year_ago: answers.arrivedOverYear ?? null,
      birth_date: answers.birthDate || null,
      has_driving_license: answers.hasDrivingLicense ?? null,
      computer_skills: answers.computerSkills || 'none',
      education_level: answers.educationLevel || '',
      origin_sector: answers.originSector || '',
    }
    const res = await fetch(
      isUpdate
        ? `${API}/api/profiles/${profileId.value}/`
        : `${API}/api/profiles/`,
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
  router.push('/hub')
}
</script>

<template>
  <ProfileSetup
    v-if="ready"
    :initial-answers="initialAnswers"
    :is-editing="!!profileId"
    @complete="handleComplete"
    @finish="handleComplete"
  />
</template>
