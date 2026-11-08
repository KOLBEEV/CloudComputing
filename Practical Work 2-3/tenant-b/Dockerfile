FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY load.py /app/load.py
USER 10001:10001
CMD ["python", "/app/load.py"]
