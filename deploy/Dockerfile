# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY . .

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "nodevault.main:app", "--host", "0.0.0.0", "--port", "8000"]
