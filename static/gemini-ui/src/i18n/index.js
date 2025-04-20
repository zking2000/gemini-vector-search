import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslation from './locales/en';
import zhTranslation from './locales/zh';

// 配置i18next
i18n
  .use(LanguageDetector) // 自动检测用户浏览器语言
  .use(initReactI18next) // 初始化react-i18next
  .init({
    resources: {
      en: {
        translation: enTranslation
      },
      zh: {
        translation: zhTranslation
      }
    },
    fallbackLng: 'zh', // 默认语言为中文
    interpolation: {
      escapeValue: false // 不转义特殊字符
    },
    detection: {
      order: ['localStorage', 'navigator'], // 先检查localStorage，再检查浏览器设置
      caches: ['localStorage'], // 将语言选择保存在localStorage中
    }
  });

export default i18n; 