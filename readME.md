# **BRAINNS** 
*Brain Research using AI-based Neural Network Segmentation*

## Overview

This is what the folder structure should look like:
```
fallstudie-ss2024/
├── backend/
│   ├── server/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── worker.py
├── dashboard/
├── data/
│   ├── db-data/
│   ├── image-repository/
│   ├── models/
│   ├── nnUnet/
│   │   ├── nnunet/
│   │   │   ├── nnUNet_trained_models/
│   │   │   ├── nnUNet_raw_data_base/
│   │   │   └── nnUNet_preprocessed/
│   │   └── Dockerfile
│   └── redis-data/
├── frontend/
├── own-model/
├── preprocessing/
├── .env
├── .gitignore
├── .gitlab-ci.yml
├── docker-compose.production.yml 
├── docker-compose.yml 
├── nginx.conf 
└── readME.md

```
## Prerequisites
1. In order to run the project locally, you need to have docker and docker compose installed. The easiest way to install both is by installing [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Clone the repository:
```
git clone https://git.imi.uni-luebeck.de/aghandels/fallstudie-ss2024.git
```

## Setup
1. **Create a data repository for the images**:
    - Create a directory called `image-repository` inside the `fallstudie-ss2024/data` folder. This is where raw images, preprocessed images and segmentations of the users will be saved.

2. **Create a .env file:** 
   - Create a `.env` file inside the `fallstudie-ss2024` folder.
   - Add the following content to the `.env` and adjust `DATA_PATH` to match the absolute path of your `image-repository` directory created in step 1. (Make sure to only use forward slashes):
   - Set the username and password as well as the root password of your database
     ```
     FLASK_DEBUG=1 # Activates useful features for development (e.g. Auto-reloading)
     DATA_PATH=C:/User/fallstudie-ss2024/data/image-repository # Path to the directory with image data
     MYSQL_DATABASE=my_database
     MYSQL_USER=
     MYSQL_PASSWORD=
     MYSQL_ROOT_PASSWORD=
     ``` 

3. **Create the AI Models:**
   - Download model weights: [Model Weights](https://drive.google.com/file/d/19E8xXUEtcx-O4Z6GIdoxK6OVXoTSMl-R/view)
   - Create a directory called `nnunet` inside `data/models/nnUnet/`
   - Copy the unzipped weights aka. the `nnUNet_trained_models` folder into `data/models/nnUnet/nnunet/`. 
   - **Note**: `nnUNet_raw_data_base/` and `nnUNet_preprocessed` will be created automatically.
   - **Note**: You don't need to create the docker images for the models manually. They will be created automatically when the first prediction is started (This can easily take more then 20 min).


## Start the app
1. **Navigate to the `fallstudie-ss2024` directory**
2. **Execute the following command:**
    ```
    docker-compose up --build
    ```
This will start up the containers for all the services.


## Stop the app
1. **Press `Ctrl + C` to stop Docker containers**
2. **Execute the following command to remove containers:**
    ```
    docker-compose down
    ```

## Resetting the database
Sometimes it's necessary to reset the database for example when changing something in the database schema. This can be done as follows:

1. Make sure the docker containers are removed:
    ```    
    docker-compose down
    ```
2. Delete the `db-data` folder completely
3. Delete the `image-repository` folder
4. Recreate Containers
    ```    
    docker-compose up --build
    ```

## Services
- Frontend: http://localhost:5173/brainns
- API: http://localhost:5001/brainns-api
- phpMyAdmin (Web database client): http://localhost:5080
- Database: mysql://localhost:3306
- Queue Dashboard: http://localhost:9181

## Next steps:
1. **Create an account**:
  - Open phpMyAdmin (http://localhost:5080)
  - Login using your database credentials (MYSQL_USER + MYSQL_PASSWORD)
  - Open `my_database` on the left
  - Open the `whitelist` table 
  - Add an email (can be fake) ending with `@uni-luebeck.de` or `@uksh.de`
  - Register the whitelisted account using the frontend (http://localhost:5173/brainns/)
2. [Create a project and start your first segmentation](User-Guides/How-to-create-a-project-and-start-a-segmentation-)
