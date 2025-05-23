import os
import boto3
from decimal import Decimal
print('Loading function')

# Environment variables
COLLECTION_ID   = os.environ['Collection_ID'] 
DDB_TABLE       = os.environ['TABLE']      
SNS_TOPIC_ARN   = os.environ.get('ARN') 

rekognition = boto3.client('rekognition')
ddb          = boto3.resource('dynamodb').Table(DDB_TABLE)
sns          = boto3.client('sns')
print('working')
def lambda_handler(event, context):
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key    = record['s3']['object']['key']
        print(f"Processing {key} in {bucket}")

        # 1) Search for matches in your “allowed” collection
        resp = rekognition.search_faces_by_image(
            CollectionId=COLLECTION_ID,
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxFaces=1,
            FaceMatchThreshold=80
        )
        matches = resp.get('FaceMatches', [])
        print(f"Found {len(matches)} matches in {COLLECTION_ID} for {key}")
        # 2) If no matches → intruder alert
        if not matches:
            if SNS_TOPIC_ARN:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=f"🚨 Intruder detected in frame {key}"
                )
            continue

        # 3) Otherwise, log the allowed match to DynamoDB
        best = matches[0]
        item = {
            'FaceId'    : best['Face']['FaceId'],
            'Timestamp' : Decimal(str(context.aws_request_id)),  # or use time.time()
            'Similarity': Decimal(str(best['Similarity'])),
            'S3Key'     : key
        }
        ddb.put_item(Item=item)
        print(f"Allowed face {item['FaceId']} matched @ {item['Similarity']}% for {key}")

    return {'statusCode': 200}
