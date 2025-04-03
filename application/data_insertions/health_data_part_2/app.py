import re

def clean_sentence_id(sentence_id):
    """Remove trailing a, b, c, or d from the sentence_id."""
    return re.sub(r'([0-9]+)[abcd]$', r'\1', sentence_id)

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            parts = line.rsplit('\t', 1)  # Split at the last tab
            if len(parts) == 2:
                sentence, sentence_id = parts
                cleaned_id = clean_sentence_id(sentence_id.strip())
                outfile.write(f"{cleaned_id}\t{sentence.strip()}\n")

# Example usage
input_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/health_data_part_2/sentences.txt"
output_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/health_data_part_2/input.txt"
process_file(input_file, output_file)
