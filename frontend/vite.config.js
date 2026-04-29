import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        host: true,
        allowedHosts: true,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure:false,
            }
        },
        headers: {
            'Content-Security-Policy': "script-src 'self' 'unsafe-eval' 'unsafe-inline';"
        }
    }
});