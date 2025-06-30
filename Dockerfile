# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set up a non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Install system dependencies required for some Python packages
# (Add any other system dependencies here if needed, e.g., gcc for C extensions)
# We are using a slim image, so we may need to install build-essential if any packages require compilation
# For now, we'll try without it and add it if the pip install fails.
# RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /home/appuser
COPY --chown=appuser:appuser requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY --chown=appuser:appuser . .

# Set the PYTHONPATH to include the current directory
ENV PYTHONPATH "${PYTHONPATH}:/home/appuser"
# Set a default port for the application
ENV PORT 8000

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run your app using uvicorn
# Use the main.py entry point which delegates to src/main.py
# Add verbose logging for container diagnostics
CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info", "--access-log"]
