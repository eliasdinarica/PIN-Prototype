import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import fr from './locales/fr.json'
import ru from './locales/ru.json'
import uk from './locales/uk.json'

const savedLanguage = localStorage.getItem('profileLanguage') || 'en'

export default createI18n({
  legacy: false,
  locale: savedLanguage,
  fallbackLocale: 'en',
  messages: { en, fr, ru, uk },
})
