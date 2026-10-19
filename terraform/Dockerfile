FROM ubuntu:24.04

RUN apt update \ 
    && apt install --no-install-recommends -y openssh-server systemd python3 sudo iproute2 systemd-sysv \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash --uid 1001 user \
    && usermod -p '*' user \
    && echo 'user ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/user \
    && chmod 440 /etc/sudoers.d/user

RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config

ARG SSH_PUB_KEY

USER user

RUN mkdir -p ~/.ssh/ \
    && chmod 700 ~/.ssh \
    && touch ~/.ssh/authorized_keys \
    && chmod 600 ~/.ssh/authorized_keys \
    && printf '%s\n' "$SSH_PUB_KEY" > /home/user/.ssh/authorized_keys

USER root

RUN systemctl enable ssh

EXPOSE 22

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]