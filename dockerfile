# Use official Python 3.13 slim image
FROM python:3.13-slim

# Set working directory inside container
WORKDIR /app

# Copy project files into container
COPY . .

# Make sure start.sh is executable
RUN chmod +x start.sh

# Install Python dependencies (make sure you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Expose backend and frontend ports
EXPOSE 8000 8501

# Run your start.sh script when container starts
CMD ["./start.sh"]
