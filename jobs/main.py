import json
import os
import random
import sys
import time

# Retrieve Job-defined env vars
TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)
# Retrieve User-defined env vars
SLEEP_MS = os.getenv("SLEEP_MS", 0)
FAIL_RATE = os.getenv("FAIL_RATE", 0)


# Define main script
def main(sleep_ms=0, fail_rate=0):
    print(f"Starting Task #{TASK_INDEX}, Attempt #{TASK_ATTEMPT}...")
    # Simulate work by waiting for a specific amount of time
    time.sleep(float(sleep_ms) / 1000)  # Convert to seconds

    # Simulate errors
    random_failure(float(fail_rate))

    print(f"Completed Task #{TASK_INDEX}.")


# Throw an error based on fail rate
def random_failure(rate):
    if rate < 0 or rate > 1:
        # Return without retrying the Job Task
        print(
            f"Invalid FAIL_RATE env var value: {rate}. " +
            "Must be a float between 0 and 1 inclusive."
        )
        return

    random_failure = random.random()
    if random_failure < rate:
        raise Exception("Task failed.")


# Start script
if __name__ == "__main__":
    try:
        main(SLEEP_MS, FAIL_RATE)
    except Exception as err:
        message = f"Task #{TASK_INDEX}, " \
                  + f"Attempt #{TASK_ATTEMPT} failed: {str(err)}"

        print(json.dumps({"message": message, "severity": "ERROR"}))
        sys.exit(1)  # Retry Job Task by exiting the process

"""
in terminal at containing folder i ran this:

gcloud builds submit --pack image=gcr.io/spikeline/logger-job

which builds the container.

then i ran this:

gcloud beta run jobs create job-quickstart \
    --image gcr.io/spikeline/logger-job \
    --tasks 50 \
    --set-env-vars SLEEP_MS=10000 \
    --set-env-vars FAIL_RATE=0.5 \
    --max-retries 5 \
    --region us-central1
    
which creates the job.

Next i ran this to run the job:

gcloud beta run jobs execute job-quickstart
"""