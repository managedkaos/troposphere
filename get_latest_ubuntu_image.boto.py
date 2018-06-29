import boto3
import json

session = boto3.Session(profile_name='devday')
client = session.client('ec2')
'''
aws ec2 describe-images \
 --filters Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64* \
 --query 'Images[*].[ImageId,CreationDate]' --output text \
 | sort -k2 -r \
 | head -n1
'''
response = client.describe_images(
    Filters=[
        {
            'Name': 'name',
            'Values': [ 'ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64*', ]
        },
    ],
)

# print(json.dumps(response['Images']))
for image in response['Images']:
    print(image['ImageId'])
