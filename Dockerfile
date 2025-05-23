# Use Alpine as the base image
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Copy the application files (commented for development)
# COPY ./app /app

# Install dependencies
RUN pip install --no-cache-dir flask Flask-Limiter

# Expose port 8081
EXPOSE 8081

# Command to run the application
CMD ["python", "app.py"]
