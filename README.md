# LLM Tool Search

## Setup
```
conda create env python=3.9
conda activate env
pip install -r requirements.txt
```
## Experiments
1. There are 4 varians of comparison:
    
    - **Finetuning (input=query, output=function name)** 
    
    `python train.py --finetune_type 1 --dataset_name API --model_name t5-base`

    - **Finetuning with docID (input=query, output=docID)**  
    
    `python train.py --finetune_type 2 --dataset_name API --model_name t5-base`
    
    - **DSI (input=query, output=docID)** 
    
    `python train.py --finetune_type 3 --dataset_name API --model_name t5-base`
    
    - **DSI w/o docID (input=query, output=function name)** 
    
    `python train.py --finetune_type 4 --dataset_name API --model_name t5-base`
