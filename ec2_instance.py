'''Module: Make an EC2 Instance'''
import time
import troposphere.ec2 as ec2
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
from troposphere.cloudformation import Init, InitConfig, InitFiles, InitFile
from troposphere.cloudformation import Metadata, WaitCondition, WaitConditionHandle
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

    #wait_handle = template.add_resource(WaitConditionHandle("waithandle"))

    #wait_condition = template.add_resource(
    #    WaitCondition(
    #        "waitcondition",
    #        Handle=Ref(wait_handle),
    #        Count=1,
    #        Timeout="600",
    #    )
    #)

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
            Metadata=Metadata(
            Init({
                    "config": InitConfig(
                        files=InitFiles({
                            "/etc/nginx/conf.d/jenkins.conf": InitFile(
                                content='upstream jenkins { server localhost:8080; } server { listen 80 default_server; listen [::]:80  default_server; location / { proxy_pass http://jenkins; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; } }',
                                mode="000644",
                                owner="root",
                                group="root"
                            )
                        }),
                    )
                }),
            ),
            Tags=[{'Key':'Name', 'Value':'Stack Instance {}'.format(time.strftime('%c'))},],
            ImageId=FindInMap('RegionMap', Ref('AWS::Region'), 'ami'),
            InstanceType='t2.micro',
            KeyName=Ref(keyname_param),
            SecurityGroups=[Ref(ec2_security_group)],
            UserData=Base64(
                Join(
                    '',
                    [
                        '#!/bin/bash -x\n',
                        'exec > /tmp/user-data.log 2>&1\n'
                        'unset UCF_FORCE_CONFFOLD\n',
                        'export UCF_FORCE_CONFFNEW=YES\n',
                        'ucf --purge /boot/grub/menu.lst\n',
                        'export DEBIAN_FRONTEND=noninteractive\n',
                        'echo "deb http://pkg.jenkins-ci.org/debian binary/" > /etc/apt/sources.list.d/jenkins.list\n',
                        'wget -q -O jenkins-ci.org.key http://pkg.jenkins-ci.org/debian-stable/jenkins-ci.org.key\n'
                        'apt-key add jenkins-ci.org.key\n',
                        'apt-get update\n',
                        '#apt-get -o Dpkg::Options::="--force-confnew" --force-yes -fuy upgrade\n',
			            'apt-get install -y python-pip\n',
			            'pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n',
                        'apt-get install -y nginx\n',
                        'apt-get install -y openjdk-8-jdk\n',
                        'apt-get install -y jenkins\n',
                        '/usr/local/bin/cfn-init --verbose --resource=Instance --region=', Ref('AWS::Region'), ' --stack=', Ref('AWS::StackName'), '\n',
                        'unlink /etc/nginx/sites-enabled/default\n'
                        'systemctl reload nginx\n',
                        'cat /var/lib/jenkins/secrets/initialAdminPassword\n',
                        #'/usr/local/bin/cfn-signal --region=', Ref('AWS::Region'), ' --stack=', Ref('AWS::StackName'), Ref(wait_condition), '\n',
                        #'/usr/local/bin/cfn-signal --success=true --data="{key:value}" ', Ref(wait_condition), '\n',
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
