# Use the PyTorch image with CUDA 11.8 support
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# Set the working directory in the container
WORKDIR /app
RUN mkdir input

# Copy segmentation files to /app
COPY /3D-Segmentation/ /app

# Install dependencies for our model (Torch/TorchIO)
COPY ./requirements.txt /app/requirements.txt

# install requirements
RUN pip install -r requirements.txt
