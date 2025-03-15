import os

def merge_files(input_folder, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for filename in sorted(os.listdir(input_folder)):
                if filename.endswith('.txt'):
                    file_path = os.path.join(input_folder, filename)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        print(f"Merging file: {filename}")
                        content = infile.read()
                        outfile.write(content + '\n')  # Append content with a newline
        print(f"\n✅ All files merged into '{output_file}' successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Usage
input_folder = "/home/sashank/Downloads/FAQ/faq"      # Your input folder path
output_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo_data/merged_output.txt"  # Output file name

merge_files(input_folder, output_file)
