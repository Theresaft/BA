// HERE WE MAKE API CALLS AND FORMAT DATA  
import JSZip from 'jszip'

// The Base URL is dynamically set for production (environment variable is embedded in frontend container)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/brainns-api';


export async function uploadDicomHeadersAPI(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/classify`, {
        method: 'POST',
        body: data
    });

    if (response.ok) {
        result = await response.json();
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText);
    }
    
    return result
}


export async function uploadProjectDataAPI(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        body: data
    });

    if (response.ok) {
        result = await response.json();
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText);
    }

    return result
}


// TODO: Never used. Remove?
export async function uploadSequenceTypesAPI(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/sequence-types`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: data
    });

    if (response.ok) {
        result = await response.json();
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText);
    }

    return result
}


export async function startSegmentationAPI(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: data
    });

    if (response.ok) {
        result = await response.json();
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText);
    }

    return result
}

export async function getSegmentationAPI() {
    
    const response = await fetch(`${API_BASE_URL}/projects/1/segmentations/1`, {
        method: 'GET',
    });

    if (response.ok) {
        const imageData = await response.blob(); // Zip file with image data for t1,tkm,t2,flair and labels

        const images = {
            t1: null,
            t1km: null,
            t2: null,
            flair: null,
            labels: [],
            fileType : response.headers.get('X-File-Type') // "DICOM" or "NIFTI" 
        }

        // Intialize "images" based on file type (DICOMs need Array)
        images.t1 = images.fileType === "NIFTI" ? null : [];
        images.t1km = images.fileType === "NIFTI" ? null : [];
        images.t2 = images.fileType === "NIFTI" ? null : [];
        images.flair = images.fileType === "NIFTI" ? null : [];


        // Save image URLs in "images"
        const zip = await JSZip.loadAsync(imageData);
        const promises = [];

        zip.forEach((relativePath, file) => {
            const sequenceType = relativePath.split('/')[0];

            const promise = file.async('blob').then(imageFile => {
                const url = URL.createObjectURL(imageFile);
                
                if (['t1', 't1km', 't2', 'flair'].includes(sequenceType)) {
                    if (images.fileType === "NIFTI") {
                        images[sequenceType] = url;
                    } else {
                        images[sequenceType].push(url);
                    }
                } else {
                    images.labels = [...images.labels, url]
                }
            });

            promises.push(promise);
        });

        await Promise.all(promises);

        return images

    } else {
        console.error('Error fetching Segmentation images:', response.statusText);
        return 
    }

}