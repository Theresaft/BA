// HERE WE MAKE API CALLS AND FORMAT DATA  

const API_BASE_URL = 'http://localhost:5001/brainns-api'
// const API_BASE_URL = 'https://141.83.20.81/brainns-api'

export async function getNiftiById (id){

    // Make api call
    const response = await fetch(`${API_BASE_URL}/nifti/${id}`, {
        method: 'GET',
    });

    // Format data
    const blob = await response.blob();		
    
    return blob;
}


export async function uploadFiles(data) {
    let result;

    const response = await fetch(`${API_BASE_URL}/assign-sequence-types`, {
        method: 'POST',
        body: data
    });

    if (response.ok) {
        result = await response.json();
    } else {
        console.error('Fehler bei der Anfrage:', response.statusText);
    }
    
    console.log(result);
    
    return result
  }