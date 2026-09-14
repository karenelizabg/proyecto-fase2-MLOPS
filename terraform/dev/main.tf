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

  environment         = "dev"
  vpc_cidr            = "10.10.0.0/16"
  public_subnet_cidr  = "10.10.1.0/24"
  availability_zone   = var.availability_zone
}

module "compute" {
  source = "../modules/compute"

  environment   = "dev"
  ami_id        = var.ami_id
  instance_type = "t3.micro"
  subnet_id     = module.network.public_subnet_id
}

module "data" {
  source = "../modules/data"

  environment       = "dev"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "image_repo"
  db_username       = var.db_username
  db_password       = var.db_password
}

module "storage" {
  source = "../modules/storage"

  environment = "dev"
  bucket_name = var.bucket_name
}
