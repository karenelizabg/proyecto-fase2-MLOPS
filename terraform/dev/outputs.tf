output "vpc_id" {
  value = module.network.vpc_id
}

output "instance_id" {
  value = module.compute.instance_id
}

output "database_endpoint" {
  value = module.data.db_endpoint
}

output "bucket_name" {
  value = module.storage.bucket_id
}
