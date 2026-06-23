import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import fr from './locales/fr.json'
import de from './locales/de.json'
import it from './locales/it.json'
import es from './locales/es.json'
import pt from './locales/pt.json'
import ru from './locales/ru.json'
import uk from './locales/uk.json'

const savedLanguage = localStorage.getItem('profileLanguage') || 'en'

export default createI18n({
  legacy: false,
  locale: savedLanguage,
  fallbackLocale: 'en',
  messages: { en, fr, de, it, es, pt, ru, uk },
})
