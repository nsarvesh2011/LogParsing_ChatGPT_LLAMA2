import pandas as pd
import re
from collections import Counter

param_regex = [
    r'{([ :_#.\-\w\d]+)}',
    r'{}'
]

out_dir = "ChatGPT/zero_shot"

datasets = [ 'Spark']
# datasets = ["HDFS", "Spark", "BGL", "HPC", "Windows", "Linux", "Android", "HealthApp", "Apache", "OpenStack", "Mac"]

# Define a function to correct a single log template using various rules
def correct_single_template(template, user_strings=None):
    """Apply all rules to process a template.

    DS (Double Space)
    BL (Boolean)
    US (User String)
    DG (Digit)
    PS (Path-like String)
    WV (Word concatenated with Variable)
    DV (Dot-separated Variables)
    CV (Consecutive Variables)

    """

    boolean = {'true', 'false'}       # Define a set of boolean values
    default_strings = {'null', 'root', 'admin'}   # Define a set of default string values
    path_delimiters = {  # Define a set of delimiters for tokenizing path-like strings
        r'\s', r'\,', r'\!', r'\;', r'\:',
        r'\=', r'\|', r'\"', r'\'',
        r'\[', r'\]', r'\(', r'\)', r'\{', r'\}'
    }
    token_delimiters = path_delimiters.union({  # Define all delimiters for tokenizing
        r'\.', r'\-', r'\+', r'\@', r'\#', r'\$', r'\%', r'\&',
    })

    if user_strings:
        default_strings = default_strings.union(user_strings)

    # Apply DS (Double Space) by stripping and replacing multiple spaces with a single space
    template = template.strip()
    template = re.sub(r'\s+', ' ', template)

    # Apply PS (Path-like String) by tokenizing and replacing valid paths with '<*>'
    p_tokens = re.split('(' + '|'.join(path_delimiters) + ')', template)
    new_p_tokens = []
    for p_token in p_tokens:
        if re.match(r'^(\/[^\/]+)+$', p_token):
            p_token = '<*>'
        new_p_tokens.append(p_token)
    template = ''.join(new_p_tokens)

    # Tokenize the template for the remaining rules
    tokens = re.split('(' + '|'.join(token_delimiters) + ')', template)  # tokenizing while keeping delimiters
    new_tokens = []
    for token in tokens:
        # Apply BL (Boolean) and US (User String) by replacing matching tokens with '<*>'
        for to_replace in boolean.union(default_strings):
            if token.lower() == to_replace.lower():
                token = '<*>'

         # Apply DG (Digit) by replacing numeric tokens with '<*>'
        if re.match(r'^\d+$', token):
            token = '<*>'

        # Apply WV (Word concatenated with Variable) by replacing matching tokens with '<*>'
        if re.match(r'^[^\s\/]*<\*>[^\s\/]*$', token):
            if token != '<*>/<*>':  # need to check this because `/` is not a deliminator
                token = '<*>'

        # collect the result
        new_tokens.append(token)

    # make the template using new_tokens
    template = ''.join(new_tokens)

   # Repeatedly substitute consecutive variables separated by '.' (DV) with a single '<*>'
    while True:
        prev = template
        template = re.sub(r'<\*>\.<\*>', '<*>', template)
        if prev == template:
            break

    # Repeatedly substitute consecutive variables not separated by any delimiter including space (CV) with a single '<*>'
    while True:
        prev = template
        template = re.sub(r'<\*><\*>', '<*>', template)
        if prev == template:
            break

    # Replace "#<*>#" with "<*>"
    while "#<*>#" in template:
        template = template.replace("#<*>#", "<*>")

    # Replace "<*>:<*>" with "<*>"
    while "<*>:<*>" in template:
        template = template.replace("<*>:<*>", "<*>")
    return template


if __name__ == '__main__':
    for dname in datasets:
        log_df = pd.read_csv(f"{out_dir}/{dname}_2k.log_structured.csv")   # Read the log data from a CSV file into a Pandas DataFrame
        content = log_df.Content.tolist()
        template = log_df.EventTemplate.tolist()
        for i in range(len(content)):
            c = content[i]
            t = str(template[i])
            for r in param_regex:
                # print(r)
                t = re.sub(r, "<*>", t)    # Replace parameter placeholders with "<*>"
                # print(t)
            # if "{{}}" in t:
            #     print(t)
            #     print(re.sub(r'\{\{}}', "<*>", t))
            #     print(re.sub(r'{{}}', "<*>", t))
            template[i] = correct_single_template(t)
        log_df.EventTemplate = pd.Series(template)    # Update the EventTemplate column in the DataFrame

        unique_templates = sorted(Counter(template).items(), key=lambda k: k[1], reverse=True)  # Count the occurrences of each unique template
        temp_df = pd.DataFrame(unique_templates, columns=['EventTemplate', 'Occurrences'])
        # temp_df.sort_values(by=["Occurrences"], ascending=False, inplace=True)
        # Save the adjusted log data and template occurrences to new CSV files
        log_df.to_csv(f"{out_dir}/{dname}_2k.log_structured_adjusted.csv")
        temp_df.to_csv(f"{out_dir}/{dname}_2k.log_templates_adjusted.csv")
        # except:
        #     pass
