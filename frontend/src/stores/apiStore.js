/** The idea was stolen from heydan3891: 
 * 	https://www.reddit.com/r/sveltejs/comments/s8rsx9/where_to_put_api_calls_stores/
 *  https://svelte.dev/repl/25bb69c7a5264d1ea3de634c2658ee3b?version=3.46.2
 */

import { writable } from 'svelte/store';

import { getNiftiById, uploadDicomHeaders, createProject, uploadSequenceTypes, startSegmentation} from '../lib/api';

const { subscribe, set, update } = writable({
	blob: '',
	classifications: '',
	projectCreationResponse: '',
	sequenceTypeUploadResponse: '',
	segmentationStarted: ''
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
	uploadDicomHeaders: async (data) => {
		if (data == '') return new Error('Data must be provided');
		const classifications = await uploadDicomHeaders(data);
		update(apiData =>{
			apiData.classifications = classifications
			return apiData
		} );
	},
	createProject: async (data) => {
		if (data == '') return new Error('Data must be provided');
		const projectCreationResponse = await createProject(data);
		update(apiData =>{
			apiData.projectCreationResponse = projectCreationResponse
			return apiData
		} );
	},
	uploadSequenceTypes: async (data) => {
		if (data == '') return new Error('Data must be provided');
		const sequenceTypeUploadResponse = await uploadSequenceTypes(data);
		update(apiData =>{
			apiData.sequenceTypeUploadResponse = sequenceTypeUploadResponse
			return apiData
		} );
	},
	startSegmentation: async (data) => {
		if (data == '') return new Error('Data must be provided');
		const segmentationStarted = await startSegmentation(data);
		update(apiData =>{
			apiData.segmentationStarted = segmentationStarted
			return apiData
		} );
	}
}
