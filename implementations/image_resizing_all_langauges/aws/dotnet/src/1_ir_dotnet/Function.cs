using Amazon.Lambda.Core;
using Amazon.S3;
using Amazon.S3.Model;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Processing;
using System.IO;
using System.Threading.Tasks;
using Newtonsoft.Json;


// Assembly attribute to enable the Lambda function's JSON input to be converted into a .NET class.
[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace _1_ir_dotnet;

public class Function
{
    private readonly AmazonS3Client _s3Client = new AmazonS3Client();

    public async Task FunctionHandler(S3Information s3Details, ILambdaContext context)
    {
        var watch = new System.Diagnostics.Stopwatch();
        // Get bucket name and key from the input event
        string bucketName = s3Details.s3Bucket;
        string keyName = s3Details.s3Key;

        // Get the image object from S3
        using var response = await _s3Client.GetObjectAsync(bucketName, keyName);
        using var originalImageStream = response.ResponseStream;

        watch.Start();

        // Create an image object using ImageSharp
        var image = Image.Load(originalImageStream);

        // Resize the image maintaining aspect ratio
        image.Mutate(x => x.Resize(new ResizeOptions
        {
            Size = new Size(100, 0), // Set width to 100 and height to 0 to maintain aspect ratio
            Mode = ResizeMode.Max
        }));

        // Write the image back to S3 under a new key
        var newKeyName = "resized/dotnet_" + keyName;
        using var memoryStream = new MemoryStream();
        image.SaveAsJpeg(memoryStream);
        memoryStream.Position = 0;

        watch.Stop();
        var requestId = context.AwsRequestId.ToString();
        var mb = context.MemoryLimitInMB;
        var ms = watch.ElapsedMilliseconds;

        LogData logData = new LogData(requestId, keyName, ms, mb);
        LambdaLogger.Log(JsonConvert.SerializeObject(logData));


        var putRequest = new PutObjectRequest
        {
            BucketName = bucketName,
            Key = newKeyName,
            InputStream = memoryStream
        };

        await _s3Client.PutObjectAsync(putRequest);
    }
}

public class S3Information
{
    public string s3Bucket { get; set; }
    public string s3Key { get; set; }
}

public class LogData
{
    public string RequestId { get; set; }
    public string KeyName { get; set; }
    public double ImageTime { get; set; }
    public int Memory { get; set; }
    public string Language { get; set; } = "dotnet";

    public LogData(string reqId, string key, double duration, int memory)
    {
        RequestId = reqId;
        KeyName = key;
        ImageTime = duration;
        Memory = memory;
    }

}
