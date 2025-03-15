input_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo_data/sentences.txt"   # Change this to your actual input file
output_file = "/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/demo_data/input.txt"  # Output file with running text

running_text = ""

with open(input_file, "r", encoding="utf-8") as infile:
    for line in infile:
        columns = line.strip().split("\t")  # Split by tab
        if len(columns) >= 2:
            running_text += columns[1] + " "  # Append sentence, add space

running_text = running_text.strip()  # Remove trailing space

# Save to file
with open(output_file, "w", encoding="utf-8") as outfile:
    outfile.write(running_text + "\n")

# Print output
print(running_text)
print(f"\nRunning text saved to '{output_file}'")
