# SemEval 2023 Task1: Visual Word Sense Disambiguation

## Set up environment


```
. .bashrc

conda env create -f env_sem.yml

conda activate glp

pip install Wikipedia-API transformers sentence_transformers git+https://github.com/openai/CLIP.git
```

## Generate Zero-shot prediction on the English test set


```
python 

python

python
```

## Generate Zero-shot prediction on the Italian test set


```
python 

python

python
```

## Fine-tune CLIP
```
!python clip_fine_tune.py --text_file path/to/text_file --gold_file path/to/gold_file --image_dir path/to/image_dir 

```
You can also pass **--epochs** (Default 5) and **--lr** (Default 5e-5). Also, it is possible to fine-tune your model with or without augmentation by passing **--augmentation** (Default True)
