import re

def extract_sentences(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        # Read the entire file content
        content = infile.read()
        
        # Use regex to find all USR blocks
        usr_blocks = re.findall(r'<sent_id=(.*?)>(.*?)</sent_id>', content, re.DOTALL)
        
        for block in usr_blocks:
            sent_id = block[0].strip()
            block_content = block[1]
            
            # Find the Hindi sentence (line starting with #)
            hindi_sentence = re.search(r'#(.*?)\n', block_content)
            if hindi_sentence:
                sentence = hindi_sentence.group(1).strip()
                # Write to output file
                outfile.write(f"{sent_id}\t{sentence}\n")

# Usage example:
input_file = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/Nios_chapters/chapter_2/USRS.txt'  # Replace with your input file path
output_file = 'extracted_sentences.txt'  # Output file path
extract_sentences(input_file, output_file)

print(f"Extraction complete. Results saved to {output_file}")