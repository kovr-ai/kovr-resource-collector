import boto3
import json
import time
import traceback

from con_mon.utils.config import settings

from main_new import wrapper as run_pipeline

sqs = boto3.client("sqs", region_name=settings.AWS_REGION)


def delete_message(handle):
    sqs.delete_message(
        QueueUrl=settings.CONNECTOR_QUEUE,
        ReceiptHandle=handle,
    )


def main():
    count = 0
    while True:
        try:
            print(f"Listening for messages at {time.time()}")
            response = sqs.receive_message(
                QueueUrl=settings.CONNECTOR_QUEUE,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
            )
            messages = response.get("Messages", [])
            if not messages:
                if count >= 10:
                    print(f"No messages received after {count} attempts")
                    break
                count += 1
                continue
            count = 0
            for message in messages:
                print("Received message at", time.time())
                handle = message.get("ReceiptHandle")
                body = message.get("Body")
                try:
                    message = json.loads(body)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    continue
                try:
                    print("Running pipeline", message)
                    delete_message(handle)
                    run_pipeline(message)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    continue
        except Exception as e:
            print(e)
            continue


if __name__ == "__main__":
    main()
