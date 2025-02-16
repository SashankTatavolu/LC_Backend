import subprocess

class ISCTagger:
    def __init__(self):
        pass
    
    def run_tagger(self, sentence):
        try:
            command = f'echo "{sentence}"|isc-tagger'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error executing command: {result.stderr.strip()}"
        except Exception as e:
            return f"Error: {str(e)}"


# tagger = ISCTagger()
# sentence = 'राम ने कहा कि सीता बाजार जा रही है  ? राम बाज़ार जायेगा और सीता घर जा रही है !'
# output = tagger.run_tagger(sentence)
# print(output)
