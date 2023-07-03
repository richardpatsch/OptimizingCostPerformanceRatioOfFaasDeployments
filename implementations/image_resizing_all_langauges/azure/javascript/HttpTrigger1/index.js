const { BlobServiceClient } = require('@azure/storage-blob')
const sharp = require('sharp')

var first_start = true

module.exports = async function (context, req) {
  const cold_start = first_start
  first_start = false

  const containerName = req.body.containerName
  const blobName = req.body.blobName
  const connectionString = req.body.connectionString

  context.log(containerName, blobName)

  const blobServiceClient =
    BlobServiceClient.fromConnectionString(connectionString)
  const containerClient = blobServiceClient.getContainerClient(containerName)
  const blockBlobClient = containerClient.getBlockBlobClient(blobName)

  const downloadBlockBlobResponse = await blockBlobClient.download(0)
  const blobBuffer = await streamToBuffer(
    downloadBlockBlobResponse.readableStreamBody
  )

  let start = Date.now()

  const img = sharp(blobBuffer)
  const resizedImageBuffer = await img.resize({ width: 100 }).toBuffer()

  let timeTaken = Date.now() - start
  const infoJson = {
    KeyName: blobName,
    Memory: 0,
    ImageTime: timeTaken,
    Language: 'javascript',
    RequestId: context.invocationId,
    ColdStart: cold_start,
  }

  context.log(JSON.stringify(infoJson))

  const newBlobName = 'resized/javascript_' + blobName
  const uploadBlobResponse = await containerClient
    .getBlockBlobClient(newBlobName)
    .upload(resizedImageBuffer, resizedImageBuffer.length)

  var a = {
    status: 200,
    message: 'Image resized and uploaded successfully!',
    cold_start: cold_start,
  }

  context.res.body = JSON.stringify(a)
}

async function streamToBuffer(readableStream) {
  return new Promise((resolve, reject) => {
    const chunks = []
    readableStream.on('data', (data) => {
      chunks.push(data instanceof Buffer ? data : Buffer.from(data))
    })
    readableStream.on('end', () => {
      resolve(Buffer.concat(chunks))
    })
    readableStream.on('error', reject)
  })
}
