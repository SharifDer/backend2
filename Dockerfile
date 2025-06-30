# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy uv configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen

# Update package lists and install git
RUN apt-get update && \
    apt-get install -y git

COPY . /app
EXPOSE 8000

# Use uv run to execute uvicorn within the virtual environment
CMD ["uv", "run", "uvicorn", "run_apps:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]