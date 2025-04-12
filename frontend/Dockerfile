# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on *inside* the container
EXPOSE 8000

# Command to run the application using Uvicorn
# Use 0.0.0.0 to allow connections from outside the container within the Docker network
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
