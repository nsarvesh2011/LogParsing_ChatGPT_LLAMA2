import json

from datasets import load_dataset
import pandas as pd
import os
import json

# Define a function to load training data
def load_train_data(r_dir=".", dataset="Apache", shot=4):
    dataset = load_dataset('json', data_files=f'{r_dir}/{dataset}/{shot}shot/1.json')
    examples = [(x['text'], x['label']) for x in dataset['train']]   # Extract text and label from the training examples
    return examples

# Define a function to load test data
def load_test_data(r_dir=".", dataset="Apache"):
    logs = pd.read_csv(f"{r_dir}/{dataset}/{dataset}_2k.log_structured_corrected.csv")  # Read log data from a CSV file using pandas
    return logs.Content.tolist()   # Return the content of logs as a list

# Define a function to create a one-shot dataset from an existing dataset
def sample_one_shot(r_dir="."):
    for dataset in os.listdir(r_dir):                # Iterate through directories in the specified root directory
        if os.path.isdir(os.path.join(r_dir, dataset)) and "_" not in dataset:    # Check if the item is a directory and does not contain an underscore in its name
            df = pd.read_csv(f"{r_dir}/{dataset}/{dataset}_2k.log_structured_corrected.csv")
            row_id = df['Content'].value_counts()[0]             # Find the row with the most frequently occurring log content
            log, label = df.iloc[row_id].Content, df.iloc[row_id].EventTemplate   # Extract the log content and label from the selected row
            os.makedirs(f'{r_dir}/{dataset}/1shot', exist_ok=True)     # Create a directory to store the one-shot dataset if it does not exist
            with open(f'{r_dir}/{dataset}/1shot/1.json', mode="w") as f:
                f.write(json.dumps({'text': log, 'label': label}))     # Write the one-shot example to a JSON file


if __name__ == '__main__':
    print(load_train_data(shot=2))
