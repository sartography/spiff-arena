import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import I18nextBrowserLanguageDetector from 'i18next-browser-languagedetector';

import enUS from './locales/en_us/translation.json';
import ptBR from './locales/pt_br/translation.json';
import es from './locales/es/translation.json';
import de from './locales/de/translation.json';
import fi from './locales/fi/translation.json';
import ptPT from './locales/pt_pt/translation.json';
import csCZ from './locales/cs_cz/translation.json';
import zhCN from './locales/zh_cn/translation.json';
import frFR from './locales/fr_fr/translation.json';

// eslint-disable-next-line import-x/no-named-as-default-member
i18next
  .use(I18nextBrowserLanguageDetector)
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
      'fr-FR': { translation: frFR },
    },
    fallbackLng: 'en-US',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
    },
  });

/**
 * Keep the document's lang attribute in sync with the active locale.
 *
 * index.html ships a static lang="en", but the app switches among several
 * locales at runtime. Without this, assistive technology keeps announcing
 * translated content with an English speech synthesizer, which fails
 * WCAG 2.1 AA success criterion 3.1.1 (Language of Page) for every
 * non-English user.
 */
const syncDocumentLanguage = (language: string) => {
  if (language) {
    document.documentElement.lang = language;
  }
};

i18next.on('languageChanged', syncDocumentLanguage);
syncDocumentLanguage(i18next.language);

export default i18next;
