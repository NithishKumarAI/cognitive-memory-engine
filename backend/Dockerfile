FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
COPY --chown=app:app . .
ENV PYTHONUNBUFFERED=1 HF_HOME=/home/app/.cache/huggingface
USER app
EXPOSE 8000
CMD ["python", "-m", "app.runtime"]
