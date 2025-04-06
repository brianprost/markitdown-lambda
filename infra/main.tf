variable "image_tag" {
  description = "The tag to use for the Docker image in ECR"
  type        = string
  default     = "latest"
}

locals {
  app_name = "markitdown-lambda"
}

module "lambda" {
  source     = "github.com/brianprost/terraform-aws-lambda-container"
  depends_on = [module.ecr]

  function_name = local.app_name
  image_uri     = "${module.ecr.repository_url}:${var.image_tag}"

  memory_size = 1024
  timeout     = 10
}

resource "aws_iam_role" "lambda_role" {
    name = "${local.app_name}-lambda-role"
    assume_role_policy = jsonencode({
        Version   = "2012-10-17",
        Statement = [{
            Action    = "sts:AssumeRole",
            Effect    = "Allow",
            Principal = {
                Service = "lambda.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
    role       = aws_iam_role.lambda_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_readonly" {
    role       = aws_iam_role.lambda_role.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

module "ecr" {
  source = "terraform-aws-modules/ecr/aws"

  repository_name = local.app_name

  repository_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "Keep last 30 images",
        selection = {
          tagStatus     = "tagged",
          tagPrefixList = ["v"],
          countType     = "imageCountMoreThan",
          countNumber   = 30
        },
        action = {
          type = "expire"
        }
      }
    ]
  })
}
