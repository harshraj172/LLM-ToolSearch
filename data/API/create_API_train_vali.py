import numpy as np
import json

id2doc_path = "huggingface_api.jsonl" # doc_id - doc
id2query_val_path = "huggingface_eval.json" # doc_id - query (vali)
id2query_train_path = "huggingface_train.json" # doc_id - query (train)

# preparing train set
with open(id2query_train_path, "r") as f:
    lines = f.readlines()

with open('API_train.json', 'w') as f:
    for line in lines:
        dict_ = json.loads(line)
        doc_id = dict_['api_data']['api_name']
        doc_text = dict_['api_data']['description']
        query_text = dict_['code'].split('\n')[0].split(': ')[-1]
        jitem = json.dumps({'text_id': doc_id, 'text': 'document: ' + doc_text})
        f.write(jitem + '\n')
        jitem = json.dumps({'text_id': doc_id, 'text': 'query: ' + query_text})
        f.write(jitem + '\n')

# preparing val set
with open(id2query_val_path, "r") as f:
    lines = f.readlines()

with open('API_val.json', 'w') as f:
    for line in lines:
        dict_ = json.loads(line)
        doc_id = dict_['api_data']['api_name']
        query_text = dict_['code'].split('\n')[0].split(': ')[-1]
        jitem = json.dumps({'text_id': doc_id, 'text': 'query: ' + query_text})
        f.write(jitem + '\n')

print("done creating train and val dataset")