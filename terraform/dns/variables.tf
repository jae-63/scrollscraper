variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
  default     = "default"
}

variable "ec2_ip" {
  description = "EC2 public IP — update this when migrating to ALB/Fargate"
  type        = string
  default     = "54.145.225.210"
}
