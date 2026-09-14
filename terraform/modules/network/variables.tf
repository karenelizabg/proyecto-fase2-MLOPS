variable "environment" {
  description = "Nombre del entorno."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR de la VPC."
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR de la subnet pública."
  type        = string
}

variable "availability_zone" {
  description = "Zona de disponibilidad."
  type        = string
}
