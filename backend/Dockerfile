FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-dev.txt ./

# Development: code is mounted in, and the server reloads on change.
FROM base AS dev
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production: no test tools, runs as a non-root user.
FROM base AS prod
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 1000 app && install -d -o app -g app /var/lib/wineapp
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
