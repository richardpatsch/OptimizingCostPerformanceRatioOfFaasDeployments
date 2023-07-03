package example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import software.amazon.awssdk.awscore.exception.AwsServiceException;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.S3Client;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import org.imgscalr.Scalr;

import java.time.Duration;
import java.time.Instant;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import javax.imageio.ImageIO;
import java.text.ParseException;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;


// Handler value: example.Handler
public class Main implements RequestHandler<Map<String,String>, String>{
    //private static final Logger logger = LoggerFactory.getLogger(Main.class);
    private static final float MAX_DIMENSION = 100;
    private final String REGEX = ".*\\.([^\\.]*)";
    private final String JPG_TYPE = "jpg";
    private final String JPEG_TYPE = "jpeg";
    private final String JPG_MIME = "image/jpeg";
    private final String PNG_TYPE = "png";
    private final String PNG_MIME = "image/png";


    @Override
    public String handleRequest(Map<String,String> event, Context context)  {
        LambdaLogger logger = context.getLogger();

        try {
            String bucketName = event.get("s3Bucket");
            String keyName = event.get("s3Key");

            // Infer the image type.
            Matcher matcher = Pattern.compile(REGEX).matcher(keyName);
            if (!matcher.matches()) {
                logger.log("Unable to infer image type for key " + keyName);
                return "Unable to infer image type for key ";
            }
            String imageType = matcher.group(1);
            if (!(JPG_TYPE.equals(imageType)) && !(PNG_TYPE.equals(imageType)) && !(JPEG_TYPE.equals(imageType))) {
                logger.log("Skipping non-image " + keyName);
                return "Skipping non-image";
            }

            // Download the image from S3 into a stream
            S3Client s3Client = S3Client.builder().build();
            InputStream s3Object = getObject(s3Client, bucketName, keyName);

            Instant start = Instant.now();


            BufferedImage img = ImageIO.read(s3Object);

            // Resize the image
            int new_width = 100;
            BufferedImage resizedImage = Scalr.resize(img, Scalr.Method.ULTRA_QUALITY, Scalr.Mode.FIT_TO_WIDTH,
                    new_width, Scalr.OP_ANTIALIAS);

            // Convert the resized image to an input stream
            ByteArrayOutputStream os = new ByteArrayOutputStream();
            ImageIO.write(resizedImage, imageType, os);

            Instant finish = Instant.now();
            long timeElapsed = Duration.between(start, finish).toMillis();  //in seconds

            // Create a JSON object
            JSONObject jsonObject = new JSONObject();
            jsonObject.put("KeyName", keyName);
            jsonObject.put("Memory", context.getMemoryLimitInMB());
            jsonObject.put("ImageTime", timeElapsed);
            jsonObject.put("Language", "java");
            jsonObject.put("RequestId", context.getAwsRequestId());

            // Print the JSON object
            logger.log(jsonObject.toString());
            // logger.log("java resizing for " + keyName + " with " + context.getMemoryLimitInMB() + " took " + timeElapsed);

            String newKey = "resized/java_" + keyName;
            putObject(s3Client, os, bucketName, newKey, imageType);


            // logger.log("Successfully resized " + bucketName + "/"
            //        + keyName + " and uploaded to " + bucketName + "/" + newKey);
            return "Ok";
        } catch (Exception e) {
            return "failed";
        }
    }

    private InputStream getObject(S3Client s3Client, String bucket, String key) {
        GetObjectRequest getObjectRequest = GetObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .build();
        return s3Client.getObject(getObjectRequest);
    }

    private void putObject(S3Client s3Client, ByteArrayOutputStream outputStream,
                           String bucket, String key, String imageType) {
        Map<String, String> metadata = new HashMap<>();
        metadata.put("Content-Length", Integer.toString(outputStream.size()));
        if (JPG_TYPE.equals(imageType) || JPEG_TYPE.equals(imageType)) {
            metadata.put("Content-Type", JPG_MIME);
        } else if (PNG_TYPE.equals(imageType)) {
            metadata.put("Content-Type", PNG_MIME);
        }

        PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .metadata(metadata)
                .build();

        // Uploading to S3 destination bucket
        //logger.info("Writing to: " + bucket + "/" + key);
        try {
            s3Client.putObject(putObjectRequest,
                    RequestBody.fromBytes(outputStream.toByteArray()));
        }
        catch(AwsServiceException e)
        {
            //logger.error(e.awsErrorDetails().errorMessage());
            System.exit(1);
        }
    }
}