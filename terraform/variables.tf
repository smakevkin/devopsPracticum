variable "server_name" {
  type    = string
  default = "server"
}

variable "ssh_port" {
  type    = number
  default = 2222
}

variable "ssh_public_key" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}