
# Get Latest Ubuntu Image

```
aws ec2 describe-images \
 --filters Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64* \
 --query 'Images[*].[ImageId,CreationDate]' --output text \
 | sort -k2 -r \
 | head -n1
```

# User Data Script Location

`/var/lib/cloud/instance/scripts/part-001`
