FROM python:3.12-slim
WORKDIR /app
COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl
EXPOSE 8000
CMD ["snackapp", "run", "--host", "0.0.0.0", "--port", "8000"]
