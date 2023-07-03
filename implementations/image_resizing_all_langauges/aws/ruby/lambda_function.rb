require 'json'
require 'aws-sdk-s3'
require 'mini_magick'

def lambda_handler(event:, context:)
  # Create a new S3 resource
  s3 = Aws::S3::Resource.new(region: 'eu-central-1')

  # Get bucket name and key from the input event
  bucket_name = event['s3Bucket']
  key_name = event['s3Key']

  # Get the image object
  object = s3.bucket(bucket_name).object(key_name)

  starting = Process.clock_gettime(Process::CLOCK_MONOTONIC)

  # Read the object (image) data
  image_data = object.get.body.read

  # Create an image object using MiniMagick
  img = MiniMagick::Image.read(image_data)

  # Calculate new height to maintain aspect ratio
  base_width = 100
  img.resize "#{base_width}x"
  ending = Process.clock_gettime(Process::CLOCK_MONOTONIC)
  elapsed = (ending - starting) * 1000 # to get ms
  # puts elapsed
  json_log = '{"KeyName": "' + key_name + '", "Memory": ' +context.memory_limit_in_mb + ', "ImageTime": ' + elapsed.to_s + ', "Language": "ruby", "RequestId": "'+context.aws_request_id+'"}'
  puts json_log
  # puts "Ruby resized: " + key_name + " with " + context.memory_limit_in_mb + " MB, in " + elapsed.to_s + " seconds."

  # Write the image back to S3 under a new key
  new_key_name = 'resized/ruby_' + key_name
  s3.bucket(bucket_name).object(new_key_name).put(body: img.to_blob)

  { statusCode: 200, body: JSON.generate('Image resized and uploaded successfully!') }
end

