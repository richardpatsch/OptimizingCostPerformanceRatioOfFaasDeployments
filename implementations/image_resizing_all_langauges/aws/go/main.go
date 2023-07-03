package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-lambda-go/lambdacontext"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/disintegration/imaging"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"log"
	"os"
	"strconv"
	"time"
)

type MyEvent struct {
	S3Bucket string `json:"s3Bucket"`
	S3Key    string `json:"s3Key"`
}

func HandleRequest(ctx context.Context, event MyEvent) (string, error) {
	sess := session.Must(session.NewSession())
	svc := s3.New(sess)

	input := &s3.GetObjectInput{
		Bucket: aws.String(event.S3Bucket),
		Key:    aws.String(event.S3Key),
	}

	result, err := svc.GetObject(input)
	if err != nil {
		return "", err
	}

	start := time.Now().UnixNano() / int64(time.Millisecond)

	img, _, err := image.Decode(result.Body)
	if err != nil {
		return "", err
	}

	resizedImg := imaging.Resize(img, 100, 0, imaging.Lanczos)

	buf := new(bytes.Buffer)
	err = imaging.Encode(buf, resizedImg, imaging.PNG)

	if err != nil {
		return "", err
	}

	end := time.Now().UnixNano() / int64(time.Millisecond)
	diff := end - start // delta in ms

	// log.Printf("go resizing for %s with %s took %s", event.S3Key, os.Getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"), elapsed)
	memory, _ := strconv.Atoi(os.Getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"))
	lc, _ := lambdacontext.FromContext(ctx)

	data := map[string]interface{}{
		"KeyName":   event.S3Key,
		"Memory":    memory,
		"ImageTime": diff,
		"Language":  "go",
		"RequestId": lc.AwsRequestID,
	}

	jsonData, err := json.Marshal(data)
	log.Printf(string(jsonData))

	outinput := &s3.PutObjectInput{
		Body:   bytes.NewReader(buf.Bytes()),
		Bucket: aws.String(event.S3Bucket),
		Key:    aws.String("resized/go_" + event.S3Key),
	}

	_, err = svc.PutObject(outinput)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Image %s in bucket %s resized successfully!", event.S3Key, event.S3Bucket), nil
}

func main() {
	lambda.Start(HandleRequest)
}
