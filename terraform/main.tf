terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.6.0"
    }
  }
}

provider "docker" {
}

resource "docker_image" "server" {
  name = "server:tf"
  triggers = {
    dockerfile = filesha256("${path.module}/Dockerfile")
  }
  build {
    context = "."
    build_args = {
      SSH_PUB_KEY = trimspace(file(pathexpand(var.ssh_public_key)))
    }
  }
}

resource "docker_container" "server" {
  name          = var.server_name
  image         = docker_image.server.image_id
  privileged    = true
  cgroupns_mode = "host"
  restart       = "unless-stopped"

  networks_advanced {
    name = "bridge"
  }
  # использовать с docker, иначе падает
  # networks_advanced {
  #  name    = "compose_monitoring"
  #  aliases = ["server"]
  #}

  ports {
    internal = 22
    external = var.ssh_port
    ip       = "127.0.0.1"
  }
  volumes {
    host_path      = "/sys/fs/cgroup/"
    container_path = "/sys/fs/"
    read_only      = false
  }
  tmpfs = { "/run" = "", "/run/lock" = "", "/tmp" = "" }
}
