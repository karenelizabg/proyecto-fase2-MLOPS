variable "aws_region" {
  description = "Región de AWS donde se administrarán los recursos."
  type        = string
  default     = "us-east-1"
}

variable "github_repository" {
  description = "Repositorio de GitHub autorizado para asumir el IAM Role."
  type        = string
  default     = "karenelizabg/proyecto-fase2-MLOPS"
}

variable "github_actions_role_name" {
  description = "Nombre del IAM Role utilizado por GitHub Actions."
  type        = string
  default     = "GitHubActionsTerraformRole"
}
