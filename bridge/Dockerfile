FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if any (not needed for now)
# RUN apt-get update && apt-get install -y ...

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command
CMD ["python", "main.py"]
