STACK_NAME=cfn-basic-ec2-public

template: ec2_instance.yml

ec2_instance.yml: ec2_instance.py
	python ec2_instance.py | tee ec2_instance.yml

lint: ec2_instance.py
	pylint ec2_instance.py

clean:
	rm ec2_instance.yml

stack: template
	aws --profile=devday cloudformation create-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://ec2_instance.yml \
		--parameters ParameterKey=KeyName,ParameterValue=mjenkins.key

delete-stack:
	aws --profile=devday cloudformation delete-stack \
		--stack-name $(STACK_NAME)

.PHONY: clean stack template delete-stack lint
