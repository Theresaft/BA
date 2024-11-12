// HERE WE MAKE API CALLS AND FORMAT DATA  

// The Base URL is dynamically set for production (environment variable is embedded in frontend container)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/brainns-api';

export async function getNiftiById (id){

    // Make api call
    const response = await fetch(`${API_BASE_URL}/nifti/${id}`, {
        method: 'GET',
    });

    // Format data
    const blob = await response.blob();		
    
    return blob;
}


export async function uploadDicomHeaders(data) {
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


export async function createProject(data) {
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


export async function uploadSequenceTypes(data) {
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


export async function startSegmentation(data) {
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

export async function getSegmentation() {
    let imageData // Zip file with image data for t1,tkm,t2,flair and labels
    let fileType // "DICOM" or "NIFTI" 
    const response = await fetch(`${API_BASE_URL}/projects/1/segmentations/1`, {
        method: 'GET',
    });

    if (response.ok) {
        imageData = await response.blob();
        fileType = response.headers.get('X-File-Type')
    } else {
        console.error('Error fetching Segmentation images:', response.statusText);
    }

    return [imageData, fileType]
}