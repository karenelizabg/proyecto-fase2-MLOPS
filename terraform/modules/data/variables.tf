variable "environment" {
  description = "Nombre del entorno."
  type        = string
}

variable "instance_class" {
  description = "Clase de instancia de la base de datos."
  type        = string
}

variable "allocated_storage" {
  description = "Almacenamiento asignado en GB."
  type        = number
}

variable "db_name" {
  description = "Nombre de la base de datos."
  type        = string
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
