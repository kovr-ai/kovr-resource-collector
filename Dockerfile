FROM python:3.12-alpine

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENV AWS_ACCESS_KEY_ID=AKIAX5678901234567890
ENV AWS_SECRET_ACCESS_KEY=1234567890123456789012345678901234567890
ENV AWS_SESSION_TOKEN=1234567890123456789012345678901234567890

RUN mkdir -p ~/.aws
RUN echo "[default]" > ~/.aws/credentials
RUN echo "aws_access_key_id = $AWS_ACCESS_KEY_ID" >> ~/.aws/credentials
RUN echo "aws_secret_access_key = $AWS_SECRET_ACCESS_KEY" >> ~/.aws/credentials
RUN echo "aws_session_token = $AWS_SESSION_TOKEN" >> ~/.aws/credentials

ENTRYPOINT ["python", "scanner.py"]