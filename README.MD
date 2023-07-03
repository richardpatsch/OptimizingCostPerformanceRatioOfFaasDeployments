This is the corresponding respository for the submitted paper: **Optimizing the Cost-Performance Ratio of FaaS Deployments**. All implementations and measurements can be found here.

# Abstract

Autoscaling serverless architectures utilizing Function as a Service (FaaS) are an established model. While there is virtually no limit to scalability in theory, in practice, a trade-off between price and performance determines the cost-efficient scalability of cloud deployments. Finding the correct specifications becomes even harder when the computational demands depend highly on the functions' inputs. Consequently, a single configuration is often not cost-efficient enough.

To solve this problem, our paper proposes a deployment model for multiple specifications to cover inputs with differing computational demands. By defining categories for the functions' inputs, requests can be routed to particular deployments to increase the overall cost-performance ratio. Applied filters to the functions' triggers alleviate the complexity of multiple deployments, and deployments can actively select inputs within their assigned category.

We evaluated our approach with multiple use cases and programming languages on Amazon Web Services (AWS) and Azure. Multiple deployments can generally be justified, if cost is higher for shorter duration. The efficiency of our approach depends on (i) the assignment of correct categories, (ii) the number of requests in each category, and (iii) the configuration granularity of the Cloud Service Provider. Different languages do not influence the effectiveness of this approach. Limited configuration possibilities on Azure hinder the effectiveness of this approach. Thus, it is easier to find the best cost-performance ratio on AWS.

![concept for multiple deployments](/repo_images/concept_design.png)

# Data

The folder data contains a, with pg_dump created, database dump of all measurements taken.
Measurements for the langauge comparison are in the table: "measurements_langauges", all other measurements are in the "measurements" table. Function description and Ids are in the "functions" table.

# Implementations / Evaluation

All measured examples are in the implementations example:

1. facedetection
   ![face recognition workflow](/repo_images/face_recognition_v2.png)
   detects faces on an image and blurs them.

2. fibonacci
   generates the nth number of the Fibonacci sequence.

3. image resizing
   resizes an image to a width of 100px. height is scaled down proportionally.
   On AWS this was evaluated in: dotnet, java, javascript, go, ruby, python, on Azure in: dotnet, java, javascript and python.

4. text 2 speech
   ![text2speech workflow](/repo_images/tts.png)
   A text to speech workflow to convert text to an mp3 file, filter profanity, convert it to wav and then compress it.

5. thumbnail stack
   ![thumbnail stack workflow](/repo_images/processing.png)
   A complex cloud formation stack, that also includes a lambda function and several other AWS services. As of now this example did not make it into the paper due to page constraints.
