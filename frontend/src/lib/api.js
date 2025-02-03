// HERE WE MAKE API CALLS AND FORMAT DATA  
import JSZip from 'jszip'

// The Base URL is dynamically set for production (environment variable is embedded in frontend container)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/brainns-api';


/**
 * Delete the project with the given ID.
 * @param {The project ID of the project to delete} projectID 
 */
export async function deleteProjectAPI(projectID) {
    console.log("Auth headers:")
    console.log(getAuthHeaders())
    console.log(`${API_BASE_URL}/projects/${projectID}`)

    return await fetch(`${API_BASE_URL}/projects/${projectID}`, {
        method: 'DELETE',
        headers: {
            ...getAuthHeaders(),
        },
    })
}


/**
 * Delete the segmentation with the given ID.
 * @param {The segmentation ID of the segmentation to delete} segmentationID 
 */
export async function deleteSegmentationAPI(segmentationID) {
    return await fetch(`${API_BASE_URL}/segmentations/${segmentationID}`, {
        method: 'DELETE',
        headers: {
            ...getAuthHeaders(),
        },
    })
}


export async function getAllProjectsAPI() {
    const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'GET',
        headers: {
            ...getAuthHeaders()
        },
    })

    if (response.ok) {
        return await response.json()
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText)
    }
}


export async function uploadDicomHeadersAPI(data) {
    let response = null
    try {
        response = await fetch(`${API_BASE_URL}/classify`, {
            method: 'POST',
            body: data
        })
    } catch(error) {
        console.log(error)
        // If an error has occurred, the response is empty, so we assign it an item containing only the information
        // that the response is not ok.
        response = {ok: false}
    }
    return response
}


export async function uploadProjectDataAPI(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        body: data,
        headers: {
            ...getAuthHeaders()
        },
    });

    if (response.ok) {
        result = await response.json();
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText);
    }

    return result
}


export async function uploadSequenceTypesAPI(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/sequences`, {
        method: 'PATCH',
        headers: {
            ...getAuthHeaders()
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
    return await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
        },
        body: data
    })
}

export async function getSegmentationAPI(segmentationID) {
    const response = await fetch(`${API_BASE_URL}/segmentations/${segmentationID}/imagedata`, {
        method: 'GET',
        headers: {
            ...getAuthHeaders(),
        },
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
                if (['t1', 't1km', 't2', 'flair'].includes(sequenceType)) {
                    if (images.fileType === "NIFTI") {
                        images[sequenceType] = imageFile;
                    } else {
                        images[sequenceType].push(imageFile);
                    }
                } else {
                    images.labels = [...images.labels, imageFile]
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


export async function getAllSegmentationStatusesAPI() {
    return await fetch(`${API_BASE_URL}/segmentations/status`, {
        method: 'GET',
        headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
        },
    })
}


export async function getSegmentationStatusAPI(segmentationID) {

    try {
        const response = await fetch(`${API_BASE_URL}/segmentation/${segmentationID}/status`, {
            method: 'GET',
            headers: {
                ...getAuthHeaders(),
            },        
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch segmentation status: ${response.statusText}`);
        }

        const data = await response.json();
        return data.status;

    } catch (error) {
        console.error("Error in getSegmentationStatusAPI:", error);
        throw error; 
    }
}


export async function loginAPI(user_mail, password) {
    let ret = { error: null, session_token: null };

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_mail, password }),
            mode: 'cors',
            credentials: 'include',
        });

        if (response.ok) {
            const data = await response.json();
            ret.session_token = data.session_token;
        } else {
            const data = await response.json();
            ret.error = data.message;
            console.log("ERROR: " + data.err)
        }
    } catch (err) {
        ret.error = err.message;
    }

    return ret;
}

export async function accountCreationAPI(user_mail, password) {
    let ret = { error: null, session_token: null };

    try {
        const response = await fetch(`${API_BASE_URL}/auth/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_mail, password }),
            mode: 'cors',
            credentials: 'include',
        });

        if (response.ok) {
            const data = await response.json();
            ret.session_token = data.session_token;
        } else {
            const data = await response.json();
            ret.error = data.message;
        }
    } catch (err) {
        ret.error = err.message;
    }

    return ret;
}


/**
 * This function logs the user out and returns the error of the logout attempt
 * @param session_token the users session token, which will be deleted in database
 * 
 * @returns the error received by the backend. No error meaning success.
 */
export async function logoutAPI(session_token) {
    let return_error = null
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders()
            },        
        });
        if (response.ok) {
            return return_error;
        }
        else {
            const data = await response.json();
            return_error = data.message;
        }
    } catch (err) {
        return_error = err.message
    }
    
    return return_error
};


export async function getUserIDAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/userID`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders()
            },
        });
        if (response.ok) {
            const data = await response.json();
            return data.user_id;
        } else
        return null
    } catch (err) {
        console.log("Error validating session_token: " + err)
    }
    return null
}

function getAuthHeaders() {
    const token = sessionStorage.getItem('session_token');
    return {
        'Authorization': `Bearer ${token}`
    };
}
