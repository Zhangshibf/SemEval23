import os
import pickle
from torch.utils.data import Dataset, DataLoader,random_split
import pandas as pd
import argparse
import torch
from nltk.corpus import wordnet as wn
import nltk
from sentence_transformers import SentenceTransformer, util
import numpy as np
class ImageTextDataset(Dataset):
    def __init__(self, data_dir, data_type,device,text_augmentation=False):
        self.device = device
        types = ["inaturalist", "train"]
        if data_type not in types:
            raise ValueError("Invalid data type. Expected one of: %s" % data_type)
        augmentation_types = [True,False]
        if text_augmentation not in augmentation_types:
            raise ValueError("Invalid augmentation type. Expected one of: %s" % augmentation_types)

        self.data_dir = data_dir
        self.image_path = list()
        self.image_name = list()

        if data_type == "inaturalist":
            # I will write this part later
            pass
        elif data_type == "train":
            # this is for the original train set of the task
            all_image_names = list()
            train_data = pd.read_csv(os.path.join(data_dir, "trial.data.v1.txt"), sep="\t", header=None)
            label_data = pd.read_csv(os.path.join(data_dir, "trial.gold.v1.txt"), sep="\t", header=None)
            keywords = list(train_data[0])
            contexts = list(train_data[1])

            for i in range(len(train_data)):
                all_image_names.append(list(train_data.loc[i, 2:]))

            self.keywords = keywords
            self.context = contexts
            image_filenames = list(label_data[0])
            self.negative_image_names = list()
            for a, b in zip(all_image_names,image_filenames):
                a.remove(b)
                self.negative_image_names.append(a)
                self.image_name.append(b)
                self.image_path.append(os.path.join(data_dir, "trial_images_v1", b))

            self.negative_path = list()
            for negs in self.negative_image_names:
                temporary = list()
                for filename in negs:
                    temporary.append(os.path.join(data_dir, "trial_images_v1", filename))
                self.negative_path.append(temporary)

        #text augmentation
        #an augmented text is composed of lemmas + definition from wordnet
        if text_augmentation:
            nltk.download('omw-1.4')
            nltk.download('wordnet')
            self.augmentation = list()
            sent_encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2').to(self.device)
            for keyword,phrase in zip(self.keywords,self.context):

                #retrieve all possible augmented texts
                synsets = wn.synsets(keyword)
                augmented_texts = list()
                if len(synsets)!=0:
                    for synset in synsets:
                        augmented_text = ''
                        for lemma in synset.lemmas():
                            augmented_text += str(lemma.name()).replace('_', ' ') + ', '
                        augmented_text += synset.definition()
                        augmented_texts.append(augmented_text)

                if len(augmented_texts)>1:
                    #check which of the augmented texts is more similar to the short phrase
                    context_emb = sent_encoder.encode(phrase)
                    aug_emb = sent_encoder.encode(augmented_texts)
                    scores = util.dot_score(context_emb, aug_emb)[0].tolist()
                    idx = np.argmax(scores)
                    self.augmentation.append(augmented_texts[idx])
                elif len(augmented_texts) == 1:
                    self.augmentation.append(augmented_texts[0])
                elif len(augmented_texts) == 0:
                    self.augmentation.append(phrase)


    def __len__(self):
        return len(self.context)

    def __getitem__(self, idx):
        # Load the image and text

        #negative images
        negative_images = list()
        negative_image_paths = self.negative_path[idx]
        negative_image_names = self.negative_image_names[idx]
        negative_image_paths = "#".join(negative_image_paths)
        negative_image_names = "#".join(negative_image_names)

        context = self.context[idx]
        keyword = self.keywords[idx]

        positive_path = self.image_path[idx]
        positive_name = self.image_name[idx]

        names = positive_name + "#" + negative_image_names
        paths = positive_path + "#" + negative_image_paths

        if self.augmentation:
            aug = self.augmentation[idx]

        return keyword, context, aug,names, paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build dataloader')
    parser.add_argument('--train', help="path to the train set")
    parser.add_argument("--output",help = "path to save the dataloader")
    args = parser.parse_args()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    # Create the dataset
    dataset = ImageTextDataset(args.train, data_type="train",device = device, text_augmentation=True)
    # Split the dataloader into train, dev, and test sets
    train_size = int(0.8 * len(dataset))
    dev_size = int(0.1 * len(dataset))
    test_size = len(dataset) - train_size - dev_size

    train_dataset, dev_dataset, test_dataset = random_split(dataset, [train_size, dev_size, test_size])

    # Create dataloaders for each set
    train_dataloader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    dev_dataloader = DataLoader(dev_dataset, batch_size=8, shuffle=True)
    test_dataloader = DataLoader(test_dataset, batch_size=8, shuffle=True)

    train_path = args.output+"/train.pk"
    dev_path = args.output + "/dev.pk"
    test_path = args.output + "/test.pk"
    with open(train_path, 'wb') as f:
        pickle.dump(train_dataloader, f)
    with open(dev_path, 'wb') as f:
        pickle.dump(dev_dataloader, f)
    with open(test_path, 'wb') as f:
        pickle.dump(test_dataloader, f)