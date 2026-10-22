#!/usr/bin/env bash
# Run once on a fresh Ubuntu 22.04/24.04 EC2 instance: bash setup-ec2.sh
set -euo pipefail

echo "==> Adding 2G swap (helps small instances)"
if ! swapon --show | grep -q swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "==> Installing Docker, Compose, Git, curl"
sudo apt-get update -y
sudo apt-get install -y docker.io docker-compose-v2 git curl fontconfig openjdk-17-jre
sudo systemctl enable --now docker

echo "==> Installing Jenkins (LTS)"
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y jenkins

echo "==> Letting Jenkins and the current user run Docker"
sudo usermod -aG docker jenkins
sudo usermod -aG docker "$USER"
sudo systemctl enable --now jenkins
sudo systemctl restart jenkins

echo
echo "Done. Open http://<EC2-PUBLIC-IP>:8080"
echo "Initial admin password:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
