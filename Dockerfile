FROM python:3.11-slim
WORKDIR /app
COPY ecotrace/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ecotrace/ .
# Hugging Face exposes port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
