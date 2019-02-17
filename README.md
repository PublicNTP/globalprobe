[![license](https://img.shields.io/github/license/mashape/apistatus.svg)]()
# GlobalProbe
Project GlobalProbe is an NTP server monitoring platform

## Installation

### Terraform

[Install Terraform](https://learn.hashicorp.com/terraform/getting-started/install.html)

### AWS permissions

Cheated and did host role with unlimited.

### Build AWS resources

Run TF script for AWS


### Make sure we can talk to the RDS instance

It defaulted to a security group that won't let the world talk to it



### Cognito JS library (actually already in JS package, but noting how to get new one)

sudo apt-get -y install npm
mkdir -p ~/tmp/cognito
cd ~/tmp/cognito
npm install amazon-cognito-identity-js package
cp node_modules/amazon-cognito-identity-js/dist/amazon-cognito-identity.min.js .../src/js/



### Serverless

```bash
$ npm install -g serverless
```

### Install Docker

https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04


### Deploy API Lambda

```bash
$ cd ~
$ serverless create --template aws-python3 --name globalprobe-api --path ./api
$ cd api
$ sudo apt-get -y install virtualenv
$ virtualenv venv --python=python3
$ source venv/bin/activate

$ serverless deploy
```

Update these for the neat docker packaging


### Test API

```bash
$ curl -d "@/home/ubuntu/tmp/add_server.json" -X POST https://25zwa0yf5h.execute-api.us-east-2.amazonaws.com/dev/v1/server/add
```



## Legal
`globalprobe` is copyrighted by [PublicNTP, Inc.](https://publicntp.org),
open-sourced under the [MIT License](https://en.wikipedia.org/wiki/MIT_License).

Refer to
[LICENSE](https://github.com/PublicNTP/globalprobe/blob/master/LICENSE)
for more information.
