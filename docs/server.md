In order to upload builds and collect statistics we run CentOS server.

## Create new user
First a new local user must be created on ottbld02:
~~~
sudo adduser electron
sudo passwd electron
sudo gpasswd -a electron wheel
su - electron
~~~


## Install InfluxDB 
Add yum repo
~~~
cat <<EOF | sudo tee /etc/yum.repos.d/influxdb.repo
[influxdb]
name = InfluxDB Repository - RHEL \$releasever
baseurl = https://repos.influxdata.com/rhel/\$releasever/\$basearch/stable
enabled = 1
gpgcheck = 1
gpgkey = https://repos.influxdata.com/influxdb.key
EOF
~~~
Install it and start service:
~~~
sudo yum install influxdb
sudo systemctl start influxdb
~~~

Set path to [influxdb.conf](../server/configs/influx/influxdb.conf) by modifying service:
~~~
sudo systemctl edit influxdb
~~~

and paste following snippet and press Ctrl+O to save, press Enter to confirm file name and Ctrl+X to exit
~~~
[Service]
Environment=INFLUXDB_CONFIG_PATH=/home/electron/influxdb/influxdb.conf
~~~

then we need to restart service:
~~~
sudo systemctl daemon-reload
sudo systemctl restart influxdb
~~~

Enable start on boot:
~~~
sudo systemctl enable influxdb
~~~

## Install Grafana 
Add yum repo
~~~
cat <<EOF | sudo tee /etc/yum.repos.d/grafana.repo
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF
~~~

Install it and start service:
~~~
sudo yum install grafana
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl status grafana-server
~~~

Enable start on boot:
~~~
sudo systemctl enable grafana-server
~~~

Dashboards could be initialized from JSON file under server/configs/grafana/dashboards

> Note: grafana configurations are saved under `/var/lib/grafana` and `/etc/grafana`
> you can copy these files for backup and restore after, change owner after copy:
> ~~~
> sudo chown -R grafana:grafana /var/lib/grafana
> sudo chown -R grafana:grafana /etc/grafana
> ~~~


## Install Python 3.7.9
~~~
cd /usr/src
sudo yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel
sudo wget https://www.python.org/ftp/python/3.7.9/Python-3.7.9.tgz
sudo tar xzf Python-3.7.9.tgz
cd Python-3.7.9
sudo yum install -y xz-devel
sudo ./configure --enable-optimizations
sudo make altinstall
sudo rm /usr/src/Python-3.7.9.tgz
python3.7 -V
~~~

## Install git
~~~
sudo yum install git
~~~

### Server Side for SP
We need to provide regular builds to SP. This is done via running _cron_ on CentOS machine. 
Cron runs [sharepoint_uploader.py](../server/sharepoint_uploader.py) multiple times per day and python code gets new 
builds from Artifactory, uploads them SP and adds information about new build to SP List.

Secret keys configuration you can find in  [Upload To SharePoint](upload_to_SharePoint.md)

To connect to SP system needs to know SP _client_id_ and _client_secret_. They are provided through environment 
variables. Also for successful download TEMP variable is required. These variables are set through 
_/home/electron/.bashrc_

Login as _electron_ user. Install cron and start it as service:
~~~
sudo yum install cronie
service crond start
chkconfig crond on
~~~

Configure cron to run every 3 hours:
~~~
crontab -l > .cron_settings
vim .cron_settings
~~~

In vim editor write:
~~~
0 */1 * * * . $HOME/.bash_profile; python3.7 /home/electron/git/beta_downloader/server/sharepoint_uploader.py
0 */1 * * * . $HOME/.bash_profile; python3.7 /home/electron/git/beta_downloader/server/transfer_statistics.py
35 7 * * SUN . $HOME/.bash_profile; cd /home/electron/git/beta_downloader &&  /usr/local/bin/python3.7 ./server/sharepoint_cleaner.py
~~~

Now activate cron to take this settings
~~~
crontab .cron_settings
~~~

To see emails from cron if something goes wrong:
~~~
vim /var/spool/mail/electron
~~~