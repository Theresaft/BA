FROM python:3.12-alpine

# Install rq-dashboard without caching the packages
RUN pip install --no-cache-dir rq-dashboard

# Ensure the latest version of click is installed without caching
#RUN pip install --no-cache-dir --upgrade click

EXPOSE 9181

