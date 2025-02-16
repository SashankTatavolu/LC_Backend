import subprocess


def getMorphFormat(input_sentence):
    command = f"echo '{input_sentence}' | apertium-destxt | lt-proc -ac bin/hi.morfLC.bin | apertium-retxt"
    result = subprocess.run(command, shell=True, text=True, capture_output=True)

    if result.stderr:
        print("Error:", result.stderr)
        return None

    return result.stdout.strip()  


# input_sentence = "rAma ne kahA ki sIwA bAjAra jA rahI hE ? rAma bAjZAra jAyegA Ora sIwA Gara jA rahI hE ." 
# morph_analysis = getMorphFormat(input_sentence)
# if morph_analysis:
#     morph_analysis = morph_analysis.split('?')
#     print("Morphological Analysis:")
#     print(morph_analysis)
# else:
#     print("Failed to get morphological analysis.")
