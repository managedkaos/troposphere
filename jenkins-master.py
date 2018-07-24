'''Module: Make an EC2 Instance'''
import time
import troposphere.ec2 as ec2
from troposphere.iam import Role, InstanceProfile, Policy
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
from troposphere.cloudformation import Init, InitConfig, InitFiles, InitFile, Metadata
from troposphere.policies import CreationPolicy, ResourceSignal
from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole

def main():
    '''Function: Generates the Cloudformation template'''
    template = Template()

    keyname_param = template.add_parameter(
        Parameter(
            'KeyName',
            Description='Name of an existing EC2 KeyPair for SSH access',
            ConstraintDescription='Must be the name of an existing EC2 KeyPair.',
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

    template.add_mapping('RegionMap', {'ap-south-1': {'ami': 'ami-ee8ea481'}, 'eu-west-3': {'ami': 'ami-daf040a7'}, 'eu-west-2': {'ami': 'ami-ddb950ba'}, 'eu-west-1': {'ami': 'ami-d2414e38'}, 'ap-northeast-2': {'ami': 'ami-65d86d0b'}, 'ap-northeast-1': {'ami': 'ami-e875a197'}, 'sa-east-1': {'ami': 'ami-ccd48ea0'}, 'ca-central-1': {'ami': 'ami-c3e567a7'}, 'ap-southeast-1': {'ami': 'ami-31e7e44d'}, 'ap-southeast-2': {'ami': 'ami-23c51c41'}, 'eu-central-1': {'ami': 'ami-3c635cd7'}, 'us-east-1': {'ami': 'ami-5cc39523'}, 'us-east-2': {'ami': 'ami-67142d02'}, 'us-west-1': {'ami': 'ami-d7b355b4'}, 'us-west-2': {'ami': 'ami-39c28c41'}})

    ec2_security_group = template.add_resource(
        ec2.SecurityGroup(
            'SecurityGroup',
            Tags=[{'Key':'Name', 'Value':'Jenkins Master {}'.format(time.strftime('%c'))},],
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
                ResourceSignal=ResourceSignal(Timeout='PT15M')
            ),
            Tags=[{'Key':'Name', 'Value':'Jenkins Master {}'.format(time.strftime('%c'))},],
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
                        'apt-get -o Dpkg::Options::="--force-confnew" --force-yes -fuy upgrade\n',
                        'apt-get install -y python-pip\n',
                        'pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n',
                        'apt-get install -y nginx\n',
                        'apt-get install -y openjdk-8-jdk\n',
                        'apt-get install -y jenkins\n',
                        '# Wait for Jenkins to Set Up\n'
                        "until [ $(curl -o /dev/null --silent --head --write-out '%{http_code}\n' http://localhost:8080) -eq 403 ]; do sleep 1; done\n",
                        'sleep 10\n',
                        '# Change the password for the admin account\n',
                        "echo 'jenkins.model.Jenkins.instance.securityRealm.createAccount(\"admin\", \"",Ref(password_param),"\")' | java -jar /var/cache/jenkins/war/WEB-INF/jenkins-cli.jar -s \"http://localhost:8080/\" -auth \"admin:$(cat /var/lib/jenkins/secrets/initialAdminPassword)\" groovy =\n",
                        '/usr/local/bin/cfn-init --resource=Instance --region=', Ref('AWS::Region'), ' --stack=', Ref('AWS::StackName'), '\n',
                        'unlink /etc/nginx/sites-enabled/default\n',
                        'systemctl reload nginx\n',
                        '/usr/local/bin/cfn-signal -e $? --resource=Instance --region=', Ref('AWS::Region'),
                        ' --stack=', Ref('AWS::StackName'), '\n',
                    ]
                )
            )
        )
    )

    template.add_output([
        Output(
            'PublicDnsName',
            Description='PublicDnsName',
            Value=Join('',['http://', GetAtt(ec2_instance, 'PublicDnsName'),])
        ),
    ])

    print(template.to_yaml())

if __name__ == '__main__':
    main()
