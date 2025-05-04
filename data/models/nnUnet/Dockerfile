# Use the PyTorch image with CUDA 12.1 support
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# Set the working directory in the container
WORKDIR /app

# Create brainns user and group with fixed UID and GID (match host)
RUN groupadd -g 1050 brainns && \
    useradd -m -u 1050 -g 1050 brainns

# Install nnU-Net
RUN pip install nnunet

# Create input directory and set permissions
RUN mkdir input && chown -R brainns:brainns /app

# Set Environment Variables
ENV nnUNet_raw_data_base=/app/nnUNet_raw_data_base
ENV nnUNet_preprocessed=/app/nnUNet_preprocessed
ENV RESULTS_FOLDER=/app/nnUNet_trained_models


# COPY weights and other files for nnunet
COPY --chown=brainns:brainns /nnunet/ /app/

# Switch to brainns user
USER brainns