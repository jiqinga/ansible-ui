import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import os from 'os'

// 🔍 获取本机IP地址
function getLocalIP(): string {
  const interfaces = os.networkInterfaces()
  for (const name of Object.keys(interfaces)) {
    const iface = interfaces[name]
    if (!iface) continue
    
    for (const alias of iface) {
      if (alias.family === 'IPv4' && !alias.internal) {
        return alias.address
      }
    }
  }
  return 'localhost'
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = env.VITE_BACKEND_PORT || '8000'
  const localIP = getLocalIP()
  
  // 🎯 使用 localhost 构建后端地址（用于开发环境）
  const backendTarget = `http://127.0.0.1:${backendPort}`
  
  console.log(`🌐 前端服务: http://${localIP}:3000`)
  console.log(`🔗 后端代理: ${backendTarget}`)
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@/components': path.resolve(__dirname, './src/components'),
        '@/pages': path.resolve(__dirname, './src/pages'),
        '@/hooks': path.resolve(__dirname, './src/hooks'),
        '@/utils': path.resolve(__dirname, './src/utils'),
        '@/types': path.resolve(__dirname, './src/types'),
        '@/styles': path.resolve(__dirname, './src/styles'),
        '@/i18n': path.resolve(__dirname, './src/i18n'),
      },
    },
    server: {
      host: '0.0.0.0', // 监听所有网络接口
      port: 3000,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        },
      },
    },
    build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          i18n: ['react-i18next', 'i18next'],
          animation: ['framer-motion'],
        },
      },
    },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
    },
  }
})