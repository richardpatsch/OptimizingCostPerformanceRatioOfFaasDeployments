dir=`pwd`
bundle config set --local deployment 'true'
docker run --platform=linux/amd64 \
  -e BUNDLE_SILENCE_ROOT_WARNING=1 \
  -v `pwd`:`pwd` \
  -w `pwd` \
  amazon/aws-sam-cli-build-image-ruby2.7 bundle install
bundle config unset deployment
bundle config unset path