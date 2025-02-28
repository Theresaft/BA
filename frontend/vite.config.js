import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { viteCommonjs } from '@originjs/vite-plugin-commonjs';


export default defineConfig({
	plugins: [
		sveltekit(),
		viteCommonjs(), // Support for CommonJS modules like dicom-parser
	  ],
	// Dependency pre-bundling. 
	optimizeDeps: {
		include: ['@cornerstonejs/core', '@kitware/vtk.js', "dicom-parser", "@cornerstonejs/tools", "@cornerstonejs/adapters", "dcmjs"],
		exclude: ["@cornerstonejs/dicom-image-loader", "@cornerstonejs/nifti-volume-loader"], //Important: Exclude dicom-image-loader
	},
	/**
	 * Specifies which dependencies should not be treated as "external" when the app is built for SSR. 
	 * This is needed when a library is required to be bundled into the server build rather than being left as-is.
	 */
	ssr: {
		noExternal: [
			'@cornerstonejs/core',
			'@kitware/vtk.js',
			'@cornerstonejs/dicom-image-loader', 
			"@cornerstonejs/tools", 
			"@cornerstonejs/nifti-volume-loader",
			"@cornerstonejs/adapters",
			"dcmjs"
		],
	},
	worker: {
		// Configure workers to use ES module format
		format: 'es',
		rollupOptions: {
		  external: [
			// Externalize specific codecs or WASM modules if needed
			'@icr/polyseg-wasm',
		  ],
		},
	  },
});
