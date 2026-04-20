# playnext_infra/variables.tf

variable "db_username" {
  description = "Username for RDS Database"
  type        = string
  default     = "playnext_admin"
}

variable "db_password" {
  description = "Password for RDS Database"
  type        = string
  sensitive   = true
}