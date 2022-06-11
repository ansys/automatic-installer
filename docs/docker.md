install docker data is taken from: https://docs.docker.com/engine/install/centos/
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

start and enable docker service
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

install docker-compose
```bash
sudo yum install -y docker-compose
```
