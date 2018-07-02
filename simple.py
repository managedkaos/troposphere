'''Module: Make an EC2 Instance'''
import time
import troposphere.ec2 as ec2
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
from troposphere.cloudformation import Init, InitConfig, InitFiles, InitFile, Metadata
from troposphere.policies import CreationPolicy, ResourceSignal
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
    password_param = template.add_parameter(
        Parameter(
            'PassWord',
            Type='String',
            NoEcho=True,
            MinLength=8,
            MaxLength=64,
            Description='Password for the admin account',
            ConstraintDescription='A complex password at least eight chars long with alphanumeric characters, dashes and underscores.',
            AllowedPattern="[-_a-zA-Z0-9]*",
        )
    )

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
            ],
        )
    )

    ec2_instance = template.add_resource(
        ec2.Instance(
            'Instance',
            Metadata=Metadata(
            Init({
                    "config": InitConfig(
                        files=InitFiles({
                            "/etc/nginx/conf.d/app.conf": InitFile(
                                content='server { listen 80 default_server; listen [::]:80  default_server; location / { proxy_pass http://localhost:8080; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; } }',
                                mode="000644",
                                owner="root",
                                group="root"
                            )
                        }),
                    )
                }),
            ),
            CreationPolicy=CreationPolicy(
                ResourceSignal=ResourceSignal(
                Timeout='PT15M')),
            Tags=[{'Key':'Name', 'Value':'Simple Stack Instance {}'.format(time.strftime('%c'))},],
            ImageId='ami-39c28c41',
            InstanceType='t2.micro',
            KeyName=Ref(keyname_param),
            SecurityGroups=[Ref(ec2_security_group)],
            UserData=Base64(
                Join(
                    '',
                    [
                        '#!/bin/bash -x\n',
                        'exec > /tmp/user-data.log 2>&1\n'
                        'apt-get update\n',
			            'apt-get install -y python-pip\n',
			            'pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n',
                        'apt-get install -y nginx\n',
                        'apt-get install -y openjdk-8-jdk\n',
                        '/usr/local/bin/cfn-init --verbose --resource=Instance --region=', Ref('AWS::Region'), ' --stack=', Ref('AWS::StackName'), '\n',
                        'unlink /etc/nginx/sites-enabled/default\n'
                        'systemctl reload nginx\n',
                        '/usr/local/bin/cfn-signal -e 0 --resource Instance --region us-west-2 --stack simple\n',
                    ]
                )
            )
        )
    )

    template.add_output([
        Output(
            'PublicDnsName',
            Description='PublicDnsName',
            Value=GetAtt(ec2_instance, 'PublicDnsName'),
        ),
    ])

    print(template.to_yaml())

if __name__ == '__main__':
    main()
