# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.12-slim as build

VOLUME /data

# Set the working directory
WORKDIR /app
COPY . /app

# Install tools
RUN apt-get update && apt-get install -y dnsutils net-tools iputils-ping

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir redis requests

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run job_monitor.py when the container launches
CMD ["python", "job_monitor.py"]
