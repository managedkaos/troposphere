AWS=/usr/local/bin/aws
JQ=/usr/local/bin/jq
PROFILE=devday
STACK_NAME=cfn-basic-ec2-public

ec2_instance.yml: ec2_instance.py
	python ec2_instance.py | tee ec2_instance.yml

lint: ec2_instance.py
	pylint ec2_instance.py

clean:
	rm ec2_instance.yml

stack: ec2_instance.yml
	$(AWS) --profile=$(PROFILE) cloudformation create-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://ec2_instance.yml \
		--parameters ParameterKey=KeyName,ParameterValue=mjenkins.key
	 $(AWS) --profile=$(PROFILE) cloudformation wait stack-create-complete \
		 --stack-name $(STACK_NAME)
	 $(AWS) --profile=$(PROFILE) cloudformation describe-stacks \
		 --stack-name $(STACK_NAME) | $(JQ) .Stacks[0].Outputs

describe-stack:
	 $(AWS) --profile=$(PROFILE) cloudformation describe-stacks \
		 --stack-name $(STACK_NAME) | $(JQ) .Stacks[0].Outputs

delete-stack:
	$(AWS) --profile=$(PROFILE) cloudformation delete-stack \
		--stack-name $(STACK_NAME)
	$(AWS) --profile=$(PROFILE) cloudformation wait stack-delete-complete \
		--stack-name $(STACK_NAME)

.PHONY: lint clean stack describe-stack delete-stack
