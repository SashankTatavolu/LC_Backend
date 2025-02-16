import json
from application.segment_repository.sentence_chunker import SentenceChunkerMain

class Segmentor:
    def __init__(self, chunks):
        self.chunks = chunks
        self.lines = []
        self.arr = []
        self.seen_sentences = set()

    def read_file(self):
        file = self.chunks.split('\n')
        for line in file:
            self.lines.append(line.strip().split())
        self.lines = [sublist for sublist in self.lines if sublist]
        # print(self.lines)
    
    def convert_to_sentence(self,chunked_text):
        # Split the text into lines
        lines = chunked_text.strip().split('\n')
        
        # Extract only the first element (word) from each line by splitting on '\t'
        words = [line.split('\t')[0] for line in lines if line.strip()]  # Ignore empty lines

        # Join the words into a single sentence
        sentence = ' '.join(words)

        # Replace any extra spaces and handle punctuation if needed
        sentence = sentence.replace("((", "").replace("))", "").replace(" ।", "।").replace("  ", " ")

        return sentence


    def get_output(self, j, l):
        count = 0
        flag = False
        flag1 = False
        for i in range(j, len(self.lines)):
            if len(self.lines[i]) > 1 and self.lines[i][1] == 'VGF':
                flag = True
                
            if len(self.lines[i]) > 2 and self.lines[i][2] == 'CC' and flag:
                if self.lines[i][0] == 'कि':
                    for o in range(i-1, 0, -1):
                        if 'इतना' == self.lines[o][0] or 'इतनी' == self.lines[o][0] or 'इतने' == self.lines[o][0]:
                            flag1 = True
                            break
                    if not flag1:
                        for k in range(i - 1, 0, -1):
                            if 'VM' in self.lines[k] and not flag1:
                                self.lines.insert(k, ['यह'])
                                break
                count += 1
                sentence = " ".join([self.lines[o][0] for o in range(j, i)])
                sentence = sentence.replace("((", "").replace("))", "").replace("  ", " ")
                self.add_sentence(sentence)
                flag = False
                self.get_output(i, l)
                
            elif i == l:
                words = []
                for o in range(l, len(self.lines)):
                    words.append(self.lines[o][0])
                sentence = " ".join(words)
                sentence = sentence.replace("((", "").replace("))", "").replace("  ", " ")
                self.add_sentence(sentence)
                break
        return count

    def add_sentence(self, sentence):
        if sentence not in self.seen_sentences:
            self.arr.append(sentence)
            self.seen_sentences.add(sentence)
        i = 0
        while i < len(self.arr) - 1:
            j = i + 1
            while j < len(self.arr):
                if self.arr[i] in self.arr[j]:
                    del(self.arr[j])
                else:
                    j += 1
            i += 1

    def add_yah_agar(self):
        if len(self.arr) > 0 and self.arr[0].startswith('अगर'):
            for i in range(len(self.arr)):
                words = self.arr[i].split()
                for j in range(len(words)):
                    if words[j] in ['और', 'तथा', 'एवं']:
                        words.insert(j + 1, 'अगर')
                        break
                self.arr[i] = ' '.join(words)

    def process(self):
        self.read_file()
        f1 = False
        for l in range(len(self.lines) - 1, 0, -1):
            if len(self.lines[l]) > 2 and self.lines[l][2] == 'CC':
                f1 = True
                cc_index = l
                self.get_output(0, cc_index)
                break
        if not f1:
            words = []
            for o in range(len(self.lines)):
                words.append(self.lines[o][0])
            sentence = " ".join(words)
            sentence = sentence.replace("((", "").replace("))", "").replace("  ", " ")
            self.add_sentence(sentence)
            
        self.add_yah_agar()

    @staticmethod
    def add_purnaviram(sentences):
        sentences_with_punc = []
        for sentence in sentences:
            if any(sentence.strip().endswith(char) for char in ['।', '?', '!']):
                sentences_with_punc.append(sentence.strip())
            else:
                sentence_with_punc = sentence.strip() + ' ।'
                sentences_with_punc.append(sentence_with_punc)
        return sentences_with_punc

    def is_first_word_digit(self, sentence):
        words = sentence.split()
        # print('word-->', words)
        return words[0].isdigit() if words else False
    
    def get_suffix(self, index):
        return chr(ord('a') + index)

    def write_output(self, sentence_id):
        if len(self.arr) == 0:
            print("No sentences to process.")
            return

        # json_output = {"sentence_id": str(sentence_id), "sentence_text": self.chunks, "segments": []}
        json_output = {"sentence_id": str(sentence_id), "sentence_text": self.convert_to_sentence(self.chunks), "segments": []}

        i = 0
        id_counter = 1
        multiple_segments = len(self.arr) > 1  # Check if multiple segments exist

        while i < len(self.arr):
            sentence = self.arr[i].strip()
            # print('sent--->', sentence)

            # Assign segment IDs with or without suffix based on whether multiple segments exist
            if multiple_segments:
                segment_id = f"{sentence_id}{self.get_suffix(i)}"  # Append suffix if multiple segments
            else:
                segment_id = f"{sentence_id}"  # Keep segment_id same as sentence_id if single segment

            json_output["segments"].append({"segment_id": segment_id, "segment_text": sentence})

            i += 1

        return json_output
