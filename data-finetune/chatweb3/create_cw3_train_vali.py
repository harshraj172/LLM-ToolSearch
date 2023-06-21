import re
import numpy as np
import json

with open('chatweb3_data-2.jsonl', "r") as f:
    data = f.readlines()

NUM_TRAIN = int(len(data)*0.9)
NUM_EVAL = int(len(data)*0.1)

with open('widgets.txt', "r") as f:
    lines = f.read()

count = 1 
widg2doc, widg2id = {}, {}
for l in lines.split('---'):
    widg2doc[re.search(r'\|(.*?)\(', l).group(1)] = l.split('Description of widget: ')[-1].split('\nRequired parameters:')[0]
    widg2id[re.search(r'\|(.*?)\(', l).group(1)] = count
    count += 1 
    
with open('chatweb3_train.json', 'w') as tf, \
        open('chatweb3_valid.json', 'w') as vf:
    for ind in range(NUM_TRAIN + NUM_EVAL):
        dict_ = json.loads(data[ind])
        if dict_['completion'] == '<WIDGET_NA><eot>': 
            print('found <WIDGET_NA><eot>')
            continue
        
        query_text = dict_['prompt']
        completion_text = dict_['completion']

        jitem = json.dumps({'completion': completion_text, 'text': 'query: ' + query_text})
        if ind <= NUM_TRAIN:
            tf.write(jitem + '\n')
        else:
            vf.write(jitem + '\n')
print("created train & val set")