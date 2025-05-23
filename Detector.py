#!/usr/bin/env python3
import os
import time
import logging
from io import BytesIO

import boto3
import cv2

# ─── Configuration ─────────────────────────────────────────────────────────────
# You can also set these via environment variables in VS Code or your shell:
FRAME_RATE = int(os.getenv("FRAME_RATE", "30"))               # process every 30th frame
S3_BUCKET  = os.getenv("S3_BUCKET",  "intruder-dectector")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
# ────────────────────────────────────────────────────────────────────────────────

# ─── AWS Clients ───────────────────────────────────────────────────────────────
session = boto3.Session(region_name=AWS_REGION)
s3      = session.client("s3")
# (No Rekognition or DynamoDB here—your Lambda handles that)
# ────────────────────────────────────────────────────────────────────────────────

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# ────────────────────────────────────────────────────────────────────────────────

def upload_frame(frame, count):
    """
    Encode a frame as JPEG and upload to S3.
    The object key is a timestamp + frame count for uniqueness.
    """
    success, buf = cv2.imencode(".jpg", frame)
    if not success:
        logging.error("Failed to encode frame #%d", count)
        return

    key = f"{int(time.time())}_{count}.jpg"
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=buf.tobytes(),
            ContentType="image/jpeg"
        )
        logging.info("Uploaded frame #%d as %s", count, key)
    except Exception as e:
        logging.error("S3 upload failed for frame #%d: %s", count, e)


def main():
    logging.info("Starting video capture (every %d frames will be uploaded)", FRAME_RATE)
    cap = cv2.VideoCapture(0)  # `0` is your default webcam; adjust if you have multiple cameras
    if not cap.isOpened():
        logging.error("Could not open video device")
        return

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.warning("Frame read failed at count %d; stopping", frame_count)
                break

            # Flip horizontally
            flipped = cv2.flip(frame, 1)

            # Display the flipped frame **only**
            cv2.imshow("Flipped Live Feed (q to quit)", flipped)

            frame_count += 1
            if frame_count % FRAME_RATE == 0:
                # upload the flipped frame now
                upload_frame(flipped, frame_count)

            # Handle quit key
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logging.info("Quit signal received; exiting")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        logging.info("Video capture stopped")

if __name__ == "__main__":
    main()
