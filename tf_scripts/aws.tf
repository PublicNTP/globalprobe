variable "db_password" {}

provider "aws" {
    region = "us-east-2"
}

# Create Cognito assets

# Cognito User Pool
resource "aws_cognito_user_pool" "globalprobe_user_pool" {

    name = "GlobalProbe_Users"

    auto_verified_attributes = [ "email" ]

    username_attributes = [ "email" ]

    password_policy {
        minimum_length = 8
    }

    # We use "nickname" for their display name
}

# GlobalProbe Admins
resource "aws_cognito_user_group" "globalprobe_admin_user_group" {
    name = "GlobalProbe_Admins"

    user_pool_id = "${aws_cognito_user_pool.globalprobe_user_pool.id}"
}


# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "javascript_client" {
    name = "GlobalProbe_WebApp"

    user_pool_id    = "${aws_cognito_user_pool.globalprobe_user_pool.id}"
}


# S3 bucket for static web content
resource "aws_s3_bucket" "static_web_content" {
    bucket  = "globalprobe.dev.publicntp.org"
    acl     = "public-read"
    policy  = "${file("s3_static_hosting_policy.json")}"

    website {
        index_document = "index.html"
        error_document = "error.html"
    }
}


# Login page
resource "aws_s3_bucket_object" "index_page" {
    bucket          = "${aws_s3_bucket.static_web_content.id}"
    key             = "index.html"
    source          = "../src/html/index.html"
    content_type    = "text/html"
}

# Cognito JS
resource  "aws_s3_bucket_object" "cognito-js" {
    bucket          = "${aws_s3_bucket.static_web_content.id}"
    key             = "js/amazon-cognito-identity.min.js"
    source          = "../src/js/amazon-cognito-identity.min.js"
    content_type    = "text/javascript"
}

# Login JS
resource "aws_s3_bucket_object" "login-js" {
    bucket          = "${aws_s3_bucket.static_web_content.id}"
    key             = "js/login.js"
    source          = "../src/js/login.js"
    content_type    = "text/javascript"
}

# Dashboard page
resource "aws_s3_bucket_object" "dashboard_page" {
    bucket          = "${aws_s3_bucket.static_web_content.id}"
    key             = "dashboard.html"
    source          = "../src/html/dashboard.html"
    content_type    = "text/html"
}

# Dashboard JS
resource "aws_s3_bucket_object" "dashboard-js" {
    bucket          = "${aws_s3_bucket.static_web_content.id}"
    key             = "js/dashboard.js"
    source          = "../src/js/dashboard.js"
    content_type    = "text/javascript"
}

# RDS instance security group
resource "aws_security_group" "rds_security_group" {
    name            = "PostgreSQL"
    description     = "Allow network traffic from all hosts to PostgreSQL"
    
    ingress {
        protocol            = "tcp"
        cidr_blocks         = [ "0.0.0.0/0" ]
        ipv6_cidr_blocks    = [ "::/0" ]
        from_port           = 5432
        to_port             = 5432
    }

    egress {
        protocol            = -1
        from_port           = 0
        to_port             = 0
        cidr_blocks         = [ "0.0.0.0/0" ]
        ipv6_cidr_blocks    = [ "::/0" ] 
    }
}

# RDS (Postgresql) instance
resource "aws_db_instance" "globalprobe_db" {
    allocated_storage           = 20      # 20GB is the min for RDS
    storage_type                = "gp2"
    engine                      = "postgres"
    instance_class              = "db.t2.micro"
    identifier                  = "globalprobe"                 # instance name
    name                        = "globalprobe"                 # DB name
    username                    = "globalprobe_admin"
    password                    = "${var.db_password}"
    publicly_accessible         = true
    skip_final_snapshot         = true
    final_snapshot_identifier   = "booya"
    vpc_security_group_ids      = [ "${aws_security_group.rds_security_group.id}" ]
}
