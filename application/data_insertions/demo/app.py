from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from googletrans import Translator

input_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/segments.txt'
output_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/Segments.txt'

translator = Translator()

with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) != 2:
            print(f"Skipping malformed line: {line}")
            continue

        sent_id, hindi = parts
        wx = transliterate(hindi, sanscript.DEVANAGARI, sanscript.WX)
        try:
            english = translator.translate(hindi, src='hi', dest='en').text
        except Exception as e:
            print(f"Translation failed for line: {line}\nError: {e}")
            english = ""

        # Double tab (`\t\t`) between each column
        outfile.write(f"{sent_id}\t\t{hindi}\t\t{wx}\t\t{english}\n")

print(f"Done! Output written to '{output_file}'")



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
