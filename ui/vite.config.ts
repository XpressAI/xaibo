import { paraglide } from '@inlang/paraglide-sveltekit/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import houdini from 'houdini/vite'
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		houdini(),
		sveltekit(),
		paraglide({
			project: './project.inlang',
			outdir: './src/lib/paraglide'
		})
	],
	optimizeDeps: {
		exclude: ['@lucide/svelte'],
		include: ['@storybook/docs']
	},
	server: {
		proxy: {
			'^/api/.*': {
				target: 'http://localhost:9001',
			}
		}
	}
});
