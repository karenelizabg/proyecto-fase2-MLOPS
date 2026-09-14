variable "aws_region" {
  description = "Región de AWS."
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Zona de disponibilidad para prod."
  type        = string
  default     = "us-east-1a"
}

variable "ami_id" {
  description = "AMI para la instancia EC2."
  type        = string
  default     = "ami-0c02fb55956c7d316"
}

variable "db_username" {
  description = "Usuario de la base de datos."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Contraseña de la base de datos."
  type        = string
  sensitive   = true
}

variable "bucket_name" {
  description = "Nombre del bucket de prod."
  type        = string
  default     = "proyecto-fase2-mlops-prod-storage"
}
