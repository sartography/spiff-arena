import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enUS from './locales/en_us/translation.json';
import ptBR from './locales/pt_br/translation.json';
import es from './locales/es/translation.json';
import de from './locales/de/translation.json';
import fi from './locales/fi/translation.json';
import ptPT from './locales/pt_pt/translation.json';
import csCZ from './locales/cs_cz/translation.json';
import zhCN from './locales/zh_cn/translation.json';

// eslint-disable-next-line import/no-named-as-default-member
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      'en-US': { translation: enUS },
      'pt-BR': { translation: ptBR },
      es: { translation: es },
      de: { translation: de },
      fi: { translation: fi },
      'pt-PT': { translation: ptPT },
      'cs-CZ': { translation: csCZ },
      'zh-CN': { translation: zhCN },
    },
    fallbackLng: 'en-US',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
    },
  });

export default i18n;
