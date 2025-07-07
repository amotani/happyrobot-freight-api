# Simple Python FastAPI Docker setup for Render
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render will set PORT environment variable)
EXPOSE $PORT

# Run the application
# Use shell form to properly resolve environment variables
CMD python -m uvicorn main:app --host 0.0.0.0 --port $PORT 