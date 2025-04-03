import wxconv
from googletrans import Translator

def hindi_to_wx(hindi_text):
    """Convert Hindi text to WX notation."""
    converter = wxconv.WXC()  # Use WXC instead of WX
    return converter.convert(hindi_text)

def translate_to_english(hindi_text):
    """Translate Hindi text to English using Google Translate."""
    translator = Translator()
    translated = translator.translate(hindi_text, src='hi', dest='en')
    return translated.text

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f, open(output_file, 'w', encoding='utf-8') as out:
        out.write("Segment ID\tHindi\tWX\tEnglish\n")  # Header
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) < 2:
                continue
            segment_id, hindi_text = parts
            wx_text = hindi_to_wx(hindi_text)
            english_text = translate_to_english(hindi_text)
            out.write(f"{segment_id}\t{hindi_text}\t{wx_text}\t{english_text}\n")

# Example usage:
input_filename = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/Ecommerce_data/segments.txt"  # Change this to your actual file
output_filename = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/Ecommerce_data/Segments.txt"
process_file(input_filename, output_filename)
print(f"Processed file saved as {output_filename}")
