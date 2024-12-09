# Base image
FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

# Disable User interaction for installing packages
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.8 and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    python3 -m pip install --upgrade pip && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Install TensorFlow-GPU 2.6.2
RUN python -m pip install tensorflow-gpu==2.6.2


# Copy the DeepMedic Files
COPY ./DeepMedic /app
WORKDIR /app

# Create input and output directory
RUN mkdir input
RUN mkdir output/predictions/prediction_test/predictions

# Install the DeepMedic Dependencie
RUN pip install .

# Downgrades (compatibility issues)
RUN pip install protobuf==3.20.1
RUN pip install numpy==1.19.5
RUN pip install pandas==1.1.5
# Error when training 
# get_data() deprecated 
RUN pip install nibabel==2.5.1 



# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set default Python version
CMD ["python"]
