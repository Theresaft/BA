# Overview
This is how the folder structure should look like.
```
backend/
├── dashboard/
├── data/
│   ├── test_data/
│   │   ├── BRATS_485_0000.nii.gz
│   │   ├── BRATS_485_0001.nii.gz
│   │   ├── BRATS_485_0002.nii.gz
│   │   └── BRATS_485_0003.nii.gz
│   └── user1/
├── models/
│   ├── nnUnet/
│   │   ├── nnunet/
│   │   │   ├── nnUNet_trained_models/
│   │   │   ├── nnUNet_raw_data_base/
│   │   │   └── nnUNet_preprocessed/
│   │   └── Dockerfile
│   └── docker-compose.yml
├── redis/
├── server/
├── .env
└── docker-compose.yml 
```


# Setup

1. **Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)**
2. **Create a data repository for the images**:
    - Create a directory called `data` inside the backend folder
    - Inside the `data` directory, create another folder called `test_data` and add the [4 NIfTI files](https://drive.google.com/drive/folders/1i0cO-fjB45EjqiNFzurReetvMNilN7fc?usp=sharing) for testing purposes
    - Inside the `data` directory, create another folder called `user1` that will store all the data of user 1
3. **Create the AI Models:**
   - Download model weights: [Model Weights](https://drive.google.com/file/d/19E8xXUEtcx-O4Z6GIdoxK6OVXoTSMl-R/view)
   - Create a directory called `nnunet` inside `models/nnUnet/`
   - Copy the unzipped weights aka. the `nnUNet_preprocessed` folder into `models/nnUnet/nnunet/`. (Note: `nnUNet_trained_models` and `nnUNet_raw_data_base` will be created automatically.)
   - Execute the following command inside the ``models`` directory to create the AI models: 
     ```
     docker-compose up --build
     ```
4. **Create a directory called `redis` inside the backend folder** 
5. **Create a .env file:** 
   - Create a `.env` file inside the backend folder.
   - Add the following content to `.env`, adjusting `DATA_PATH` to match your `data` directory created in step 2:
     ```
     FLASK_DEBUG=1 # Activates useful features for development (e.g. Auto-reloading)
     APP_SETTINGS=server.config.DevelopmentConfig # Turns off CORS during development
     DATA_PATH=/path/to/your/backend/data # Path to the directory with image data
     ``` 

# Start
1. **Navigate to the `backend` directory**
2. **Execute the following command:**
    ```
    docker-compose up --build
    ```

# Stop
1. **Press `Ctrl + C` to stop Docker containers**
2. **Execute the following command:**
    ```
    docker-compose down
    ```

# Services
- API: http://localhost:5000
- Queue Dashboard: http://localhost:9181