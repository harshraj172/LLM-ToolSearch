# LLM Tool Search

## Files
- `generate.py` samples output of a given input to produce variations using different temperatures and input paraphrases. It produces outputs using the default/normal sampling method and the ranking trick to be proposed.
- `score.py` scores the outputs generated using the default/normal sampling method and the ranking trick to be proposed.
- `score_utils` utility functions for `score.py`.
- `example-consistency_paraphrasing.ipynb` proof of concept of the idea.

## Setup
```
conda create env python=3.9
conda activate env
pip install -r requirements.txt
```
## Experiments
1. There are 4 varians of comparison:
    a. Finetuning (input=query, output=function name) - `python train.py --finetune_type 1 --dataset_name API --model_name t5-base`
    b. Finetuning with docID (input=query, output=docID) - `python train.py --finetune_type 2 --dataset_name API --model_name t5-base`
    c. DSI (input=query, output=docID) - `python train.py --finetune_type 3 --dataset_name API --model_name t5-base`
    d. DSI w/o docID (input=query, output=function name) - `python train.py --finetune_type 4 --dataset_name API --model_name t5-base`
