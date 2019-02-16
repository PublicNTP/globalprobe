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

# Cognito Identity Pool
resource "aws_cognito_identity_pool" "globalprobe_identity_pool" {
    identity_pool_name                  = "globalprobe_identity_pool"
    allow_unauthenticated_identities    = false
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
