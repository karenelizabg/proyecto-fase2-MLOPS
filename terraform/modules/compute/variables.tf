variable "environment" {
  description = "Nombre del entorno."
  type        = string
}

variable "ami_id" {
  description = "AMI utilizada por la instancia."
  type        = string
}

variable "instance_type" {
  description = "Tipo de instancia EC2."
  type        = string
}

variable "subnet_id" {
  description = "Subnet donde se desplegará la instancia."
  type        = string
}
