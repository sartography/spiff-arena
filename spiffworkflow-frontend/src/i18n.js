import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en_us from './locales/en_us/translation.json';
import pt_br from './locales/pt_br/translation.json';
import es from './locales/es/translation.json';
import de from './locales/de/translation.json';
import fi from './locales/fi/translation.json';
import pt_pt from './locales/pt_pt/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      'en-US': { translation: en_us },
      'pt-BR': { translation: pt_br },
      'es': { translation: es },
      'de': { translation: de },
      'fi': { translation: fi },
      'pt-PT': { translation: pt_pt },
    },
    fallbackLng: 'en-US',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['navigator'],
    },
  });

export default i18n;
