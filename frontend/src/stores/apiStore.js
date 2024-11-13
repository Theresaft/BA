/** The idea was stolen from heydan3891: 
 * 	https://www.reddit.com/r/sveltejs/comments/s8rsx9/where_to_put_api_calls_stores/
 *  https://svelte.dev/repl/25bb69c7a5264d1ea3de634c2658ee3b?version=3.46.2
 */

import { writable } from 'svelte/store';

import { getNiftiById, uploadDicomHeaders, createProject, uploadSequenceTypes, startSegmentation, getSegmentation} from '../lib/api';

const { subscribe, set, update } = writable({
	blob: '',
	classifications: '',
	sequenceTypeUploadResponse: '',
	segmentationStarted: '',
	imageData : null, // Currently holding the images loaded into the viewer TODO: Reorganize Store
	isNIFTI : true // If imageData are nifti or dicom files 
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
		return await createProject(data);
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
	},
	getSegmentation: async () => {
		const res = await getSegmentation();
		const imageData = res[0]
		const fileType = res[1]

		update(apiData => {
			apiData.imageData = imageData
			apiData.fileType = fileType
			return apiData
		} );
	}
}
