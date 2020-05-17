export AWS_PROFILE=akhil
aws s3 cp ./web/videoapp.js s3://me.akhil.webrtc.aws.html
aws s3 cp ./web/index.html s3://me.akhil.webrtc.aws.html
aws cloudfront create-invalidation --distribution-id E1TWNDZ56BI5BN --paths "/*"
