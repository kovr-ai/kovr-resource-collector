FROM python:3.11-slim

COPY . /app

WORKDIR /app

ENV AWS_ACCESS_KEY_ID=aws_access_key_id
ENV AWS_SECRET_ACCESS_KEY=aws_secret_access_key
ENV AWS_SESSION_TOKEN=aws_session_token
ENV AWS_EXTERNAL_ID=aws_external_id

ENV AWS_REGION=aws_region
ENV AWS_ROLE_ARN=aws_role_arn

ENV APPLICATION_ID=application_id
ENV SOURCE_ID=source_id
ENV CONNECTION_ID=connection_id

ENV AZURE_CLIENT_ID=azure_client_id
ENV AZURE_CLIENT_SECRET=azure_client_secret
ENV AZURE_TENANT_ID=azure_tenant_id
ENV AZURE_SUBSCRIPTION_ID=azure_subscription_id

# ENV PROVIDER=provider

RUN pip install -r data_collector_requirements.txt

CMD ["/bin/sh", "-c", "python data_collector.py --provider aws"]