# Ollama Model S3 Export - Manual Process

Since the Ollama model is stored in a Docker volume and the EC2 instance has limited disk space (30GB), you need to use a streaming approach to export the model to S3.

## Prerequisites

- EC2 instance running with Ollama container
- Model already downloaded in Ollama (`llama3.2-vision`)
- S3 bucket created: `ttb-verifier-ollama-models-253490750467`
- IAM permissions configured for EC2 to write to S3

## Option 1: Export Using AWS CLI from Your Local Machine

If you have the AWS CLI and SSM plugin installed locally:

```bash
# 1. Get the S3 bucket name
S3_BUCKET=$(cd infrastructure && terragrunt output -raw ollama_models_bucket)

# 2. Connect to EC2 via SSM
aws ssm start-session --target i-00b92bc2cf4161b27

# 3. Once connected, run these commands:
sudo -i
docker run --rm \
  --volumes-from ttb-ollama \
  -v $(pwd):/backup \
  alpine:latest \
  tar czf /backup/model.tar.gz -C /root/.ollama models

# 4. Upload to S3 (this may take 5-10 minutes)
aws s3 cp /backup/model.tar.gz s3://ttb-verifier-ollama-models-253490750467/models/llama3.2-vision.tar.gz

# 5. Clean up
rm /backup/model.tar.gz

# 6. Verify
aws s3 ls --human-readable s3://ttb-verifier-ollama-models-253490750467/models/
```

## Option 2: Direct Streaming (Requires More Memory)

```bash
aws ssm start-session --target i-00b92bc2cf4161b27

# Once connected:
sudo -i
docker run --rm \
  --volumes-from ttb-ollama \
  alpine:latest \
  tar cz -C /root/.ollama models | \
  aws s3 cp - s3://ttb-verifier-ollama-models-253490750467/models/llama3.2-vision.tar.gz
```

## Option 3: Use EBS Volume (Recommended for Production)

For a more robust solution, consider attaching a separate EBS volume:

1. Create a 20GB EBS volume
2. Mount it to `/mnt/models`
3. Export model there
4. Upload to S3
5. Keep volume for future exports

## Verification

After upload, verify the model is in S3:

```bash
aws s3 ls --human-readable --recursive s3://ttb-verifier-ollama-models-253490750467/models/

# You should see something like:
# 2026-02-17 11:30:00  3.2 GiB models/llama3.2-vision.tar.gz
```

## Testing the S3 Download

After the model is in S3, test that new EC2 instances can download it:

```bash
# Destroy and recreate instance
cd infrastructure
terragrunt destroy -target=aws_instance.ttb -auto-approve
terragrunt apply -target=aws_instance.ttb -auto-approve

# Monitor initialization logs
aws ssm start-session --target $(terragrunt output -raw ec2_instance_id)
sudo tail -f /var/log/cloud-init-output.log
```

You should see:
```
Found model in S3, downloading...
Model restored from S3 successfully
```

Instead of:
```
Model not found in S3, falling back to ollama pull...
This will take 5-15 minutes...
```

## Current Status

**Model NOT yet exported to S3**

The infrastructure is ready, but the model hasn't been successfully exported yet due to disk space constraints on the EC2 instance. The init script will fall back to `ollama pull` for now (15-25 min RTO).

To achieve the improved RTO (8-12 min), you need to complete the manual export process above.

## Alternative: Increase EC2 Root Volume

If you prefer an automated solution, you can increase the root volume size in `infrastructure/instance.tf`:

```hcl
  root_block_device {
    volume_size = 50  # Increase from 30 to 50 GB
    volume_type = "gp3"
  }
```

Then recreate the instance and the export script should work automatically.
