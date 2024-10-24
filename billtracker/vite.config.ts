import path from 'path';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { VitePWA } from 'vite-plugin-pwa';
import proxyOptions from './proxyOptions';

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [vue(),
		VitePWA({
			registerType: "autoUpdate",
			strategies: "injectManifest",
			injectRegister: null,
			devOptions: {
				enabled: true,
			},
			manifest: {
				display: "standalone",
				name: "Bill Tracker",
				short_name: "Bill Tracker",
				start_url: "/billtracker",
				description: "Everyday HR & Payroll operations at your fingertips",
				theme_color: "#ffffff",
				icons: [
					{
						src: "/assets/agarwals/billtracker/vite.svg",
						sizes: "192x192",
						type: "image/png",
						purpose: "any",
					},
					{
						src: "/assets/agarwals/billtracker/vite.svg",
						sizes: "192x192",
						type: "image/png",
						purpose: "maskable",
					},
					{
						src: "/assets/agarwals/billtracker/vite.svg",
						sizes: "512x512",
						type: "image/png",
						purpose: "any",
					},
					{
						src: "/assets/agarwals/billtracker/vite.svg",
						sizes: "512x512",
						type: "image/png",
						purpose: "maskable",
					},
				],
			},
		}),
	],
	server: {
		port: 8080,
		proxy: proxyOptions
	},
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src')
		}
	},
	build: {
		outDir: '../agarwals/public/billtracker',
		emptyOutDir: true,
		target: 'es2015',
	},
	optimizeDeps: { include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client'], },
});
