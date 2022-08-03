# syntax=docker/dockerfile:1.3
FROM python:3.10-slim-bullseye

RUN mkdir /app

COPY requirements.txt /app/

RUN --mount=type=cache,mode=0755,id=pip_cache,target=/root/.cache/pip \
    pip install -r /app/requirements.txt -i https://pypi.doubanio.com/simple

RUN mkdir -p /app/logs /app/db

COPY backend /app/backend

ENV ENV="production"

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0","--port", "8000",  "--proxy-headers"]