# w/o docid
import numpy as np
import json
import random 

id2doc_path = "huggingface_api.jsonl" # doc_id - doc
id2query_val_path = "huggingface_eval.json" # doc_id - query (vali)
id2query_train_path = "huggingface_train.json" # doc_id - query (train)

# preparing train set
with open(id2query_train_path, "r") as f:
    lines = f.readlines()
random.shuffle(lines)

with open('API_train.json', 'w') as f:
    for line in lines:
        dict_ = json.loads(line)
        doc_id = dict_['api_data']['api_name']
        query_text = dict_['code'].split('\n')[0].split(': ')[-1]
        jitem = json.dumps({'completion': doc_id, 'text': 'query: ' + query_text})
        f.write(jitem + '\n')

# preparing val set
with open(id2query_val_path, "r") as f:
    lines = f.readlines()
random.shuffle(lines)

with open('API_valid.json', 'w') as f:
    for line in lines:
        dict_ = json.loads(line)
        doc_id = dict_['api_data']['api_name']
        query_text = dict_['code'].split('\n')[0].split(': ')[-1]
        jitem = json.dumps({'completion': doc_id, 'text': 'query: ' + query_text})
        f.write(jitem + '\n')

print("done creating train and val dataset")