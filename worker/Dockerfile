# Teacher-labelling worker image (Task 1).
FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

WORKDIR /app

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/storage.py worker/label_worker.py worker/clean.py ./
COPY prompts/teacher_prompt.txt ./prompts/teacher_prompt.txt

ENV PROMPT_FILE=/app/prompts/teacher_prompt.txt \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "label_worker.py"]
