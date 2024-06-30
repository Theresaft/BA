# Use the PyTorch image with CUDA 12.1 support
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# Set the working directory in the container
WORKDIR /app

# Install nnU-Net
RUN pip install nnunet

# Set Environment Variables
ENV nnUNet_raw_data_base=/app/nnunet/nnUNet_raw_data_base
ENV nnUNet_preprocessed=/app/nnunet/nnUNet_preprocessed
ENV RESULTS_FOLDER=/app/nnunet/nnUNet_trained_models


RUN pip install flask
COPY api.py /app/

#CMD nnUNet_predict -i $nnUNet_raw_data_base/nnUNet_raw_data/Task001_BrainTumour/imagesTs/ -o /app/nnunet/output -t 1 -m 3d_fullres
#CMD nnUNet_predict -i /app/nnunet/input -o /app/nnunet/output -t 1 -m 3d_fullres

CMD ["python", "api.py"]
