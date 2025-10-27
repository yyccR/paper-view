import { createI18n } from 'vue-i18n'
import zh from './locales/zh'
import en from './locales/en'

// 获取浏览器语言
const getBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage
  if (browserLang.startsWith('zh')) return 'zh'
  if (browserLang.startsWith('en')) return 'en'
  return 'zh' // 默认中文
}

// 获取存储的语言偏好
const getStoredLanguage = () => {
  return localStorage.getItem('paper-view-language')
}

// 确定初始语言
const getInitialLanguage = () => {
  return getStoredLanguage() || getBrowserLanguage()
}

const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: getInitialLanguage(),
  fallbackLocale: 'zh',
  messages: {
    zh,
    en
  },
  globalInjection: true // 全局注入 $t
})

// 导出切换语言的方法
export const setLanguage = (lang) => {
  i18n.global.locale.value = lang
  localStorage.setItem('paper-view-language', lang)
  document.documentElement.lang = lang
}

export default i18n
