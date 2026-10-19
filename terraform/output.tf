output "ssh_command" {
  value = "ssh -p ${var.ssh_port} -i ~/.ssh/id_e25519 user@localhost"
}
