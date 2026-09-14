output "vpc_id" {
  description = "ID de la VPC."
  value       = aws_vpc.this.id
}

output "public_subnet_id" {
  description = "ID de la subnet pública."
  value       = aws_subnet.public.id
}
