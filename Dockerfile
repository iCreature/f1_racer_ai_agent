FROM python:3.12-slim

WORKDIR /app

# Append src to Python's module search path
ENV PYTHONPATH="$PYTHONPATH:/app/src"

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

EXPOSE 8000

# Exec-form CMD ensures flags go to Uvicorn directly
CMD ["uvicorn", "src.api.main:app", "--host", "localhost", "--port", "8000"]

