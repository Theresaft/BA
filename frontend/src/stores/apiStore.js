/** The idea was stolen from heydan3891: 
 * 	https://www.reddit.com/r/sveltejs/comments/s8rsx9/where_to_put_api_calls_stores/
 *  https://svelte.dev/repl/25bb69c7a5264d1ea3de634c2658ee3b?version=3.46.2
 */

import { writable } from 'svelte/store';

import { getNiftiById, uploadFiles } from './api';

const { subscribe, set, update } = writable({
	blob: '',
	uploadedFiles: ''
});

export const apiStore = {
    subscribe,
    getNiftiById: async (id) => {
		// Validate data 
		if (id == '') return new Error('Id must be provided');
		
		const blob = await getNiftiById(id);
		update(apiData => {
			apiData.blob = blob
			return apiData
		} );
	},
	uploadFiles: async (data) => {
		if (data == '') return new Error('Data must be provided');
		const uploadedFiles = await uploadFiles(data);
		update(apiData =>{
			apiData.uploadedFiles = uploadedFiles
			return apiData
		} );
	}
}

