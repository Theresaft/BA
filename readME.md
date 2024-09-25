# Fallstudie 2024 (still looking for a name)

## Overview

This is how the folder structure should look like:
```
fallstudie-ss2024/
├── backend/
│   ├── image-repository/
│   │   ├── user_id/
│   │   │   ├── project_id/
│   │   │   ├── project_id/
│   │   │   │   ├── raw/
│   │   │   │   ├── preprocessed/
│   │   │   │   └── segmentations/
│   │   └── user1/
│   ├── models/
│   │   ├── nnUnet/
│   │   │   ├── nnunet/
│   │   │   │   ├── nnUNet_trained_models/
│   │   │   │   ├── nnUNet_raw_data_base/
│   │   │   │   └── nnUNet_preprocessed/
│   │   │   └── Dockerfile
│   │   └── docker-compose.yml
│   ├── server/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── wait-for-it.sh
│   └── worker.py
├── dashboard/
├── db-data/
├── frontend/
├── redis-data/
├── Segmentation/
├── .env
└── docker-compose.yml 

```

## Setup

1. **Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)**
2. **Create a data repository for the images**:
    - Create a directory called `image-repository` inside the backend folder. This is where raw images, preprocessed images and segmentations of the users will be saved.
3. **Create the AI Models:**
   - Download model weights: [Model Weights](https://drive.google.com/file/d/19E8xXUEtcx-O4Z6GIdoxK6OVXoTSMl-R/view)
   - Create a directory called `nnunet` inside `models/nnUnet/`
   - Copy the unzipped weights aka. the `nnUNet_trained_models` folder into `models/nnUnet/nnunet/`. (Note: `nnUNet_preprocessed` and `nnUNet_raw_data_base` will be created automatically.)
   - Execute the following command inside the ``models`` directory to create the AI models: 
     ```
     docker-compose up --build
     ```
4. **Create a .env file:** 
   - Create a `.env` file inside the `fallstudie-ss2024` folder.
   - Add the following content to `.env`, adjusting `DATA_PATH` to match your `image-repository` directory created in step 2:
     ```
     FLASK_DEBUG=1 # Activates useful features for development (e.g. Auto-reloading)
     DATA_PATH=/path/to/your/backend/image-repository # Path to the directory with image data
     ``` 

## Start

1. **Navigate to the `fallstudie-ss2024` directory**
2. **Execute the following command:**
    ```
    docker-compose up --build
    ```

## Stop

1. **Press `Ctrl + C` to stop Docker containers**
2. **Execute the following command to remove containers:**
    ```
    docker-compose down
    ```

## Connecting to the database using a client
1. Download a mysql compatible database client like [MySQL-Workbench](https://dev.mysql.com/downloads/workbench/)
2. Connect to the database with the following configuration:
    ```
    Hostname: 127.0.0.1
    Port: 3306
    Username: user
    Password: user_password
    ```

## Resetting the database
1. Make sure the docker containers are removed:
    ```    
    docker-compose down
    ```
2. Delete the `db-data` folder completely
3. Delete everything in the `image-repository` folder
4. Recreate Containers
    ```    
    docker-compose up --build
    ```


## Start a prediction
1. **Create a User**
- Send a post request to: http://127.0.0.1:5001/auth/users with the following body: 
    ```
    {
        "username": "superman",
        "password": "securepasSword123"
    }
    ```
2. **Create a Project**
- Send a post request to http://127.0.0.1:5001/projects with the following body:

    ```
    {
        "project_name": "my segmentaiton project",
        "sequences": [
            {
                "sequence_name": "sequence_001",
                "sequence_type": "t1"
            },
            {
                "sequence_name": "sequence_002",
                "sequence_type": "t1km"
            },
            {
                "sequence_name": "sequence_003",
                "sequence_type": "t2"
            },
            {
                "sequence_name": "sequence_004",
                "sequence_type": "flair"
            }
        ]
    }
    ```
- This will create the necessary DB-Entries (project and sequences) as well as the folder structure under:  
    `fallstudie-ss2024/backend/image-repository/1/1` 
3. **Start a Prediction**
- Download some test data (currently still nifty) from [here](https://drive.google.com/drive/folders/1i0cO-fjB45EjqiNFzurReetvMNilN7fc?usp=sharing).
- Copy the test data into the newly created folder `fallstudie-ss2024/backend/image-repository/1/1/raw` .
    - Note: The User ID and the Project ID (both "1") are currently hardcoded into the route.
- Send a post request without a body to: http://127.0.0.1:5001/predict

## Services

- API: http://localhost:5001
- Queue Dashboard: http://localhost:9181
- Database: mysql://localhost:3306