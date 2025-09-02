FROM python:3.11-slim

COPY . /app

WORKDIR /app

RUN pip install uv
RUN uv pip install -r requirements.txt --system

CMD ["/bin/sh", "-c", "python service.py"]