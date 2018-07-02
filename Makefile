AWS=/usr/local/bin/aws
JQ=/usr/local/bin/jq
PROFILE=devday
STACK_NAME=cfn-basic-ec2-public

template: ec2_instance.yml

ec2_instance.yml: ec2_instance.py
	python ec2_instance.py | tee ec2_instance.yml

lint: ec2_instance.py
	pylint ec2_instance.py

clean:
	rm ec2_instance.yml

stack: template
	$(AWS) --profile=$(PROFILE) cloudformation create-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://ec2_instance.yml \
		--parameters ParameterKey=KeyName,ParameterValue=mjenkins.key
	 $(AWS) --profile=$(PROFILE) cloudformation wait stack-create-complete --stack-name $(STACK_NAME)
	 $(AWS) --profile=$(PROFILE) cloudformation describe-stacks --stack-name cfn-basic-ec2-public | $(JQ) .Stacks[0].Outputs

delete-stack:
	$(AWS) --profile=$(PROFILE) cloudformation delete-stack \
		--stack-name $(STACK_NAME)

.PHONY: clean stack template delete-stack lint
