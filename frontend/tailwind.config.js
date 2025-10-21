/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 🎨 玻璃态设计配色方案
      colors: {
        glass: {
          primary: 'rgba(255, 255, 255, 0.6)',
          secondary: 'rgba(255, 255, 255, 0.45)',
          hover: 'rgba(255, 255, 255, 0.75)',
          border: 'rgba(255, 255, 255, 0.35)',
          text: {
            primary: '#1f2937',
            secondary: '#475569',
            white: '#ffffff',
            accent: '#4f46e5',
          }
        },
        gradient: {
          primary: {
            from: '#667eea',
            to: '#764ba2',
          },
          secondary: {
            from: '#f093fb',
            to: '#f5576c',
          },
          tertiary: {
            from: '#4facfe',
            to: '#00f2fe',
          }
        }
      },
      // 🎨 玻璃态圆角设计
      borderRadius: {
        'glass': '15px',
        'glass-sm': '8px',
        'glass-lg': '24px',
      },
      // 🎨 玻璃态阴影效果
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glass-hover': '0 15px 35px 0 rgba(31, 38, 135, 0.4)',
        'glass-subtle': '0 4px 16px 0 rgba(31, 38, 135, 0.2)',
        'glass-strong': '0 20px 40px 0 rgba(31, 38, 135, 0.4)',
      },
      // 🎨 玻璃态模糊效果
      backdropBlur: {
        'glass': '10px',
        'glass-strong': '20px',
        'glass-light': '5px',
      },
      // 🎨 动画时间曲线
      transitionTimingFunction: {
        'glass': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'glass-bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      // 🎨 动画持续时间
      transitionDuration: {
        'glass': '300ms',
        'glass-fast': '150ms',
        'glass-slow': '400ms',
      },
      // 📱 响应式断点
      screens: {
        'xs': '475px',
        'glass-mobile': {'max': '768px'},
        'glass-tablet': {'min': '768px', 'max': '1024px'},
        'glass-desktop': {'min': '1024px'},
      },
      // 🎨 字体配置
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
          '"Apple Color Emoji"',
          '"Segoe UI Emoji"',
          '"Segoe UI Symbol"',
        ],
      },
    },
  },
  plugins: [
    // 🎨 自定义玻璃态工具类
    function({ addUtilities, theme }) {
      const newUtilities = {
        '.glass-container': {
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(14px)',
          borderRadius: '15px',
          border: '1px solid rgba(255, 255, 255, 0.35)',
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        '.glass-container:hover': {
          transform: 'translateY(-5px)',
          boxShadow: '0 20px 40px 0 rgba(31, 38, 135, 0.4)',
          background: 'rgba(255, 255, 255, 0.72)',
        },
        '.glass-button': {
          background: 'rgba(255, 255, 255, 0.45)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.4)',
          borderRadius: '15px',
          padding: '12px 24px',
          color: '#1f2937',
          fontWeight: '500',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
        },
        '.glass-button:hover': {
          background: 'rgba(255, 255, 255, 0.6)',
          transform: 'translateY(-2px)',
        },
        '.glass-button:active': {
          transform: 'scale(0.98)',
        },
        '.glass-input': {
          background: 'rgba(255, 255, 255, 0.55)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.4)',
          borderRadius: '8px',
          padding: '12px 16px',
          color: '#1f2937',
          fontSize: '14px',
          transition: 'all 0.3s ease',
        },
        '.glass-input:focus': {
          borderColor: 'rgba(102, 126, 234, 0.6)',
          boxShadow: '0 0 0 3px rgba(102, 126, 234, 0.15)',
          outline: 'none',
        },
        '.glass-input::placeholder': {
          color: 'rgba(71, 85, 105, 0.65)',
        },
        '.glass-nav': {
          background: 'rgba(255, 255, 255, 0.45)',
          backdropFilter: 'blur(22px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.32)',
        },
        '.gradient-bg-primary': {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        },
        '.gradient-bg-secondary': {
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        },
        '.gradient-bg-tertiary': {
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        },
        // 📱 移动端优化
        '@media (max-width: 768px)': {
          '.glass-container': {
            padding: '16px',
            borderRadius: '12px',
            backdropFilter: 'blur(5px)',
          },
          '.glass-button:hover': {
            transform: 'none',
          },
        },
      }
      addUtilities(newUtilities)
    },
  ],
}