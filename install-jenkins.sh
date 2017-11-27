#!/bin/bash

# Install docker, nginx, git
apt-get install -y docker.io nginx git

# Install jenkins
wget -q -O - https://pkg.jenkins.io/debian/jenkins-ci.org.key | sudo apt-key add -
sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
apt-get update -y
apt-get install -y jenkins

# Add jenkins user to docker group
gpasswd -a jenkins docker


# Configure nginx as proxy for jenkins
rm /etc/nginx/sites-available/default
cat > /etc/nginx/sites-available/jenkins <<EOL
upstream app_server {
    server 127.0.0.1:8080 fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80 default ipv6only=on;
    server_name ci.yourcompany.com;

    location / {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$http_host;
        proxy_redirect off;

        if (!-f \$request_filename) {
            proxy_pass http://app_server;
            break;
        }
    }
}
EOL
ln -s /etc/nginx/sites-available/jenkins /etc/nginx/sites-enabled/

# (re)start the services
service docker restart
service jenkins restart
service nginx restart



# Install pip
apt-get install -y python-pip python-dev build-essential
# Fix for pip
export LC_ALL=C


# Install aws cli
pip install awscli --upgrade

mkdir app
chown jenkins: app