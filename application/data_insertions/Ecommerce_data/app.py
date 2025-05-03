# import wxconv
# from googletrans import Translator

# def hindi_to_wx(hindi_text):
#     """Convert Hindi text to WX notation."""
#     converter = wxconv.WXC()  # Use WXC instead of WX
#     return converter.convert(hindi_text)

# def translate_to_english(hindi_text):
#     """Translate Hindi text to English using Google Translate."""
#     translator = Translator()
#     translated = translator.translate(hindi_text, src='hi', dest='en')
#     return translated.text

# def process_file(input_file, output_file):
#     with open(input_file, 'r', encoding='utf-8') as f, open(output_file, 'w', encoding='utf-8') as out:
#         out.write("Segment ID\tHindi\tWX\tEnglish\n")  # Header
#         for line in f:
#             parts = line.strip().split(maxsplit=1)
#             if len(parts) < 2:
#                 continue
#             segment_id, hindi_text = parts
#             wx_text = hindi_to_wx(hindi_text)
#             english_text = translate_to_english(hindi_text)
#             out.write(f"{segment_id}\t{hindi_text}\t{wx_text}\t{english_text}\n")

# # Example usage:
# input_filename = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/segments.txt"  # Change this to your actual file
# output_filename = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/sentences.txt"
# process_file(input_filename, output_filename)
# print(f"Processed file saved as {output_filename}")



def remove_ids_and_combine(file_path, output_path=None):
    running_text = ""

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                running_text += parts[1].strip() + " "

    running_text = running_text.strip()  # Remove trailing space

    if output_path:
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(running_text)
        print(f"Running text saved to {output_path}")
    else:
        print(running_text)


# Example usage:
input_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/sentences.txt"         # Replace with your file name
output_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo/input.txt"       # Optional: Output file
remove_ids_and_combine(input_file, output_file)
