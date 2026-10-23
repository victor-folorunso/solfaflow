/// <reference types="vitest/config" />
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// The Python server (server.py) owns uploads, progress and results; in dev, Vite forwards to it.
const API = 'http://127.0.0.1:8765';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// Public pages are prerendered to plain HTML (for search engines); the song pages are
			// private, client-rendered, and served through the 200.html fallback.
			adapter: adapter({ fallback: '200.html' })
		})
	],
	server: {
		proxy: {
			'/api': API,
			'/results': API
		}
	},
	test: {
		include: ['src/**/*.test.ts']
	}
});
