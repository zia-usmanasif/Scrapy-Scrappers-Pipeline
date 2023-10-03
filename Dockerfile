# Use an official Python runtime as a parent image
FROM python:3.7-slim-bullseye

# Set the working directory to /app
RUN mkdir -p /home/app
RUN chmod -R 777 /home/app
WORKDIR /home/app

# Copy the requirements file into the container
COPY ./requirements.txt /home/app/requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container

COPY . /home/app/


# Set environment variables as needed (e.g., AWS credentials)
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
ENV S3PIPELINE_MAX_CHUNK_SIZE=10
ENV BUCKET_NAME=""
ENV SCRAPY_ENV="development"
ENV STANDALONE_SELENIUM_CHROME_DRIVER=True
ENV URI=http://host.docker.internal:4444/wd/hub
