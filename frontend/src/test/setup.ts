import '@testing-library/jest-dom'
import { vi } from 'vitest'
import React from 'react'

// 🎨 Mock Framer Motion for tests
const sanitizeMotionProps = (props: Record<string, unknown>) => {
  const {
    initial,
    animate,
    exit,
    whileHover,
    whileTap,
    transition,
    variants,
    layout,
    ...rest
  } = props

  return {
    ...rest,
    ...(initial ? { initial: '[object Object]' } : {}),
    ...(animate ? { animate: '[object Object]' } : {}),
    ...(exit ? { exit: '[object Object]' } : {}),
    ...(whileHover ? { whilehover: '[object Object]' } : {}),
    ...(whileTap ? { whiletap: '[object Object]' } : {}),
    ...(transition ? { transition: '[object Object]' } : {}),
    ...(variants ? { variants: '[object Object]' } : {}),
    ...(layout ? { layout: String(layout) } : {}),
  }
}

const createMotionComponent = (tag: string) =>
  ({ children, ...props }: any) => React.createElement(tag, sanitizeMotionProps(props), children)

vi.mock('framer-motion', () => ({
  motion: {
    div: createMotionComponent('div'),
    button: createMotionComponent('button'),
    svg: createMotionComponent('svg'),
    path: createMotionComponent('path'),
    span: createMotionComponent('span'),
    nav: createMotionComponent('nav'),
    aside: createMotionComponent('aside'),
    form: createMotionComponent('form'),
    input: createMotionComponent('input'),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
}))

// 🌐 Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      changeLanguage: () => new Promise(() => {}),
    },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: () => {},
  },
}))

// 🚀 Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({
      pathname: '/',
    }),
  }
})

// 🎨 Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
}))

// 🎨 Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
}))

// 🎨 Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
