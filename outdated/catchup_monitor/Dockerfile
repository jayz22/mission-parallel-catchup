FROM python:3.9-slim

# Install necessary packages
RUN pip install redis requests flask flask-socketio

# Copy the monitor script into the container
COPY monitor.py /monitor.py

# Run the monitor script
CMD ["python", "/monitor.py"]
