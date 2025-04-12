# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# Ensure build dependencies like gcc might be needed for some libraries (though unlikely for these)
# RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/* # Example if needed
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on *inside* the container (not published to host)
EXPOSE 8001

# Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
