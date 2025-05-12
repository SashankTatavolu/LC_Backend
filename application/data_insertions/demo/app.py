# from indic_transliteration import sanscript
# from indic_transliteration.sanscript import transliterate
# from googletrans import Translator

# input_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/segments.txt'
# output_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/Segments.txt'

# translator = Translator()

# with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
#     for line in infile:
#         line = line.strip()
#         if not line:
#             continue
#         parts = line.split('\t')
#         if len(parts) != 2:
#             print(f"Skipping malformed line: {line}")
#             continue

#         sent_id, hindi = parts
#         wx = transliterate(hindi, sanscript.DEVANAGARI, sanscript.WX)
#         try:
#             english = translator.translate(hindi, src='hi', dest='en').text
#         except Exception as e:
#             print(f"Translation failed for line: {line}\nError: {e}")
#             english = ""

#         # Double tab (`\t\t`) between each column
#         outfile.write(f"{sent_id}\t\t{hindi}\t\t{wx}\t\t{english}\n")

# print(f"Done! Output written to '{output_file}'")



# import re

# def extract_blocks(text):
#     # Capture everything between <sent_id=...> and </sent_id>
#     return re.findall(r'(<sent_id=.*?>\n.*?</sent_id>)', text, re.DOTALL)

# def sort_key(block):
#     # Extract sent_id from the block
#     match = re.search(r'<sent_id=(.*?)>', block)
#     if match:
#         sent_id = match.group(1)
#         # Split sent_id into parts: prefix, number, optional letter
#         parts = re.match(r'^(.*?)(\d+)([a-z]*)$', sent_id)
#         if parts:
#             prefix, number, suffix = parts.groups()
#             return (prefix, int(number), suffix)
#     return ('', 0, '')

# def sort_conllu_file(input_path, output_path):
#     with open(input_path, 'r', encoding='utf-8') as f:
#         raw_text = f.read()

#     blocks = extract_blocks(raw_text)
#     blocks_sorted = sorted(blocks, key=sort_key)

#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write('\n\n'.join(blocks_sorted))

# # === Run the script ===
# if __name__ == '__main__':
#     input_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/USRs.txt'
#     output_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/output.txt'
#     sort_conllu_file(input_file, output_file)
#     print(f"✅ Sorted output written to: {output_file}")


# import json

# # File paths
# input_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/input.json'
# output_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/Segments.txt'

# # Load input JSON from file
# with open(input_file, 'r', encoding='utf-8') as f:
#     data = json.load(f)

# # Sort by segment_index
# data_sorted = sorted(data, key=lambda x: x['segment_index'])

# # Write formatted lines to output file with tab separation
# with open(output_file, 'w', encoding='utf-8') as f:
#     for item in data_sorted:
#         line = f"{item['segment_index']}\t{item['segment_text']}\t{item['english_text']}\t{item['wx_text']}\n"
#         f.write(line)

# print(f"✅ Output written to {output_file} with tab-separated values.")


# import json
# from collections import OrderedDict

# # Load your JSON file
# with open('/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/input.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)

# # Reorder the keys in each sentence
# reordered_sentences = []
# for sentence in data["sentences"]:
#     reordered = OrderedDict()
#     reordered["project_id"] = sentence["project_id"]
#     reordered["sentence_id"] = sentence["sentence_id"]
#     reordered["sentence"] = sentence["sentence"]
#     reordered_sentences.append(reordered)

# # Prepare final structure
# output_data = {"sentences": reordered_sentences}

# # Write to a new JSON file
# with open('/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/output.json', 'w', encoding='utf-8') as f:
#     json.dump(output_data, f, ensure_ascii=False, indent=4)



# def remove_ids_and_get_text(input_file, output_file):
#     seen_sentences = set()
#     running_text = []

#     with open(input_file, 'r', encoding='utf-8') as f:
#         for line in f:
#             parts = line.strip().split('\t', 1)
#             if len(parts) == 2:
#                 sentence = parts[1]
#                 if sentence not in seen_sentences:
#                     seen_sentences.add(sentence)
#                     running_text.append(sentence)

#     with open(output_file, 'w', encoding='utf-8') as f:
#         f.write(' '.join(running_text))


# # Example usage
# remove_ids_and_get_text('/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/sentences.txt', '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/input.txt')



import sys
import re

def process_file(input_file, output_file):
    data = {}

    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue

            sentence_id = parts[0]
            sentence_text = parts[2] if len(parts) >= 3 else ""

            # Extract base ID by removing the trailing a, b, c... etc.
            base_id = re.sub(r'[a-zA-Z]$', '', sentence_id)

            # Merge sentences with the same base ID
            if base_id not in data:
                data[base_id] = sentence_text
            else:
                data[base_id] += sentence_text  # No space to avoid double spacing

    with open(output_file, 'w', encoding='utf-8') as file:
        for base_id, text in data.items():
            file.write(f"{base_id}\t{text.strip()}\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        process_file(input_file, output_file)
