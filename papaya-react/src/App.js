import React, { useState } from 'react';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [params, setParams] = useState({ kioskMode: false });

  const updateImage = () => {
    if (!selectedFile) return;
    try {
      const selectedFileURL = URL.createObjectURL(selectedFile);
      setParams({ ...params, images: [selectedFileURL] });
      window.papaya.Container.resetViewer(0, params);
    } catch (error) {
      console.error(error);
    }
  };

  const selectFile = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ width: '800px' }}>

        {/* Papaya */}
        <div id="papaya_viewer" className="papaya" ref={null}></div>

        <form style={{ margin: '10px' }} onSubmit={(e) => { e.preventDefault(); updateImage(); }}>
          <h3>Upload file:</h3>
          <input type="file" required onChange={selectFile} />

          <button type="submit">
            Visualize image
          </button>
        </form>

      </div>
    </div>
  );
}

export default App;
