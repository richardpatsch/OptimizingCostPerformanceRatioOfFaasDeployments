import json
from better_profanity import profanity

profanity.load_censor_words()

def lambda_handler(event, context):
    message = event.get('message')
    reference = event.get('reference')
    print({'data': {'reference': reference, 'id': f'{context.aws_request_id}'}})


    filtered_message = profanity.censor(message)
    indexes = extract_indexes(filtered_message)
    indexes_percent = extract_indexes_percent(filtered_message)

    print("MessageSize:" + str(len(message)))
    print("Number of Profanities:" + str(len(indexes)))
    
    return {
        "originalMessage": message,
        "censoredMessage": filtered_message,
        "indexes": indexes,
        "indexesPercent": indexes_percent,
        "reference": reference
    }
    

def extract_indexes(text, char="*"):
    indexes = []
    in_word = False
    start = 0
    for index, value in enumerate(text):
        if value == char:
            if not in_word:
                # This is the first character, else this is one of many
                in_word = True
                start = index
        else:
            if in_word:
                # This is the first non-character
                in_word = False
                #indexes.append(((start - 1) / len(text), (index) / len(text)))
                indexes.append((start-1, index))
                
    if in_word:
        #indexes.append(((start - 1) / len(text), (index) / len(text)))     
        indexes.append((start-1, index))

    
    return indexes



def extract_indexes_percent(text, char="*"):
    indexes = []
    in_word = False
    start = 0
    for index, value in enumerate(text):
        if value == char:
            if not in_word:
                # This is the first character, else this is one of many
                in_word = True
                start = index
        else:
            if in_word:
                # This is the first non-character
                in_word = False
                indexes.append(((start - 1) / len(text), (index) / len(text)))
                #indexes.append((start-1, index))
                
    if in_word:
        indexes.append(((start - 1) / len(text), (index) / len(text)))     
        #indexes.append((start-1, index))

    
    return indexes
