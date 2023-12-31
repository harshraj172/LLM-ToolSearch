import argparse
from data import IndexingTrainDataset, IndexingCollator, QueryEvalCollator
from transformers import T5Tokenizer, T5ForConditionalGeneration, TrainingArguments, TrainerCallback
from trainer import IndexingTrainer
import numpy as np
import torch
import wandb
from torch.utils.data import DataLoader
from tqdm import tqdm


class QueryEvalCallback(TrainerCallback):
    def __init__(self, test_dataset, logger, restrict_decode_vocab, args: TrainingArguments, tokenizer: T5Tokenizer):
        self.tokenizer = tokenizer
        self.logger = logger
        self.args = args
        self.test_dataset = test_dataset
        self.restrict_decode_vocab = restrict_decode_vocab
        self.dataloader = DataLoader(
            test_dataset,
            batch_size=self.args.per_device_eval_batch_size,
            collate_fn=QueryEvalCollator(
                self.tokenizer,
                padding='longest'
            ),
            shuffle=False,
            drop_last=False,
            num_workers=self.args.dataloader_num_workers,
        )

    def on_evaluate(self, args, state, control, **kwargs):
        hit_at_1 = 0
        hit_at_10 = 0
        model = kwargs['model'].eval()
        for batch in tqdm(self.dataloader, desc='Evaluating dev queries'):
            inputs, labels = batch
            with torch.no_grad():
                if self.restrict_decode_vocab:
                    batch_beams = model.module.generate(
                        inputs['input_ids'].to(model.device),
                        max_length=20,
                        num_beams=10,
                        prefix_allowed_tokens_fn=self.restrict_decode_vocab,
                        num_return_sequences=10,
                        early_stopping=True, ).reshape(inputs['input_ids'].shape[0], 10, -1)
                else:
                    batch_beams = model.module.generate(
                        inputs['input_ids'].to(model.device),
                        max_length=20,
                        num_beams=10,
                        num_return_sequences=10,
                        early_stopping=True, ).reshape(inputs['input_ids'].shape[0], 10, -1)
                for beams, label in zip(batch_beams, labels):
                    rank_list = self.tokenizer.batch_decode(beams,
                                                            skip_special_tokens=True)  # beam search should not return repeated docids but somehow due to T5 tokenizer there some repeats.
                    hits = np.where(np.array(rank_list)[:10] == label)[0]
                    if len(hits) != 0:
                        hit_at_10 += 1
                        if hits[0] == 0:
                            hit_at_1 += 1
        self.logger.log({"Hits@1": hit_at_1 / len(self.test_dataset), "Hits@10": hit_at_10 / len(self.test_dataset)})


def compute_metrics(eval_preds):
    num_predict = 0
    num_correct = 0
    for predict, label in zip(eval_preds.predictions, eval_preds.label_ids):
        num_predict += 1
        if len(np.where(predict == 1)[0]) == 0:
            continue
        if np.array_equal(label[:np.where(label == 1)[0].item()],
                          predict[np.where(predict == 0)[0][0].item() + 1:np.where(predict == 1)[0].item()]):
            num_correct += 1

    return {'accuracy': num_correct / num_predict}


def main():
    L = 50  # only use the first 32 tokens of documents (including title)

    # We use wandb to log Hits scores after each epoch. Note, this script does not save model checkpoints.
    wandb.login()
    wandb.init(project="llm_tool_search", name=f"{args.dataset_name}-{args.model_name}-{args.finetune_type}-{args.train_file_name.split('-')[-1]}")

    tokenizer = T5Tokenizer.from_pretrained(args.model_name, cache_dir='cache')
    model = T5ForConditionalGeneration.from_pretrained(args.model_name, cache_dir='cache')

    train_dataset = IndexingTrainDataset(path_to_data=f"data{'-finetune' if args.finetune_type in [1, 2] else ''}/{args.dataset_name}/{args.train_file_name}",
                                         max_length=L,
                                         cache_dir='cache',
                                         tokenizer=tokenizer,)
    
    # This eval set is really not the 'eval' set but used to report if the model can memorise (index) all training data points.
    eval_dataset = IndexingTrainDataset(path_to_data=f"data{'-finetune' if args.finetune_type in [1, 2] else ''}/{args.dataset_name}/{args.val_file_name}",
                                        max_length=L,
                                        cache_dir='cache',
                                        tokenizer=tokenizer,)
    
    # This is the actual eval set.
    test_dataset = IndexingTrainDataset(path_to_data=f"data{'-finetune' if args.finetune_type in [1, 2] else ''}/{args.dataset_name}/{args.val_file_name}",
                                        max_length=L,
                                        cache_dir='cache',
                                        tokenizer=tokenizer,)

    ################################################################
    # docid generation constrain, we only generate integer docids.
    SPIECE_UNDERLINE = "▁"
    INT_TOKEN_IDS = []
    for token, id in tokenizer.get_vocab().items():
        if token[0] == SPIECE_UNDERLINE:
            if token[1:].isdigit():
                INT_TOKEN_IDS.append(id)
        if token == SPIECE_UNDERLINE:
            INT_TOKEN_IDS.append(id)
        elif token.isdigit():
            INT_TOKEN_IDS.append(id)
    INT_TOKEN_IDS.append(tokenizer.eos_token_id)

    def restrict_decode_vocab(batch_idx, prefix_beam):
        return INT_TOKEN_IDS
    ################################################################    
    
    training_args = TrainingArguments(
        output_dir="./results",
        learning_rate=0.0005,
        warmup_steps=10000,
        # weight_decay=0.01,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        evaluation_strategy='steps',
        eval_steps=5000,
        max_steps=20000,
        dataloader_drop_last=False,  # necessary
        report_to='wandb',
        logging_steps=200,
        save_strategy='no',
        # fp16=True,  # gives 0/nan loss at some point during training, seems this is a transformers bug.
        dataloader_num_workers=10,
        gradient_accumulation_steps=args.gradient_accumulation_steps
    )
    
    if args.finetune_type in [2, 3]:
        kwargs = \
        {'callbacks': [QueryEvalCallback(test_dataset, wandb, restrict_decode_vocab, training_args, tokenizer)],
         'restrict_decode_vocab': restrict_decode_vocab,}
    else:
        kwargs = {'callbacks': [QueryEvalCallback(test_dataset, wandb, None, training_args, tokenizer)],}
    trainer = IndexingTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=IndexingCollator(
            tokenizer,
            padding='longest',
        ),
        compute_metrics=compute_metrics,
        **kwargs
    )
    trainer.train(
    )


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='parser to run the script')

    # add arguments
    parser.add_argument('--finetune_type',
                        type=int,
                        default=1,
                        help='''Method for finetuning:
                        1 - finetuning (input=query, output=function name)
                        2 - finetuning with docID (input=query, output=docID)
                        3 - DSI (input=query, output=docID)
                        4 - DSI w/o docID (input=query, output=function name)
                        ''')
    parser.add_argument('--dataset_name',
                        type=str,
                        default="API",
                        help='name of the dataset')
    parser.add_argument('--model_name',
                        type=str,
                        default="t5-base",
                        help='model to be finetuned')
    args = parser.parse_args()
    if args.finetune_type == 1:
        args.train_file_name = f'{args.dataset_name}_train-0.75.json'
        args.val_file_name = f'{args.dataset_name}_valid.json'
        args.gradient_accumulation_steps = 1
    elif args.finetune_type == 2:
        args.train_file_name = f'{args.dataset_name}_train-docid-0.75.json'
        args.val_file_name = f'{args.dataset_name}_valid-docid.json'
        args.gradient_accumulation_steps = 1
    elif args.finetune_type == 3:
        args.train_file_name = f'{args.dataset_name}_multi_task_train-docid-0.75.json'
        args.val_file_name = f'{args.dataset_name}_valid-docid.json'
        args.gradient_accumulation_steps = 2
    elif args.finetune_type == 4:
        args.train_file_name = f'{args.dataset_name}_multi_task_train-0.75.json'
        args.val_file_name = f'{args.dataset_name}_valid.json'
        args.gradient_accumulation_steps = 2
        
    main()