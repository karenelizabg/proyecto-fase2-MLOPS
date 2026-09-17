output "bucket_name" {
  value = aws_s3_bucket.this.id
}

output "dvc_bucket_names" {
  value = { for purpose, bucket in aws_s3_bucket.dvc : purpose => bucket.id }
}
