terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source = "../modules/network"

  environment        = "prod"
  vpc_cidr           = "10.20.0.0/16"
  public_subnet_cidr = "10.20.1.0/24"
  availability_zone  = var.availability_zone
}

module "compute" {
  source = "../modules/compute"

  environment   = "prod"
  ami_id        = var.ami_id
  instance_type = "t3.small"
  subnet_id     = module.network.public_subnet_id
}

module "data" {
  source = "../modules/data"

  environment       = "prod"
  instance_class    = "db.t3.small"
  allocated_storage = 30
  db_name           = "image_repo"
  db_username       = var.db_username
  db_password       = var.db_password
}

module "storage" {
  source = "../modules/storage"

  environment = "prod"
  bucket_name = var.bucket_name
}
