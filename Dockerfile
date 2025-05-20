# Step 1: Set base image
FROM python:3.12-slim

# Step 2: Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Step 3: Set working directory
WORKDIR /app

# Step 4: Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Step 5: Install Python dependencies
COPY requirements.txt .

# Upgrade pip and install packages listed in requirements.txt.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Step 6: Copy application code
COPY src .

# Step 7: (Optional) Collect static files if needed
# RUN python manage.py collectstatic --noinput

# Step 8: (Optional) Run database migrations
# RUN python manage.py migrate

# Step 9: Create and use a non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app
# Change ownership of the code directory
RUN chown -R app:app /app
# Switch to the app user
USER app

# Step 10: Expose port
EXPOSE 8000

# Step 11: Run the application server when the container starts
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conf.wsgi:application", "--workers", "3", "--threads", "2"]