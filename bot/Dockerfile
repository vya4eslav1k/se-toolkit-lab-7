# Bot Dockerfile
# Uses uv for dependency management from pyproject.toml

FROM python:3.12-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy bot project files (context is bot/)
COPY pyproject.toml uv.lock README.md ./
COPY lms_bot/ ./lms_bot/
COPY handlers/ ./handlers/
COPY services/ ./services/
COPY bot.py ./

# Install dependencies using uv
RUN uv sync --frozen

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Run the bot
CMD ["uv", "run", "bot.py"]
