AWS=/usr/local/bin/aws
JQ=/usr/local/bin/jq
PROFILE=devday
STACK_NAME=jenkins_master
PASSWORD=C0mpl3x_Pa55w0rd
KEYNAME=mjenkins.key

$(STACK_NAME).yml: $(STACK_NAME).py
	python $< | tee $@

lint: $(STACK_NAME).py
	pylint $<

clean:
	@rm $(STACK_NAME).yml || echo "All clean! :D"

stack: $(STACK_NAME).yml
	@$(AWS) --profile=$(PROFILE) cloudformation create-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://$(STACK_NAME).yml \
		--parameters ParameterKey=KeyName,ParameterValue=$(KEYNAME) \
		             ParameterKey=PassWord,ParameterValue=$(PASSWORD)
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
