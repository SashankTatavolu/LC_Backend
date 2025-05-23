# Use a more complete Python image to avoid missing dependencies
FROM python:3.9-buster

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    fonts-indic \
    apertium-all-dev \
    graphviz && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to cache dependencies
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt gunicorn  # Install Gunicorn

# Copy the rest of the app
COPY . /app

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

# Use Gunicorn to run Flask app with multiple workers
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
