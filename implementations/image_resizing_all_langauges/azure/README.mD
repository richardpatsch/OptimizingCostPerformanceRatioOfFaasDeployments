log query in insights:

traces
| extend data=parse_json(message)
| extend rId=tostring(data.RequestId)
| filter isnotnull(data.KeyName)
| project data.KeyName, data.ImageTime, data.Language, data.RequestId, data.Memory, rId
| join (requests
| extend rId=tostring(customDimensions['InvocationId'])
| project timestamp, customDimensions['InvocationId'], success, duration, rId)
on rId
| filter success==True
| project data_KeyName, data_ImageTime, data_Language, rId, data_Memory, timestamp, duration
| project-rename KeyName=data_KeyName, ImageTime=data_ImageTime, Language=data_Language, requestId=rId, Memory=data_Memory
