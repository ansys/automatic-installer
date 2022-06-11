In order to upload builds and collect statistics we run CentOS server.

## Create new user
First a new local user must be created on ottbld02:
~~~
sudo adduser electron
sudo passwd electron
sudo gpasswd -a electron wheel
su - electron
~~~


## Install git
~~~
sudo yum install git
~~~

### Server Side for SP
We need to provide regular builds to SP. This is done via running _cron_ on CentOS machine. 
Cron runs [sharepoint_uploader.py](../docker/sharepoint/code/sharepoint_uploader.py) multiple times per day and python code gets new 
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
