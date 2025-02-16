import sys
import re
from wxconv import WXC
from application.segment_repository.run_tagger import ISCTagger
from application.segment_repository.run_morph import getMorphFormat
from application.constant.all_tam import TAM_LIST

class SentenceChunker:
    def __init__(self):
        self.tagger = ISCTagger()

    def tag_sentence(self, sentence):
        tagger_output = self.tagger.run_tagger(sentence)
        tag_out = tagger_output.split('\n')
        tagged_words = []
        index = 1  
        for item in tag_out:
            if item:
                hin_word, tag = item.split()
                tagged_words.append([index, hin_word, tag])  
                index += 1  
        return tagged_words

    def morph_analyze(self, sentence):
        hin_to_wx = WXC(order="utf2wx", lang="hin")
        wx_sent = hin_to_wx.convert(sentence)
        complete_morph_output = getMorphFormat(wx_sent)
        morph_outputs = complete_morph_output.split('?.!')
        for morph_output in morph_outputs:
            word_morph_output = morph_output.split("$")
            morph_info = []
            for item in word_morph_output:
                symbol_match = re.search(r'([?.!])\s\^', item)
                symbol = symbol_match.group(1) if symbol_match else None
                if symbol:
                    word = symbol
                    root = symbol
                    tam = 'unk'
                    morph_info.append([word, root, tam])
                    # continue
                
                word_match = re.search(r'\^([^/]+)/', item)
                word = word_match.group(1) if word_match else item.split('/')[0].strip('^ ')
                tam_match = re.search(r'<tam:(?P<tam>[^>]*)>', item)
                tam = tam_match.group('tam') if tam_match else "unk"
                root_match = re.search(r'/(?P<root>[^<]*)<', item)
                root = root_match.group('root') if root_match else item.split('/')[0].strip('^ ')
                morph_info.append([word, root, tam])
            return morph_info
    
    def identify_VGF(self, complete_word_info):
        ranjak_list= ["cala", "dAla", "cuka", "xe", "lenA", "bETa", "uTa", "jA", "padZa", "A"]
        for info in complete_word_info:
            if info[2] == 'VM':
                word = info[3]
                word_index = info[0]
                temp_word_index = temp_word_index_iter = word_index + 1
                temp_pos_tag = 0
                vaux_count = 0
                while (
                    temp_word_index <= len(complete_word_info) and
                    temp_word_index <= len(complete_word_info) and
                    complete_word_info[temp_word_index - 1][2] == "VAUX"
                ):
                    vaux_count += 1
                    temp_word_index += 1
    
                if vaux_count == 0:
                    if info[4] in ('hE', 'WA'):
                        complete_tam = 'hE_1-pres' if info[4] == 'hE' else 'hE_1-past'
                    else:
                        complete_tam = info[5] + '_1'
                    
                    if complete_tam in TAM_LIST:
                        info.append('VGF')
                
                elif vaux_count == 1:
                    word_index_in = temp_word_index_iter
                    vm_root = info[4]
                    vm_suffix = info[5]
    
                    if (
                        int(word_index_in) == info[0] + 1 and
                        complete_word_info[temp_word_index_iter - 1][2] == 'VAUX'
                    ):
                        vaux_root = complete_word_info[temp_word_index_iter - 1][4]
                        vaux_suffix = complete_word_info[temp_word_index_iter - 1][5]
                        vaux_word = complete_word_info[temp_word_index_iter - 1][3]
                        
                    if vaux_root == 'jA' and vm_suffix == 'yA':
                        complete_tam = vm_suffix + '_' + vaux_root + '_' + vaux_suffix
                    elif(vaux_root in ranjak_list):
                        complete_tam = vaux_suffix
                    else:
                        complete_tam = vm_suffix + '_' + vaux_word
    
                    complete_tam = complete_tam + '_1' 
                    if complete_tam in TAM_LIST:
                        info.append('VGF')
    
                else:
                    word_index_in = temp_word_index_iter
                    vm_root = info[4]
                    vm_suffix = info[5]
                    vaux_word = complete_word_info[temp_word_index_iter - 1][3]
                    vaux_root = complete_word_info[temp_word_index_iter - 1][4]
                    vaux_suffix = complete_word_info[temp_word_index_iter - 1][5]
    
                    if vaux_root == 'jA' and vm_suffix == 'yA':
                        if vaux_suffix == "0":
                            complete_tam = vm_suffix + "_" + vaux_root
                        else:
                            complete_tam = vm_suffix + "_" + vaux_root + "_" + vaux_suffix
    
                        temp_word_index_in = word_index_in
                        while (
                            temp_word_index_in < len(complete_word_info) and
                            complete_word_info[temp_word_index_in][2] == "VAUX"
                        ):
                            temp_vaux = complete_word_info[temp_word_index_in][3]
                            complete_tam = complete_tam + "_" + temp_vaux
                            temp_word_index_in += 1
                    
                    elif(vaux_root in ranjak_list):
                        complete_tam = vaux_suffix
                        temp_word_index_in = word_index_in
                        while (
                            temp_word_index_in < len(complete_word_info) and
                            complete_word_info[temp_word_index_in][2] == "VAUX"
                        ):
                            temp_vaux = complete_word_info[temp_word_index_in][3]
                            complete_tam = complete_tam + "_" + temp_vaux
                            temp_word_index_in += 1
    
                    else:
                        complete_tam = vm_suffix
                        temp_word_index_in=word_index_in-1
                        while (
                            temp_word_index_in < len(complete_word_info) and
                            complete_word_info[temp_word_index_in][2] == "VAUX"
                        ):
                            temp_vaux = complete_word_info[temp_word_index_in][3]
                            complete_tam = complete_tam + "_" + temp_vaux
                            temp_word_index_in += 1
                            
                    complete_tam = complete_tam + '_1' 
                    # print('complete_tam-->',)
                    if complete_tam in TAM_LIST:
                        info.append('VGF')
    
    def format_output(self, complete_word_info):
        formatted_output = ""
        group = False
        for item in complete_word_info:
            word = item[1]
            index = item[0]
            tag = item[2]
            vgf = 'VGF' if len(item) > 6 and 'VGF' in item[6] else ''
            if vgf:
                if not group:
                    formatted_output += "((" + "\t\t" + vgf + "\n"
                    group = True
            else:
                if group:
                    formatted_output += "))\n"
                    group = False
            formatted_output += f"{word}\t{index}\t{tag}\n"
        if group:
            formatted_output += "))"
        return formatted_output

class SentenceChunkerMain:
    @staticmethod
    def main(sentence):
        processor = SentenceChunker()
        tagged_words = processor.tag_sentence(sentence)
        morph_info = processor.morph_analyze(sentence)
        # print('tagger_output-->', tagged_words)
        # print('morph output-->', morph_info)
        complete_word_info = []
        for i in range(min(len(tagged_words), len(morph_info))):
            complete_word_info.append(tagged_words[i] + morph_info[i])

        # Identify VGF in complete_word_info
        processor.identify_VGF(complete_word_info)
        # print('complete info-->', complete_word_info)
        split_lists = []
        current_list = []
        for item in complete_word_info:
            if item[1] in ['?', '.', '!', '।']:
                current_list.append(item)
                # If the current list is not empty, append it to split_lists
                if current_list:
                    split_lists.append(current_list)
                # Create a new empty list for the next split
                current_list = []
            else:
                # Append the current item to the current list
                current_list.append(item)
    
        
        # Append the last remaining current list
        if current_list:
            split_lists.append(current_list)
        # print('final list --->', split_lists)

        formatted_outputs = []
        # for lst in split_lists:
        for idx, lst in enumerate(split_lists, 1):  
            formatted_output = processor.format_output(lst)
            # print(formatted_output)
            # formatted_outputs.append(f'{idx} \n{formatted_output}\n\n')
            formatted_outputs.append(f'{formatted_output}\n\n')
            # print(formatted_outputs)
        return formatted_outputs


