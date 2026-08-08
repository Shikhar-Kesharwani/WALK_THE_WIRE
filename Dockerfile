FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS production
WORKDIR /app
RUN addgroup --system app && adduser --system --group app
COPY --from=builder /root/.local /home/app/.local
COPY src/ /app/src/
RUN chown -R app:app /app
USER app
ENV PATH=/home/app/.local/bin:$PATH
ENV PORT=5000
ENV FLASK_APP=src.web:app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
CMD ["gunicorn", "-b", "0.0.0.0:5000", "src.web:app"]
