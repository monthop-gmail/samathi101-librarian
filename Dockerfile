FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for pymupdf and others if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from requirements if possible, or directly
RUN pip install --upgrade pip
RUN pip install --no-cache-dir \
    google-genai \
    pymupdf4llm \
    python-frontmatter

# Copy the script
COPY scripts/ /app/scripts/

# The command to run the organizer
CMD ["python", "scripts/organize_files.py"]
