'''Module: Make an EC2 Instance'''
import troposphere.ec2 as ec2
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
from create_ami_region_map import create_ami_region_map

def main():
    '''Function: Generates the Cloudformation template'''
    template = Template()

    keyname_param = template.add_parameter(
        Parameter(
            'KeyName',
            Description='Name of an existing EC2 KeyPair for SSH access',
            ConstraintDescription='must be the name of an existing EC2 KeyPair.',
            Type='AWS::EC2::KeyPair::KeyName',
        )
    )

    template.add_mapping('RegionMap', create_ami_region_map())

    ec2_security_group = template.add_resource(
        ec2.SecurityGroup(
            'SecurityGroup',
            GroupDescription='SSH, HTTP/HTTPS open for 0.0.0.0/0',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    CidrIp='0.0.0.0/0'),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='80',
                    ToPort='80',
                    CidrIp='0.0.0.0/0'),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='443',
                    ToPort='443',
                    CidrIp='0.0.0.0/0'),
            ],
        )
    )


    ec2_instance = template.add_resource(
        ec2.Instance(
            'Instance',
            Tags=[{'Key':'Name', 'Value':'Stack Instance'},],
            ImageId=FindInMap('RegionMap', Ref('AWS::Region'), 'ami'),
            InstanceType='t1.micro',
            KeyName=Ref(keyname_param),
            SecurityGroups=[Ref(ec2_security_group)],
            UserData=Base64(
                Join(
                    '',
                    [
                        '#!/bin/bash -xe\n',
                        'apt install -y nginx\n',
                    ]
                )
            )
        )
    )

    template.add_output([
        Output(
            'PublicDNS',
            Description='Public DNS',
            Value=GetAtt(ec2_instance, 'PublicDnsName'),
        ),
    ])

    print(template.to_yaml())

if __name__ == '__main__':
    main()
