In order to upload builds and collect statistics we run Ubuntu server with docker.

## Create new user
First a new local user must be created on ottbld02:
~~~
sudo useradd -m -d /home_local/electron electron
sudo passwd electron
sudo usermod -aG sudo electron
su - electron
~~~


## Install git
~~~
sudo apt install git
~~~

## Install Docker
Instruction is taken from: https://docs.docker.com/engine/install/centos/
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

## Start Docker
First, set following environment variables for your user (electron user) 
  - client_id
  - client_secret

How to get values you can read in [upload_to_SharePoint.md](upload_to_SharePoint.md).

Second,
create folder "settings" in the same dir with [docker-compose.yml](../docker/docker-compose.yml) 
file and put there downloader config files.

Finally,
start docker services via
```bash
sudo -E docker-compose up -d
```
This will start docker compose, pass environment variables from current user and detach from docker.
