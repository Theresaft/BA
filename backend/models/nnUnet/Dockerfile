# Use the PyTorch image with CUDA 12.1 support
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# Set the working directory in the container
WORKDIR /app

# Install nnU-Net
RUN pip install nnunet
RUN mkdir input


# Set Environment Variables
ENV nnUNet_raw_data_base=/app/nnUNet_raw_data_base
ENV nnUNet_preprocessed=/app/nnUNet_preprocessed
ENV RESULTS_FOLDER=/app/nnUNet_trained_models


# COPY weights and other files for nnunet
COPY /nnunet/ /app/
