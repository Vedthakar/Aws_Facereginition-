import os
import boto3
from decimal import Decimal
import time


# ─── Environment variables (set these in Configuration → Environment)
TABLE_NAME    = os.environ['DynomoDB_TABLE']
COLLECTION_ID   = os.environ['Collection_ID']  
print("🔍 All env vars:", dict(os.environ))  
print("🔍 TABLE_NAME is:", repr(TABLE_NAME))    
# ───────────────────────────────────────────────────────────────────────────────

dynamodb    = boto3.resource('dynamodb').Table(TABLE_NAME)
s3          = boto3.client('s3')
rekognition = boto3.client('rekognition')

def lambda_handler(event, context):
    # 0) Dump the raw event
    print("🔥 FULL EVENT PAYLOAD:", event)

    # 1) Loop every S3 record
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key    = record['s3']['object']['key']
        print(f" → Event for s3://{bucket}/{key}")

        # 3) Read the uploader’s metadata.fullname (fallback to key)
        head = s3.head_object(Bucket=bucket, Key=key)
        fullname = head.get('Metadata', {}).get('key', key)
        print(f"   Metadata fullname = {fullname}")

        # 4) Persist each new FaceId → FullName in DynamoDB
        try:
            dynamodb.put_item(
                TableName=TABLE_NAME,
                Item={
                    'FaceId': key,        # Corrected: simple value for FaceId
                    'Timestamp' : "0.0",  # or use time.time()
                    'Similarity': " ",
                    'S3Key': fullname  # Corrected: simple value for FullName
                }
            )
            print(f"   ✅ Wrote 'S3Key' → {fullname}")
        except Exception as e:
            print(f"   ❌ DynamoDB error: {e}")

        try:
            response = rekognition.index_faces(
                CollectionId=COLLECTION_ID,
                Image={'S3Object': {'Bucket': bucket, 'Name': key}},
                ExternalImageId=key,
                DetectionAttributes=['ALL']
            )
            print(f"Indexed face(s) from s3://{bucket}/{key} into collection {COLLECTION_ID}: {response}")
        except Exception as e:
            print(f"Error indexing face from s3://{bucket}/{key}: {e}")

    return {'statusCode': 200}
