# Define variables
DOCKER_REPO = jayz22
IMAGE_NAME = job-monitor
TAG = latest

# Default target
all: build push

# Build the Docker image
build:
	docker build -t $(DOCKER_REPO)/$(IMAGE_NAME):$(TAG) .

# Push the Docker image to the repository
push:
	docker push $(DOCKER_REPO)/$(IMAGE_NAME):$(TAG)

# Clean up local Docker images
clean:
	docker rmi $(DOCKER_REPO)/$(IMAGE_NAME):$(TAG)
