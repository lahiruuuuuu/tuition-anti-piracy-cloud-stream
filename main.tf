# 1. Point Terraform to your local machine instead of real AWS
provider "aws" {
  access_key                  = "mock"
  secret_key                  = "mock"
  region                      = "ap-south-1" # Colombo/Mumbai region code
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3     = "http://localhost:4566"
    iam    = "http://localhost:4566"
    lambda = "http://localhost:4566" # Added this so Lambda directs locally
  }
}

# 2. Build the Locked Video Vault Container
resource "aws_s3_bucket" "video_vault" {
  bucket = "tuition-premium-videos-local"
}

# 3. Block all direct public internet links from stealing files
resource "aws_s3_bucket_public_access_block" "block_piracy" {
  bucket = aws_s3_bucket.video_vault.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 4. Zip up the Python security code automatically
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/auth_stream.py"
  output_path = "${path.module}/auth_stream.zip"
}

# 5. Create an IAM Role for the Lambda function inside our mock environment
resource "aws_iam_role" "lambda_role" {
  name = "tuition_lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" } # Fixed the missing lambda string here!
    }]
  })
}

# 6. Deploy the Guard Function to LocalStack
resource "aws_lambda_function" "stream_authorizer" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "student_stream_authorizer"
  role             = aws_iam_role.lambda_role.arn
  handler          = "auth_stream.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}


