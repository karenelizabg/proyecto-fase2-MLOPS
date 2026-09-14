output "db_endpoint" {
  description = "Endpoint de la base de datos."
  value       = aws_db_instance.this.endpoint
}

output "db_name" {
  description = "Nombre de la base de datos."
  value       = aws_db_instance.this.db_name
}
