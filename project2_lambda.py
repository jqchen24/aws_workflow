# first lambda
import json
import boto3
import base64

s3 = boto3.client('s3')



def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event['s3_bucket']

    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, '/tmp/image.png')

    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

# second lambda

import json
import base64
import os
import boto3
# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')

# Fill this in with the name of your deployed model
ENDPOINT = 'image-classification-2022-01-19-19-01-34-821'

## Need to provide actual output of first lambda action to the test event.
def lambda_handler(event, context):
    # print(event)
    
    # # Decode the image data
    image = base64.b64decode(event['image_data'])   ## only good for test event
    # image = base64.b64decode(event['body']['image_data']) 
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                      ContentType='image/png',
                                      Body=image)    
    # print(response)
                                
    
    result = json.loads(response['Body'].read())

    print('result is:', result)

    # We return the data back to the Step Function    
    event["inferences"] = result

    # event["body"]["inferences"] = result
    return {
          "statusCode": 200,
        #   "body": json.dumps(event["body"])
          "body": json.dumps(event)
    }


## Third lambda 

import json


THRESHOLD = .93


def lambda_handler(event, context):

    # Grab the inferences from the event
    print('event is: ', event)
    inferences = event['inferences']
    # inferences = event['body']['inferences']

    # body = json.loads(event['body'])
    # inferences = json.loads(body['inferences'])
    
    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = inferences[0] > THRESHOLD or inferences[1] > THRESHOLD
    print('whether meets threshold:', meets_threshold)
    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")
    
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }