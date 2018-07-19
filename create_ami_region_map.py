'''
Module: Creates an AMI region map
'''
import sys
import boto3

def create_ami_region_map(profile_name='mmx', ami_description='ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64*'):
    """
    Function: Takes an AMI description as input and looks in each region for AMI's
    that match.  Returns a dict of the matches using the regions as keys.
        {
            'us-east-1':{'ami':'ami-5cc39523'},
            'us-west-1':{'ami':'ami-d7b355b4'},
            ...
        }
    """
    ami_region_map = dict()

    session = boto3.Session(profile_name=profile_name)
    client = session.client('ec2')

    response = client.describe_regions()

    for region in response['Regions']:
        client2 = session.client('ec2', region_name=region['RegionName'])

        response = client2.describe_images(
            Filters=[
                {'Name': 'name', 'Values': [ami_description]}
            ]
        )

        image = sorted(response['Images'], key=lambda k: k['CreationDate'], reverse=True)[0]

        ami_region_map[region['RegionName']] = {'ami':image['ImageId']}

    return ami_region_map

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print(create_ami_region_map(profile_name=sys.argv[1], ami_description=sys.argv[2]))
    else:
        print(create_ami_region_map())
