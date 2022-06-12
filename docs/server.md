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
