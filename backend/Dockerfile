FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# sentence-transformers depends on PyTorch. Install the CPU wheel explicitly so
# pip does not pull multi-gigabyte CUDA libraries into this CPU-only service.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
