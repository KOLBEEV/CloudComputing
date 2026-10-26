FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY server.py /app/server.py
USER 10001:10001
EXPOSE 8080
CMD ["python", "/app/server.py"]
