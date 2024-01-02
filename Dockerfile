FROM python:3.9-slim

ARG POETRY_VERSION=1.3.2
ARG ENVIRONMENT=production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=$POETRY_VERSION \
    ENVIRONMENT=$ENVIRONMENT \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel "poetry==${POETRY_VERSION}"

COPY poetry.lock pyproject.toml ./

RUN if [ "$ENVIRONMENT" = "production" ]; then \
    poetry install --no-interaction --no-ansi --no-root; \
    else \
    poetry install --no-interaction --no-ansi --no-root --all-extras; \
    fi

COPY . .

EXPOSE 8000