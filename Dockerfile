# Use the official Python image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    && apt-get clean

# Set working directory
WORKDIR /code

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of your app
COPY ../exchange_api .

# Command to run your app (example)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
