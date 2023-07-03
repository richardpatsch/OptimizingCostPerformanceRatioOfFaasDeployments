using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Processing;
using Azure.Storage.Blobs;


namespace Company.Function
{
    public class HttpTrigger1
    {
        public static bool first_run = true;

        [FunctionName("HttpTrigger1")]
        public static async Task<IActionResult> Run(
           [HttpTrigger(AuthorizationLevel.Function, "post", Route = null)] HttpRequest req,
           ExecutionContext context,
           ILogger log)
        {

            bool cold_start = first_run;
            first_run = false;

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            dynamic data = JsonConvert.DeserializeObject(requestBody);

            string connectionString = data?.connectionString;
            string containerName = data?.containerName;
            string blobName = data?.blobName;

            if (string.IsNullOrEmpty(connectionString) || string.IsNullOrEmpty(containerName) || string.IsNullOrEmpty(blobName))
            {
                return new BadRequestObjectResult("Please pass a valid 'connectionString', 'containerName' and 'blobName' in the request body");
            }

            // Get the blob
            var blobServiceClient = new BlobServiceClient(connectionString);
            var blobContainerClient = blobServiceClient.GetBlobContainerClient(containerName);
            var blobClient = blobContainerClient.GetBlobClient(blobName);

            using var memoryStream = new MemoryStream();
            await blobClient.DownloadToAsync(memoryStream);
            memoryStream.Position = 0;

            var watch = new System.Diagnostics.Stopwatch();
            watch.Start();

            // Create an image object using ImageSharp
            var image = Image.Load(memoryStream);

            // Resize the image maintaining aspect ratio
            image.Mutate(x => x.Resize(new ResizeOptions
            {
                Size = new Size(100, 0), // Set width to 100 and height to 0 to maintain aspect ratio
                Mode = ResizeMode.Max
            }));

            using var outputMemoryStream = new MemoryStream();
            image.SaveAsJpeg(outputMemoryStream);
            outputMemoryStream.Position = 0;
            watch.Stop();

            // Write the image back to Blob storage under a new blob
            var newBlobName = "resized/dotnet_" + blobName;
            BlobClient newBlobClient = blobContainerClient.GetBlobClient(newBlobName);

            await newBlobClient.UploadAsync(outputMemoryStream, overwrite: true);

            var ms = watch.ElapsedMilliseconds;

            LogData logData = new LogData(context.InvocationId.ToString(), blobName, ms, 0, cold_start);
            log.LogInformation(JsonConvert.SerializeObject(logData));

            var x = new
            {
                status_code = 200,
                message = $"Image resized and saved to: {newBlobName}",
                cold_start = cold_start
            };
            return new OkObjectResult(JsonConvert.SerializeObject(x));
        }
    }


    public class LogData
    {
        public string RequestId { get; set; }
        public string KeyName { get; set; }
        public double ImageTime { get; set; }
        public int Memory { get; set; }
        public string Language { get; set; } = "dotnet";
        public bool ColdStart { get; set; }

        public LogData(string reqId, string blobName, double duration, int memory, bool coldStart)
        {
            RequestId = reqId;
            KeyName = blobName;
            ImageTime = duration;
            Memory = memory;
            ColdStart = coldStart;
        }
    }
}
