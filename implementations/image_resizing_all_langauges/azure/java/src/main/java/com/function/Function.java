package com.function;

import com.microsoft.azure.functions.ExecutionContext;
import com.microsoft.azure.functions.HttpMethod;
import com.microsoft.azure.functions.HttpRequestMessage;
import com.microsoft.azure.functions.HttpResponseMessage;
import com.microsoft.azure.functions.HttpStatus;
import com.microsoft.azure.functions.annotation.AuthorizationLevel;
import com.microsoft.azure.functions.annotation.FunctionName;
import com.microsoft.azure.functions.annotation.HttpTrigger;

import org.imgscalr.Scalr;
import com.azure.storage.blob.*;
import com.fasterxml.jackson.annotation.JsonBackReference;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.Instant;
import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.time.Duration;
import org.json.JSONObject;

/**
 * Azure Functions with HTTP Trigger.
 */
public class Function {

    private final String REGEX = ".*\\.([^\\.]*)";
    private final String JPG_TYPE = "jpg";
    private final String JPEG_TYPE = "jpeg";
    private final String PNG_TYPE = "png";

    public static Boolean first_run = true;

    /**
     * This function listens at endpoint "/api/HttpExample". Two ways to invoke it
     * using "curl" command in bash:
     * 1. curl -d "HTTP Body" {your host}/api/HttpExample
     * 2. curl "{your host}/api/HttpExample?name=HTTP%20Query"
     */
    @FunctionName("HttpExample")
    public HttpResponseMessage run(
            @HttpTrigger(name = "req", methods = {
                    HttpMethod.POST }, authLevel = AuthorizationLevel.FUNCTION) HttpRequestMessage<Optional<String>> request,
            final ExecutionContext context) {
        Boolean cold_start = first_run;
        first_run = false;

        context.getLogger().info("Java HTTP trigger processed a request.");

        // Parse JSON input
        String body = request.getBody().orElse("");
        JsonObject input = JsonParser.parseString(body).getAsJsonObject();
        String blobName = input.get("blobName").getAsString();
        String containerName = input.get("containerName").getAsString();
        String connectionString = input.get("connectionString").getAsString();

        // Infer the image type.
        Matcher matcher = Pattern.compile(REGEX).matcher(blobName);
        if (!matcher.matches()) {
            return request.createResponseBuilder(HttpStatus.BAD_REQUEST)
                    .body("Unable to infer image type for key " + blobName).build();
        }

        String imageType = matcher.group(1);
        if (!(JPG_TYPE.equals(imageType)) && !(PNG_TYPE.equals(imageType)) && !(JPEG_TYPE.equals(imageType))) {
            return request.createResponseBuilder(HttpStatus.BAD_REQUEST)
                    .body("Skipping non-image " + blobName).build();
        }

        try {
            BlobServiceClient blobServiceClient = new BlobServiceClientBuilder().connectionString(connectionString)
                    .buildClient();
            BlobContainerClient containerClient = blobServiceClient.getBlobContainerClient(containerName);
            BlobClient blobClient = containerClient.getBlobClient(blobName);

            InputStream blobStream = new ByteArrayInputStream(blobClient.downloadContent().toBytes());

            Instant start = Instant.now();

            BufferedImage img = ImageIO.read(blobStream);

            // Resize the image
            int new_width = 100;
            BufferedImage resizedImage = Scalr.resize(img, Scalr.Method.ULTRA_QUALITY, Scalr.Mode.FIT_TO_WIDTH,
                    new_width, Scalr.OP_ANTIALIAS);

            // Convert the resized image to an input stream
            ByteArrayOutputStream os = new ByteArrayOutputStream();
            ImageIO.write(resizedImage, imageType, os);
            InputStream resizedImageStream = new ByteArrayInputStream(os.toByteArray());

            Instant finish = Instant.now();
            long timeElapsed = Duration.between(start, finish).toMillis(); // in seconds

            context.getLogger().info("Image resize for " + blobName + " took " + timeElapsed + " milliseconds.");

            // Create a JSON object
            JSONObject jsonObject = new JSONObject();
            jsonObject.put("KeyName", blobName);
            jsonObject.put("Memory", 0);
            jsonObject.put("ImageTime", timeElapsed);
            jsonObject.put("Language", "java");
            jsonObject.put("RequestId", context.getInvocationId());
            jsonObject.put("ColdStart", cold_start);

            // Print the JSON object
            context.getLogger().info(jsonObject.toString());

            String newBlobName = "resized/java_" + blobName;
            uploadToBlob(resizedImageStream, newBlobName, containerClient, context);

            JSONObject jobj = new JSONObject();
            jobj.put("status", HttpStatus.OK);
            jobj.put("message", "Image resized successfully!");
            jobj.put("cold_start", cold_start);

            return request.createResponseBuilder(HttpStatus.OK).body(jobj.toString()).build();
        } catch (Exception e) {
            JSONObject jobj = new JSONObject();
            jobj.put("status", HttpStatus.INTERNAL_SERVER_ERROR);
            jobj.put("message", "Image resized failed!");
            jobj.put("cold_start", cold_start);

            context.getLogger().severe(e.getMessage());
            return request.createResponseBuilder(HttpStatus.INTERNAL_SERVER_ERROR).body(jobj.toString()).build();
        }
    }

    private void uploadToBlob(InputStream inputStream, String blobName, BlobContainerClient containerClient,
            ExecutionContext context) {
        try {
            BlobClient blobClient = containerClient.getBlobClient(blobName);
            blobClient.upload(inputStream, inputStream.available(), true);

            context.getLogger().info("Successfully resized and uploaded to blob with name " + blobName);
        } catch (Exception e) {
            context.getLogger().severe(e.getMessage());
        }
    }
}
