// import individual service
import {
  GetObjectCommand,
  PutObjectCommand,
  S3Client,
} from '@aws-sdk/client-s3'
import { info, time } from 'console'
import sharp from 'sharp'

const client = new S3Client({})

export const handler = async (event, context) => {
  const bucketName = event.s3Bucket
  const keyName = event.s3Key

  console.log(bucketName, keyName)

  const buffer = Buffer.concat(
    await (
      await client.send(
        new GetObjectCommand({
          Key: keyName,
          Bucket: bucketName,
        })
      )
    ).Body.toArray()
  )

  let start = Date.now()

  // Create an image object using sharp
  const img = sharp(buffer)

  // Resize the image
  const resizedImage = await img.resize({ width: 100 }).toBuffer()

  let timeTaken = Date.now() - start
  //let timeInSeconds = timeTaken / 1000
  let mb = context.memoryLimitInMB

  const infoJson = {
    KeyName: keyName,
    Memory: Number(mb),
    ImageTime: timeTaken,
    Language: 'javascript',
    RequestId: context.awsRequestId,
  }

  console.log(infoJson)

  // Write the image back to S3 under a new key
  const newKeyName = 'resized/javascript_' + keyName

  const putCommand = new PutObjectCommand({
    Bucket: bucketName,
    Key: newKeyName,
    Body: resizedImage,
  })

  const response = await client.send(putCommand)

  return {
    statusCode: 200,
    body: JSON.stringify('Image resized and uploaded successfully!'),
  }
}
