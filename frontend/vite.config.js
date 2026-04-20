import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        headers: {
            'Content-Security-Policy': "script-src 'self' 'unsafe-eval' 'unsafe-inline';"
        }
    }
});