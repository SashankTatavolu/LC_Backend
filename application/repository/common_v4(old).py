import os
import sys
import re
import subprocess
import os
import sys
import re
import subprocess
import application.repository.constant
from wxconv import WXC
import json
import tempfile
# from googletrans import Translator
from indic_transliteration import sanscript
# from bulk_runner import output_list1
# from generate_input_modularize_new import additional_words_dict,spkview_dict
# from Table import store_data
from application.repository.verb import Verb
from application.repository.concept import Concept
from wxconv import WXC
import json
import tempfile
# from googletrans import Translator
from indic_transliteration import sanscript
# from bulk_runner import output_list1
# from generate_input_modularize_new import additional_words_dict,spkview_dict
# from Table import store_data
from application.repository.verb import Verb
from application.repository.concept import Concept
additional_words_dict = {}
processed_postpositions_dict = {}
construction_dict = {}
spkview_dict = {}
MORPHO_SEMANTIC_DICT = {}
data_case_for_k4=[]
construction_dict_to_leave={}
#pre processing

# def read_file(file_path):
#     """
#     Functionality: To read the file from mentioned file_path.
#     Exception: If file_path is incorrect raise an exception - "No such File found." and exit the program.
#     Parameters:
#         file_path - path of file to be read.
#     Returns:
#         Returns array of lines for data given in file.
#     """
#     log(f'File ~ {file_path}')
#     try:
#         with open(file_path, 'r') as file:
#             lines = file.readlines()
#             if len(lines) > 10 and lines[10].strip() == '':
#                 lines = lines[:10]
#         log('File data read.')
#     except FileNotFoundError:
#         log('No such File found.', 'ERROR')
#         sys.exit()
#     return lines

def log(mssg, logtype='OK'):
    '''Generates log message in predefined format.'''

    # Format for log message
    # #print(f'log : [{logtype}]:{mssg}')
    if logtype == 'ERROR':
        path = sys.argv[1]
        write_hindi_test(' ', 'Error', mssg, 'test.csv', path)

def write_hindi_text(hindi_output, POST_PROCESS_OUTPUT, OUTPUT_FILE):
    """Append the hindi text into the file"""
    
    with open(OUTPUT_FILE, 'w') as file:
        file.write(POST_PROCESS_OUTPUT)
        file.write('\n')
        file.write(hindi_output)
        # log('Output data write successfully')
        # #print(hindi_output)
    return "Output data write successfully"

def write_hindi_text_list(hindi_output, post_process_output, output_file):
    """
    Append the Hindi text into the file after processing the post-processing output.

    Parameters:
    hindi_output (str): The Hindi text to be written to the file.
    post_process_output (str): The processed output that includes delimiters.
    output_file (str): The path to the file where the text will be written.
    """
    # Split the post_process_output based on '/'
    parts = hindi_output.split('/')
    
    # Extract the sentence part (the last part)
    sentence = parts[-1].strip()
    
    # Extract the markers from the remaining parts
    markers = [part.strip() for part in parts[:-1]]
    
    # Generate the output variations
    output_variations = [f"{marker} {sentence}" for marker in markers]
    
    # #print the variations for debugging
    # #print(output_variations)
    
    # Write the processed and Hindi output to the file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(post_process_output)
        file.write('\n')
        file.write('\n'.join(output_variations))
    # #print(output_variations)
    # #print the written Hindi output for confirmation
    # #print("Hindi output written successfully.")
    
    return "Output data written successfully"

def write_hindi_test(hindi_output, POST_PROCESS_OUTPUT, src_sentence, OUTPUT_FILE, path):
    """Append the hindi text into the file"""
    OUTPUT_FILE = 'TestResults.csv'# temporary for presenting
    str = path.strip('lion_story/')
    if str == '1':
        with open(OUTPUT_FILE, 'w') as file:
            file.write("")

    with open(OUTPUT_FILE, 'a') as file:
        file.write(path.strip('../hindi_gen/lion_story') + '\t')
        file.write(src_sentence.strip('"').strip('\n').strip('#') + '\t')
        file.write(POST_PROCESS_OUTPUT + '\t')
        file.write(hindi_output + '\t')
        file.write('\n')
        # log('Output data write successfully')
    return "Output data write successfully"

def write_masked_hindi_test(hindi_output, POST_PROCESS_OUTPUT, src_sentence, masked_data, OUTPUT_FILE, path):
    """Append the hindi text into the file"""
    OUTPUT_FILE = 'TestResults_masked.csv'  # temporary for presenting
    with open(OUTPUT_FILE, 'a') as file:
        file.write(path.strip('lion_story/') + ',')
        file.write(src_sentence.strip('#') + ',')
        file.write(POST_PROCESS_OUTPUT + ',')
        file.write(hindi_output + ',')
        file.write(masked_data)
        file.write('\n')
        # log('Output data write successfully')
    return "Output data write successfully"

# def masked_postposition(processed_words, words_info, processed_verbs):
#     '''Calculates masked postposition to words wherever applicable according to rules.'''
#     masked_PPdata = {}

#     for data in processed_words:
#         if data[2] not in ('p', 'n', 'other'):
#             continue
#         data_info = getDataByIndex(data[0], words_info)
#         try:
#             data_case = False if data_info == False else data_info[4].split(':')[1].strip()
#         except IndexError:
#             data_case = False
#         ppost = ''
#         ppost_value = '<>'
#         # if data_case in ('k1', 'pk1'):
#         #     if findValue('yA', processed_verbs, index=6)[0]:  # has TAM "yA"
#         #         if findValue('k2', words_info, index=4)[0]: # or findExactMatch('k2p', words_info, index=4)[0]:
#         #             ppost = ppost_value
#         # if data_case in ('r6', 'k3', 'k5', 'k5prk', 'k4', 'k4a', 'k7t', 'jk1','k7', 'k7p','k2g', 'k2','rsk', 'ru' ):
#         #     ppost = ppost_value
#         if data_case in ('k7','k7t','k7p','k2p'):
#             ppost = ppost_value
#         elif data_case == 'krvn' and data_info[2] == 'abs':  #abstract noun as adverb
#             ppost = ppost_value
#         elif data_case in ('k2g', 'k2') and data_info[2] in ("anim", "per"):
#             ppost = ppost_value #'ko'
#         elif data_case in ('rsm', 'rsma','k7a'):
#             ppost = ppost_value+ ' ' + ppost_value #ke pAsa
#         elif data_case == 'rt':
#             # ppost = ppost_value+ ' ' + ppost_value #'ke lie'
#             ppost = ppost_value
#         elif 'rask' in data_case:
#             # ppost = ppost_value+ ' ' + ppost_value #ke sath
#             ppost = ppost_value
#         elif data_case == 'rv':
#             ppost = ppost_value+ ' ' + ppost_value + ' ' + ppost_value#'kI tulanA meM'
#         elif data_case == 'r6':
#             ppost = ppost_value # 'kI' if data[4] == 'f' else 'kA'
#             nn_data = nextNounData(data[0], words_info)
#             if nn_data != False:
#                 if nn_data[4].split(':')[1] in ('k3', 'k4', 'k5', 'k7', 'k7p', 'k7t', 'mk1', 'jk1', 'rt'):
#                     ppost = ppost_value
#                 elif nn_data[3][1] != 'f' and nn_data[3][3] == 'p':
#                     ppost = ppost_value#'ke'
#                 else:
#                     pass
#         else:
#             pass
#         if data[2] == 'p':
#             temp = list(data)
#             temp[7] = ppost if ppost != '' else 0
#             data = tuple(temp)
#         if data[2] == 'n' or data[2] == 'other':
#             temp = list(data)
#             temp[8] = ppost if ppost != '' else None
#             data = tuple(temp)
#             masked_PPdata[data[0]] = ppost
#     # #print(masked_PPdata,'mppp')
#     return masked_PPdata

def clean(word, inplace=''):
    """
    Clean concept words by removing numbers and special characters from it using regex.
    >>> clean("kara_1-yA_1")
    'karayA'
    >>> clean("kara_1")
    'kara'
    >>> clean("padZa_1")
    'pada'
    >>> clean("caDZa_1")
    'caDa'
    """
    # Replace specific patterns
    word = word.replace('dZ', 'd').replace('jZ', 'j').replace('DZ', 'D')
    # Remove numbers and special characters
    return re.sub(r'[^a-zA-Z]+', inplace, word)

# def process_files(input_filename):
#     # Read input from file
#     with open(input_filename, 'r', encoding='utf-8') as infile:
#         input_text = infile.read()
    
#     # Convert the input to output
#     output_text = convert_vert_to_csv(input_text)
#     # Write the output to a file
#     with open(input_filename, 'w', encoding='utf-8') as outfile:
#         outfile.write(output_text)
    # return output_text
def process_sentence(segment_ids,sentences, all_output):
    # Create a dictionary to hold the output
    if len(segment_ids)>1 and len(segment_ids)==len(all_output):
        for segment_id, output in zip(segment_ids, all_output):
            if segment_id and output:
                    sentences.append({
                        "segment_id": segment_id,
                        "text": output
                    })
            # current_segment_id = None
            # current_text = None
        output = {
            "bulk": sentences
        }
    else:
        output = {
            "sentence_id": segment_ids,
            "text": all_output
        }
    # #print the JSON output
    # #print(json.dumps(output, ensure_ascii=False, indent=2))
    # Convert the dictionary to a JSON string
    json_output = json.dumps(output, ensure_ascii=False)
    return json_output

def convert_vert_to_csv(input_text):
    # Split the input text into lines
    lines = input_text.strip().splitlines()
    
    # Extract the first line (segment_id)
    segment_id = lines[0].strip()
    # #print(segment_id)
    # Extract the second line (sentence)
    sentence = lines[1].strip()
    if "<segment_id=" in segment_id:  # Extract sentence id
        segment_id = segment_id.split('=')[1].strip('>')  # Extract everything after '=' and remove '>'
    # Initialize lists to store the columns
    words, indices, entities, extra_column1, extra_column2, extra_column3, extra_column4, extra_column5, extra_column6 = ([] for _ in range(9))
    # #print(columns)
    # Process each line of the table data (ignore the first and last lines)
    for line in lines[2:-2]:
        columns = line.split()
        words.append(columns[0]) 
         # word
        indices.append(columns[1])  # index
        entities.append(columns[2] if columns[2] != '-' else '')  # entity
        
        # Check each extra column and replace '-' with empty string
        extra_column1.append(columns[3] if columns[3] != '-' else '')
        extra_column2.append(columns[4] if columns[4] != '-' else '')
        extra_column3.append(columns[5] if columns[5] != '-' else '')
        extra_column4.append(columns[6] if columns[6] != '-' else '')
        extra_column5.append(columns[7] if columns[7] != '-' else '')
        extra_column6.append(columns[8] if len(columns) > 8 and columns[8] != '-' else '')

    # Extract the last line (marker) before the final closing tag
    last_line_marker = lines[-2].strip()
    
    # Create a list of output strings (each line as a separate string)
    output = [
        sentence,
        ','.join(words),
        ','.join(indices),
        ','.join(entities),
        ','.join(extra_column1),
        ','.join(extra_column2),
        ','.join(extra_column3),
        ','.join(extra_column4),
        ','.join(extra_column5),
        ','.join(extra_column6),
        last_line_marker,
    ]
    
    return output,segment_id

def generate_rulesinfo(file_data):
    '''
    Functionality: Extract all rows of USR, remove spaces from Running and end and break the entire row on the basis of comma and convert into list of strings.
    Exception: If length of file_data array is less than 10 raise an exception - Invalid USR. USR does not contain 10 lines.' and exit the program.
    Parameters:
        file_data - This is an array of lines read from input file.
    Returns:
        Return list of rows of USR as list of lists.
    '''

    if len(file_data) < 10:
        log('Invalid USR. USR does not contain 10 lines.', 'ERROR')
        sys.exit()

    src_sentence = file_data[0]
    root_words = file_data[1].strip().split(',')
    index_data = file_data[2].strip().split(',')
    seman_data = file_data[3].strip().split(',')
    gnp_data = file_data[4].strip().split(',')
    depend_data = file_data[5].strip().split(',')
    discourse_data = file_data[6].strip().split(',')
    spkview_data = file_data[7].strip().split(',')
    scope_data = file_data[8].strip().split(',')
    construction_data=file_data[9].strip().split(',')
    sentence_type = file_data[10].strip()
    # construction_data = ''
    # if len(file_data) > 10:
    #     construction_data = file_data[10].strip()

    log('Rules Info extracted succesfully fom USR.')
    # #print('generate_rulesinfo : ',[src_sentence, root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data,
            # scope_data, sentence_type, construction_data])
    return [src_sentence, root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data,
            scope_data, construction_data,sentence_type]

def populate_spkview_dict(spkview_info,index_data):
    populate_spk_dict = False
    a = 'after'
    b = 'before'
    for i, info in enumerate(spkview_info):
        clean_spk_info = info.rstrip('_1234567890')
        if clean_spk_info in application.repository.constant.spkview_list_b or clean_spk_info in application.repository.constant.spkview_list_a or clean_spk_info == 'result':
            populate_spk_dict = True
            if clean_spk_info in application.repository.constant.spkview_list_a:
                temp = (a, clean_spk_info)
                spkview_dict[index_data[i]] = [temp]
            else:
                temp = (b, clean_spk_info)
                spkview_dict[index_data[i]] = [temp]
    return populate_spk_dict

def generate_wordinfo(root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data,
                      scope_data,construction_data):
    '''
    Functionality:
        1. To check USR format
        2. Combine each concept with its corresponding information at the same index in all rows in tuples. Group all these tuples as word_info list.

    Parameters:
        1. root_words - second row of USR. Contains all concepts/ root words
        2. index_data - third row of USR. Contains indexing of concepts from 1, 2, 3 and onwards
        3. seman_data - fourth row of USR. Contains semantic information about all concepts
        4. gnp_data - fifth row of USR. Contains number information of the concept
        5. depend_data - sixth row of USR. Contains dependency information of the concept
        6. discourse_data - seventh row of USR. Contains discourse information of the concept
        7. spkview_data - eighth row of USR. Contains speaker's view information of the concept
        8. scope_data - ninth row of USR. Contains scope information of the concept

    Returns:
        Generates an array of tuples containing word and its USR info i.e USR info word wise.
        '''
    return list(
        zip(index_data, root_words, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data,construction_data))
    # return check_USR_format(root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data)

def check_USR_format(root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data,
                      scope_data):
    '''
    Functionality:
    1. To check if root words and their indices are in order
    2. To ensure that all the tuples of the USR have same number of enteries

    Returns:
        Corrected USR as an array of tuples containing word and its USR info (corresponding value on same index in each row) i.e USR info word wise.
    '''
    data = [root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data]
    len_root = len(root_words)
    len_index = len(index_data)

    if len_root > len_index:
        diff = len_root - len_index
        while diff:
            index_data.append(0)
            diff = diff - 1
            log(f'{application.repository.constant.USR_row_info[1]} has lesser enteries as compared to {application.repository.constant.USR_row_info[0]}')

    elif len_root < len_index:
        diff = len_index - len_root
        while diff:
            index_data.pop()
            diff = diff - 1
            log(f'{application.repository.constant.USR_row_info[1]} has more enteries as compared to {application.repository.constant.USR_row_info[0]}')

    #once the lengths of root_words and index_data are equal check value of each index
    len_root = len(root_words)
    len_index = len(index_data)
    if len_root == len_index:
        for i in range(1, len_root + 1):
            if index_data[i - 1] == i:
                continue
            else:
                index_data[i - 1] = i
                log(f'{application.repository.constant.USR_row_info[1]} has wrong entry at position {i}')

    #Checking all tuples have same number of enteries
    max_col = max(index_data)
    i = 0
    for ele in data:
        length = len(ele)
        if length < max_col:
            diff = max_col - length
            while diff:
                ele.append('')
                log(f'Added one entry at the end of {application.repository.constant.USR_row_info[i]}')
                diff = diff - 1
        elif length > max_col:
            diff = length - max_col
            while diff:
                ele.pop()
                log(f'Removed one entry from the end of {application.repository.constant.USR_row_info[i]}')
                diff = diff - 1
        i = i + 1

    #Removing spaces if any,before/ after each ele for all rows in USR
    for row in data:
        for i in range(0, len(row)):
            if type(row[i]) != int and row[i] != '':
                temp = row[i].strip()
                row[i] = temp

    return list(
        zip(index_data, root_words, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data))

def identify_cat(words_list):
    '''
    Functionality: There are various categorizations of the concepts such as - nouns, pronouns etc. This function Checks word for its type to process
    accordingly and add that word to its corresponnding list.

    Parameters:
        1. words_list: It is an array of tuples. Each tuple consists of concept wise USR info.

    Returns:
        All the categorized lists of nouns, pronouns etc. with input concept tuple appended in it

    For eg.
        #jaMgala meM eka Sera WA.
        jaMgala_1, Sera_1, hE_1-past
        1,2,3
        ,anim male,
        sg,,
        3:k7p, 3:k1,0:main
        ,,
        def,,
        ,,
        affirmative

    Result -
        indeclinables = []
        pronouns = []
        nouns = [(1, 'jaMgala_1', '', 'sg', '3:k7p', '', 'def', ''), (2, 'Sera_1', 'anim male', '', '3:k1', '', '', '')]
        adjectives = []
        verbs = [(3, 'hE_1-past', '', '', '0:main', '', '', '')]
        adverbs = []
        others = []
        nominal_verbs = []
    '''
    foreign_words=[]
    indeclinables = []
    pronouns = []
    nouns = []
    verbal_adjectives = []
    adjectives = []
    verbs = []
    others = []
    adverbs = []
    nominal_verb = []
    for word_data in words_list:
        # if clean(word_data[1]) in ('cp','conj','disjunct','span','widthmeas','depthmeas','distmeas','rate','timemeas','waw','calender','massmeas','heightmeas','spatial','xvanxva','compound'):
        #     del(word_data)
        if check_foreign_words(word_data):
            log(f'{word_data[1]} identified as foreign word.')
            foreign_words.append(word_data)
        elif check_indeclinable(word_data):
            log(f'{word_data[1]} identified as indeclinable.')
            indeclinables.append(word_data)
        elif check_digit(word_data):
            log(f'{word_data[1]} identified as noun.')
            nouns.append(word_data)
        elif check_verb(word_data):
            log(f'{word_data[1]} identified as verb.')
            verbs.append(word_data)
        elif check_adjective(word_data):
            log(f'{word_data[1]} identified as adjective.')
            adjectives.append(word_data)
        # elif check_verbal_adjective(word_data):
        #     log(f'{word_data[1]} identified as adjective.')
        #     verbal_adjectives.append(word_data)
        elif check_pronoun(word_data):
            log(f'{word_data[1]} identified as pronoun.')
            pronouns.append(word_data)
        elif check_adverb(word_data):
            log(f'{word_data[1]} identified as adverb.')
            adverbs.append(word_data)
        elif check_nominal_verb(word_data):
            log(f'{word_data[1]} identified as nominal verb form.')
            nominal_verb.append(word_data)
        elif check_noun(word_data):
            log(f'{word_data[1]} identified as noun.')
            nouns.append(word_data)
        elif check_named_entity(word_data):
            log(f'{word_data[1]} identified as named entity and processed as other word.')
            others.append(word_data)
        else:
            log(f'{word_data[1]} identified as other word, but processed as noun with default GNP.')  # treating other words as noun
            nouns.append(word_data)
    return foreign_words,indeclinables, pronouns, nouns,verbal_adjectives, adjectives, verbs, adverbs, others, nominal_verb

def check_named_entity(word_data):
    if word_data[2] == 'ne':
        return True
    return False

def check_noun(word_data):
    '''
    Functionality:
        1. Check semantic data has place/ ne
        2. Check if GNP row has number info sg or pl

    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise

    For eg.     :
        #राम ने दो रोटी और दाल खायी।
        rAma,xo_1,rotI_1,xAla_1,KA_1-yA_1
        1,2,3,4,5,6
        male per,,,,
        sg,,sg,sg,
        6:k1,3:card,6:k2,6:k2,0:main
        ,,,,,
        ,,,,,
        ,,,,,
        affirmative
        conj:[3,4]

        word_data = (1, 'rAma', 'male per', 'sg', '6:k1', '', '', '')
        Result     : True (as word_data[3] == 'sg')
    '''

    try:
        # identifying nouns from sem_cat
        if word_data[2] in ('place','Place','ne','NE') and '^' not in word_data[1]:
            return True
        # GNP present for a concept
        # if 'kriyAmUla' in word_data[8]:
        #     return True
        if 'pl' == word_data[3]:
            return True
        return False
    except IndexError:
        log(f'Index Error for GNP Info. Checking noun for {word_data[1]}', 'ERROR')
        sys.exit()

def check_pronoun(word_data):
    '''
    Functionality:
        1. Check if the concept belongs to PRONOUN_TERMS list ('speaker', 'kyA', 'Apa', 'jo', 'koI' etc.)
        2. Check if dependency relation is not r6 and discourse data is coref

    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise

    For eg.     :
        #मैंने आज स्नान किया।
        speaker,Aja_1,snAna+kara_1-yA_1
        1,2,3
        anim male,,
        sg,,
        3:k1,3:k7t,0:main
        ,,
        ,,
        ,,
        affirmative

        word_data     : (1, 'speaker', 'anim male', 'sg', '3:k1', '', '', '')
    Result:
        True (as 'speaker' exists in PRONOUN_TERMS list)
    '''

    try:
        if clean(word_data[1]) in application.repository.constant.PRONOUN_TERMS:
            return True
        elif 'coref' in word_data[5]:
            if 'r6' not in word_data[4]: # for words like apanA
                return True
        else:
            return False
    except IndexError:
        log(f'Index Error for GNP Info. Checking pronoun for {word_data[1]}', 'ERROR')
        sys.exit()

def check_adjective(word_data):
    '''
    Functionality:
        1. Check if dependency data is any of the following - 'card', 'mod', 'meas', 'ord', 'intf'
        2. Check if dependency relation is k1s and does not have GNP info
        3. Check if dependency relation is r6 and discourse data is coref

    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise

    For eg.     :
        #राम ने दो रोटी और दाल खायी।
        rAma,xo_1,rotI_1,xAla_1,KA_1-yA_1
        1,2,3,4,5,6
        male per,,,,
        sg,,sg,sg,
        6:k1,3:card,6:k2,6:k2,0:main
        ,,,,,
        ,,,,,
        ,,,,,
        affirmative
        conj:[3,4]

        word_data     : (2, 'xo_1', '', '', '3:card', '', '', '')
    Result:
        True (as dependency relation is card)
    '''

    # Convert the tuple to a list
    word_data_list = list(word_data)

    if word_data_list[4] != '':
        rel = word_data_list[4].strip().split(':')[1]
        if rel=='mod' and (word_data_list[3]==('mawupa') or word_data_list[2]=='season'):
            return False
        if rel in application.repository.constant.ADJECTIVE_DEPENDENCY:
            return True
        if word_data_list[3] == '' and rel not in application.repository.constant.ADJECTIVE_DEPENDENCY and word_data_list[5] != '0:main':
            word_data_list[3] = 'sg'
        if rel == 'k1s' and word_data_list[3] == '': # k1s and no GNP -> adj
            return True
        if rel == 'k1s' and word_data_list[3] in ('compermore','comperless'): 
            return True
        

        # if word_data_list[5] != '':
        #     if ':' in word_data_list[5]:
        #         coref = word_data_list[5].strip().split(':')[1]
        #         if rel == 'r6' and coref == 'coref': # for words like apanA
        #             return True

    # Convert the list back to a tuple
    word_data = tuple(word_data_list)

    return False

def check_nonfinite_verb(word_data):
    '''Check if word is a non-fininte verb by the USR info'''

    if word_data[4] != '':
        rel = word_data[4].strip().split(':')[1]
        # if rel in ('rpk','rbk', 'rvks', 'rbks','rsk', 'rbplk'):
        if rel in ('rpk','rbk'):
            return True
    return False

def check_verb(word_data):
    '''
    Functionality:
        1. Check for both finite and non-finite verbs-
            nonfinite verbs     : checked by dependency
            main verb     : identified by '-' in it
    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise

    For eg.     :
        #मैंने आज स्नान किया।
        speaker,Aja_1,snAna+kara_1-yA_1
        1,2,3
        anim male,,
        sg,,
        3:k1,3:k7t,0:main
        ,,
        ,,
        ,,
        affirmative

        word_data     : (3, 'snAna+kara_1-yA_1', '', '', '0:main', '', '', '')
    Result:
        True (as '-' in 'snAna+kara_1-yA_1')

    '''
    # if '-' not in word_data[1]:
    #     rword = word_data[1]
    #     if rword in extract_tamdict_hin():
    #         return True
    if '-' in word_data[1]:
        rword = word_data[1].split('-')[1]
        sss=extract_tamdict_hin()
        # #print(sss)
        if rword in extract_tamdict_hin():
            return True
        else:
            log(f'Verb "{rword}" not found in TAM dictionary', 'WARNING')
            return False
    else:
        if word_data[4] != '':
            rel = word_data[4].strip().split(':')[1]
            if rel in application.repository.constant.NON_FINITE_VERB_DEPENDENCY:
                return True
    return False


def check_adverb(word_data):
    '''
    Functionality: Check for kr_vn/ krvn in dependency row.

    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise
    '''
    if word_data[4] != '':
        rel = word_data[4].strip().split(':')[1]
        if rel in ('kr_vn','krvn','vkvn','freq'):
            return True
    return False

def check_foreign_words(word_data):
    '''checks ^ is present infront of word 
    if it is present then it is a foreign word'''

    if word_data[1][0]=='^' and word_data[2]=='fw':        
        return True
    else:
        return False

def check_indeclinable(word_data):
    '''
    Functionality:
        Return True as indeclinable if:
        1. the semantic info of the concept is 'unit'
        2. Check if word is in INDECLINABLE_WORDS or UNITS list in repository.constant.py

    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise

    For eg.:
        #मैंने आज स्नान किया।
        speaker,Aja_1,snAna+kara_1-yA_1
        1,2,3
        anim male,,
        sg,,
        3:k1,3:k7t,0:main
        ,,
        ,,
        ,,
        affirmative

        word_data = (2, 'Aja_1', '', '', '3:k7t', '', '', '')

    Result:
        True (as Aja exists in repository.constant.INDECLINABLE_WORDS)

    '''
    if word_data[2] == 'unit':
        return True
    
    if (clean(word_data[1]) in application.repository.constant.UNITS or 
        word_data[8] and word_data[8].split(':')[1] in ('unit', 'per_unit') or 
        clean(word_data[1]) in application.repository.constant.INDECLINABLE_WORDS):
        return True
    return False

def check_digit(word_data):
    '''
    Functionality:
        Return True if:
        1. the concept has digits or float value

    Parameters:
        word_data: tuple of concept with all its information

    '''
    num = word_data[1]
    if '_' in num:
        num = num.strip().split('_')[0]
    if num.isdigit():
        return True
    else:
        try:
            float_value = float(num)
            return True
        except ValueError:
            return False
    return False

def check_nominal_verb(word_data):
    '''
    Functionality: Check if dependency value belongs to NOMINAL_VERB_DEPENDENCY list and there is no GNP information

    Parameters:
        word_data: tuple of concept with all its information

    Returns:
        True - if any of the above condition is met
        False - otherwise
    '''
    # if word_data[4].strip() != '':
    #     relation = word_data[4].strip().split(':')[1]
    #     gnp_info = word_data[3]
    #     if relation in repository.constant.NOMINAL_VERB_DEPENDENCY and gnp_info == '':
    #         return True
    # return False
    if word_data[4].strip() != '':
        relation = word_data[4].strip().split(':')[1]
        # gnp_info = word_data[3]
        term=clean(word_data[1])
        # #print(word_data[3],'vkl')
        #     return False
        
        tags = find_tags_from_dix_as_list(term)
        # #print(tags,term,'tags3')
        for tag in tags:
            if tag['cat'] =='v' and relation in application.repository.constant.NOMINAL_VERB_DEPENDENCY:
                # noun_type = category = 'vn'
                return True
                    # term += 'nA'
                # log(f'{term} processed as nominal verb with index {index} gen:{gender} num:{number} person:{person} noun_type:{noun_type} case:{case} and postposition:{postposition}')
                # break
    else:
        return False

def check_is_digit(num):
    if num.isdigit():
        return True
    else:
        try:
            float_value = float(num)
            return True
        except ValueError:
            return False
    return False

# def check_main_verb(depend_data):
    # flag=False
    # for dep in list(depend_data):
    #     if dep:
    #         dep1=dep.strip().split(':')[1]
    #         if dep1== 'main' or dep1=='rcelab' or dep1=='rcdelim':
    #             flag=True
    #             break
    # if flag==False:
    #     return(log('USR error. Main verb not identified. Check the USR.'))
        # sys.exit()
def check_main_verb(depend_data):
    for dep in depend_data:
        if dep:  # Check if dep is not empty
            dep_type = dep.strip().split(':')[1]  # Extract the type after splitting
            if dep_type in ('main', 'rcelab', 'rcdelim'):  # Check for main verb types
                return True  # Return immediately if a main verb is found

    # Log the error if no main verb was identified
    log('USR error. Main verb not identified. Check the USR.')
    return False

            
def convert_to_devanagari(text):
    # Convert English text to Devanagari script
    devanagari_text = sanscript.transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
    return devanagari_text
# def translate_to_hindi(text):
#     translator = Translator()
#     translated = translator.translate(text, src='en', dest='hi')
#     return translated.text

def process_foreign_word(index_data,foreign_words_data,words_info,verbs_data):
    # for verb in verbs_data:
    #    if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
    #         main_verb = verb
    #         break
    processed_foreign_words=[]
    flag=False
    for i,foreign_word in enumerate(foreign_words_data):
        index=foreign_word[0]
        gender, number, person, case = get_default_GNP()
        category='n'
        type=''
        foreign_list = list(foreign_word)
        # for main verb
        relation_head = foreign_word[4].strip().split(':')[0]
        relation = foreign_word[4].strip().split(':')[1]
        # if int(relation_head) in index_data and relation=='k1':
        main_verb,flag=process_construction_cp(relation_head,verbs_data,flag,index)
        # for verb in verbs_data:
        #     # if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
        #     v = relation_head + ':verbalizer'
        #     if v == verb[8]:
        #         # id = construction_data.index(v)
        #         main_verb=verb
        #         break
        #     elif int(relation_head)==verb[0]:
        #         main_verb=verb
        #         break
        # else:
        #     main_verb=verb
        
        foreign_list[1] = foreign_list[1].replace('^','')
        # if '_' in foreign_list[1]:
        foreign_list[1]=clean(foreign_list[1])
        foreign_list[1]=convert_to_devanagari(foreign_list[1])
        # foreign_list[1]=convert_to_hindi(foreign_list[1])
        foreign_word = tuple(foreign_list)
        case,postposition = preprocess_postposition_new('noun', foreign_word, words_info, main_verb,index_data)
        if flag:
            del processed_postpositions_dict[float(index)]
        processed_foreign_words.append((index,foreign_word[1],category,case,gender,number,person,type,postposition))
        
    return processed_foreign_words

def convert_to_hindi(word):
    # wx = WXC(order='wx2utf', lang='hin')
    wx1 = WXC(order='utf2wx', lang='hin')
    hindi_text_list = wx1.convert(word)
    return hindi_text_list

def preprocess_postposition_new(concept_type, np_data, words_info, verb_data, index_data):
    '''Calculates postposition to words wherever applicable according to rules.'''
    cp_verb_list = ['prayApreprsa+kara','sahAyawA+kara']
    
    if len(verb_data) > 0:
        verb_term = verb_data[1]
        if len(verb_term) > 0:
            root_main = verb_term.strip().split('-')[0].split('_')[0]
    if np_data != ():
        data_case = np_data[4].strip().split(':')[1]
        data_case_for_k4.append(np_data[4])
        data_head = np_data[4].strip().split(':')[0]
        data_index = np_data[0]
        ind_in_index_data = index_data.index(data_index)
        data_seman = np_data[2]
    ppost = ''
    new_case = 'o'
    # #print(np_data,'nnnn')
    if data_case in ('k1', 'pk1'):
        if is_tam_ya(verb_data): # has TAM "yA" or "yA_hE" or "yA_WA" marA WA
            k2exists, k2_index = find_match_with_same_head(data_head, 'k2', words_info, index=4) # or if CP_present, then also ne - add #get exact k2, not k2x
            # vk2exists, vk2_index = find_match_with_same_head(data_head, 'vk2', words_info, index=4)
            if k2exists:
                ppost = 'ne'
                # if is_CP(verb_term):
                #     cp_parts = verb_term.strip().split('+')
                #     clean_cp_term = ''
                #     for part in cp_parts:
                #         part = part.split("-")[0]
                #         clean_cp_term = clean_cp_term + clean(part) + '+'
                #     clean_cp_term = clean_cp_term[0:-1]
                #     if clean_cp_term in cp_verb_list:
                #         update_additional_words_dict(k2_index, 'after', 'kA')
            # elif vk2exists:
            #     ppost = 'ne'
            else:
                ppost = ''
                log('Karma k2 not found. Output may be incorrect')

        elif identify_complete_tam_for_verb(verb_term) in application.repository.constant.nA_list:
            ppost = 'ko'
        else:
            log('inside tam ya else')

    elif data_case=='mod' and data_seman=='season':
        ppost = 'kA'
        nn_data = nextNounData(data_head, words_info)
        # #print(nn_data,'nndl')
        if nn_data != False:
            if nn_data[4].split(':')[1] in ('k3', 'k4', 'k5', 'k7', 'k7p', 'k7t', 'r6', 'mk1', 'jk1', 'rt'):
                ppost = 'ke'
                if nn_data[3] == 's':#agreement with gnp
                    if nn_data[3] == 'f':
                        ppost = 'kI'
                    else:
                        ppost = 'kA'
                else:
                    pass
    elif data_case == 'k2g':
        ppost = process_dep_k2g(data_case, verb_data)
    elif data_case == 'k2': #if CP present, and if concept is k2 for verb of CP, and the verb is not in specific list, then kA
        if data_seman and data_seman!=''and data_seman.split()[0] in ("anim", "per"):
            check_k4=data_head+':k4'
            # check_k7t=data_head+':k7t'
            if clean(root_main) in application.repository.constant.reciprocal_verbs:
                ppost = 'se'
            elif check_k4 not in data_case_for_k4:
                ppost = 'ko'
        else:
            new_case = 'd'

    # elif data_case in ('k2p','k7','k7p','k7t','rt'):
    #     # ppost = '' 
    #     ppost = '<>'
    elif data_case in ('k2p'):
        ppost = '' # modified from meM 22/06
    elif data_case in ('k3', 'k5', 'k5prk'):
        ppost = 'se'
    elif data_case in ('k4', 'k4a', 'jk1'):
        ppost = 'ko'
    elif data_case == 'k7t' and np_data[2]=='timex':
        ppost = 'para'
    elif data_case == 'k7t' and clean(np_data[1]) not in ['kala','subaha','Aja','aBI','pahale']:
        ppost = 'ko'
    elif data_case == 'k7':
        ppost = 'meM'
    elif data_case =='k7p':
        ppost = 'para'
    elif data_case =='k7a':
        ppost = 'ke anusAra'
    elif data_case == 'krvn' and data_seman == 'abs':
        ppost = 'se'
    elif data_case == 'rt':
        ppost = 'ke liye'
    elif data_case == 'rblak':
        ppost = 'ke bAxa'
    elif data_case == 'rblsk':
        ppost = 'we samaya'
    # elif data_case == 'rblsk':
    #     ppost = 'we samaya'
    elif data_case == 'rblpk':
        ppost = 'se pahale'
    elif data_case in ('rsm', 'rsma'):
        ppost = 'ke pAsa'
    elif data_case == 'rhh':
        ppost = 'ke'
    elif data_case == 'rsk':
        ppost = 'hue'
    elif data_case == 'rn':
        ppost = 'meM'
    elif data_case == 'rib':
        ppost = 'se'
    elif data_case == 'rasneg':
        ppost = 'ke binA'
    elif data_case == 'ru':
        ppost = 'jEsI'
    elif data_case == 'rkl':
        next_word = fetchNextWord(ind_in_index_data + 1, words_info)
        if next_word == 'bAxa':
            ppost = 'ke'
        elif next_word == 'pahale':
            ppost = 'se'

    elif data_case == 'rdl':
        next_word = fetchNextWord(ind_in_index_data + 1, words_info)
        if next_word in ('anxara', 'bAhara', 'Age', 'sAmane', 'pICe', 'Upara', 'nIce', 'xAyeM',
                         'bAyeM', 'cAroM ora', 'bIca', 'pAsa','uparI'):
            ppost = 'ke'
        elif next_word == 'xUra':
            ppost = 'se'

    elif data_case == 'rv':
        ppost = 'se'
    elif data_case == 'mk1':
        ppost = 'se'
    elif data_case == 'rh':
        ppost = 'ke_kAraNa'
    elif data_case == 'rd':
        ppost = 'kI ora'
    elif data_case == 'rp':
        ppost = 'se hokara'
    # elif 'rask7' in data_case:
    #     ppost = 'sahiwa'
    elif 'rask' in data_case:
        ppost = 'ke sAWa'
    elif data_case == 'r6':
        ppost = 'kA' #if data[4] == 'f' else 'kA'
        nn_data = nextNounData(data_head, words_info)
        if nn_data != False:
            if nn_data[4].split(':')[1] in ('k3', 'k4', 'k5', 'k7', 'k7p', 'k7t', 'r6', 'mk1', 'jk1', 'rt'):
                ppost = 'ke'
                if nn_data[3] == 's':#agreement with gnp
                    if nn_data[3] == 'f':
                        ppost = 'kI'
                    else:
                        ppost = 'kA'
                else:
                    pass
    elif data_case == 'quantless':
        ppost = 'se kama'
    elif data_case == 'quantmore':
        ppost = 'se aXika'
    else:
        pass
    if ppost == '':
        new_case = 'd'

    if concept_type == 'noun':
        if ppost == '':
            ppost = None
        processed_postpositions_dict[data_index] = ppost

    if concept_type == 'pronoun':
        if ppost == '':
            ppost = 0
        processed_postpositions_dict[data_index] = ppost
    return new_case, ppost

def process_nominal_verb(index_data,nominal_verbs_data, processed_noun, words_info, verbs_data):

   nominal_verbs = []
   flag=False
#    for verb in verbs_data:
#        if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
#             main_verb = verb
#             break
    
   for nominal_verb in nominal_verbs_data:
        index = nominal_verb[0]
        term = clean(nominal_verb[1])
        gender = 'm'
        number = 's'
        person = 'a'
        # category = 'n'
        noun_type = 'common'
        case = 'o'
        postposition = ''
        log_msg = f'{term} identified as nominal, re-identified as other word and processed as common noun with index {index} gen:{gender} num:{number} person:{person} noun_type:{noun_type} case:{case} and postposition:{postposition}'

        relation = ''
        if nominal_verb[4] != '':
            relation = nominal_verb[4].strip().split(':')[1]

        relation_head = nominal_verb[4].strip().split(':')[0]
        # relation = nominal_verb[4].strip().split(':')[1]
        # if int(relation_head) in index_data and relation=='k1':
        main_verb,flag=process_construction_cp(relation_head,verbs_data,flag,index)
        # for verb in verbs_data:
        #     # if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
        #     v = relation_head + ':verbalizer'
        #     if v == verb[8]:
        #         # id = construction_data.index(v)
        #         main_verb=verb
        #         break
        #     elif int(relation_head)==verb[0]:
        #         main_verb=verb
        #         break
        # else:
        #     main_verb=verb
        # verb = Verb()

        # verb.type = 'nonfinite'
        # verb.tam = ''
        # tam=''
        # tam = set_tam_for_nonfinite(relation)

        case, postposition = preprocess_postposition_new('noun', nominal_verb, words_info, main_verb, index_data)
        # #print(processed_postpositions_dict,index,flag,'klllll')
        if flag:
            del processed_postpositions_dict[float(index)]
        # tags = find_tags_from_dix_as_list(term)
        # for tag in tags:
        #     if (tag[0] == 'cat' and tag[1] == 'v'):
        noun_type = 'vn'
        category='vn'
        if relation in ('k2', 'rt', 'rh','rblpk','rblak','rblsk'):
            term = term + 'nA'
            log_msg = f'{term} processed as nominal verb with index {index} gen:{gender} num:{number} person:{person} noun_type:{noun_type} case:{case} and postposition:{postposition}'
            noun = (index, term, category, case, gender, number, person, noun_type, postposition)
            processed_noun.append(noun)
            log(log_msg)
            # break
        elif relation in ('k1'):
            case='d'
            term = term + 'nA'
            log_msg = f'{term} processed as nominal verb with index {index} gen:{gender} num:{number} person:{person} noun_type:{noun_type} case:{case} and postposition:{postposition}'
            noun = (index, term, category, case, gender, number, person, noun_type, postposition)
            processed_noun.append(noun)
            log(log_msg)
            # break

        noun = (index, term, category, case, gender, number, person, noun_type, postposition)
        # processed_noun.append(noun)
        # nominal_verbs.append(noun)
        
   return processed_noun

def process_adverb_as_noun(concept, processed_nouns):
    index, term, *_ = concept
    case = 'd' if ('+se_') not in term else 'o'
    term = clean(term.split('+')[0])
    category, gender, number, person, noun_type, postposition = 'n', 'm', 'p', 'a', 'abstract', 'se'
    processed_postpositions_dict[index] = postposition
    noun = (index, term, category, case, gender, number, person, noun_type, postposition)
    processed_nouns.append(noun)
    log(f' Adverb {term} processed as an abstract noun with index {index} gen:{gender} num:{number} case:{case},noun_type:{noun_type} and postposition:{postposition}')
    return

def process_adverb_as_verb(concept, processed_verbs):
    index, term, *_ = concept
    term = clean(term)
    gender, number, person, category, type, case = 'm', 's', 'a', 'v', 'adverb', 'd'
    tags = find_tags_from_dix_as_list(term)
    # #print(tags,'tags5')
    for tag in tags:
        if tag['cat']== 'v':
            tam = 'kara'
            adverb = (index, term, category, gender, number, person, tam, case, type)
            processed_verbs.append(adverb)
            log(f'{term} adverb processed as a verb with index {index} gen:{gender} num:{number} person:{person}, and tam:{tam}')
            return

def process_adverbs(adverbs, processed_nouns, processed_verbs, processed_indeclinables, reprocessing):
    for adverb in adverbs:
        term = clean(adverb[1])
        if '+se_' in term or adverb[2] == 'abs':  # for adverbs like jora+se
            if not reprocessing:
                process_adverb_as_noun(adverb, processed_nouns)
        else:  # check morph tags
            tags = find_tags_from_dix_as_list(term)
            # #print(tags,'tags4')
            for tag in tags:
                if tag['cat']== 'v':  # term type is verb in morph dix
                    return process_adverb_as_verb(adverb, processed_verbs)
                elif tag['cat']== 'adj':  # term type is adjective in morph dix
                    term += 'rUpa se'
                    processed_indeclinables.append((adverb[0], term, 'indec'))
                    log(f'adverb {adverb[1]} processed indeclinable with form {term}')
            else:
                for processed in processed_indeclinables:
                    if term == processed[1]:
                        log(f'adverb {adverb[1]} already processed indeclinable, no processing done')
                        return
                processed_indeclinables.append((adverb[0], term, 'indec'))  # to be updated, when cases arise.
                log(f'adverb {adverb[1]} processed indeclinable with form {term}, no processing done')
                return

def process_indeclinables(indeclinables):
    '''
    Functionality:
        1. They do not require any furthur processing
        2. Make a tuple with - index, term, type(indec)

    Parameters:
        indeclinables: List of indeclinable data

    Returns:
        list of tuples.

    for eg.     :
        indeclinables: [(2, 'Aja_1', '', '', '3:k7t', '', '', '')]

    Result:
       processed_indeclinables: [(2, 'Aja', 'indec')]
    '''

    processed_indeclinables = []
    for indec in indeclinables:
        clean_indec = clean(indec[1])
        processed_indeclinables.append((indec[0], clean_indec, 'indec'))
    return processed_indeclinables

def process_nouns(index_data,seman_data,nouns, words_info, verbs_data):
    '''
    Functionality:
        1. Make a noun tuple
        2. We update update_additional_words_dict(index, 'before', 'eka'), if number == 's' and noun[6] == 'some'

    Parameters:
        1. nouns - List of noun data
        2. words_info - List of USR info word wise
        3. verbs_data - List of verbs data

    Returns:
        processed_nouns = List of noun tuples where each tuple looks like - (index, word, category, case, gender, number, proper/noun type= proper, common, NC, nominal_verb, CP_noun or digit, postposition)

    For eg.:
        rAma,xo_1,rotI_1,xAla_1,KA_1-yA_1
        1,2,3,4,5,6
        male per,,,,
        sg,,sg,sg,
        6:k1,3:card,6:k2,6:k2,0:main
        ,,,,,
        ,,,,,
        ,,,,,
        affirmative
        conj:[3,4]

        nouns     : [(1, 'rAma', 'male per', 'sg', '6:k1', '', '', ''), (3, 'rotI_1', '', 'sg', '6:k2', '', '', ''), (4, 'xAla_1', '', 'sg', '6:k2', '', '', '')]
        words_info     : [(1, 'rAma', 'male per', 'sg', '6:k1', '', '', ''), (2, 'xo_1', '', '', '3:card', '', '', ''), (3, 'rotI_1', '', 'sg', '6:k2', '', '', ''), (4, 'xAla_1', '', 'sg', '6:k2', '', '', ''), (5, 'KA_1-yA_1', '', '', '0:main', '', '', '')]
        verbs_data     : [(5, 'KA_1-yA_1', '', '', '0:main', '', '', '')]

    Result:
        processed_nouns     : [(1, 'rAma', 'n', 'o', 'm', 's', 'a', 'proper', 'ne'), (3, 'rotI', 'n', 'd', 'f', 's', 'a', 'common', None), (4, 'xAla', 'n', 'd', 'f', 's', 'a', 'common', None)]
    '''

    processed_nouns = []
    main_verb = ''
    flag=False
    # for verb in verbs_data:
    #     if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
    #         main_verb = verb
    #         #print(main_verb,'vbb')
            # break
    # if not len(main_verb):
    #     log('USR error. Main verb not identified. Check the USR.')
    #     sys.exit()
        # return None
    

    for noun in nouns:
        category = 'n'
        index = noun[0]
        # dependency = noun[4].strip().split(':')[1]
        gender, number, person = extract_gnp_noun(noun)
        # #print(noun)
        relation_head = noun[4].strip().split(':')[0]
        # relation = noun[4].strip().split(':')[1]
        # if int(relation_head) in index_data and relation=='k1':
        
        main_verb,flag=process_construction_cp(relation_head,verbs_data,flag,index)
        # for verb in verbs_data:
        #     if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
        #         v = relation_head + ':verbalizer'
        #         # #print(verb,relation_head,noun,'vbb')
        #         if v == verb[8]:
        #             # id = construction_data.index(v)
        #             main_verb=verb
        #             break
        #         elif relation_head and int(relation_head)==verb[0]:
        #             main_verb=verb
        #             break
        #         else:
        #             main_verb=verb
        # else:
        #     for verb in verbs_data:
        #         if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
        #             main_verb = verb
        #             #print(main_verb,'vbb')
        #             break
        # #print(main_verb,'vbbb')
        # for verb in verbs_data:
        #     v = relation_head + ':verbalizer'
        #     if int(relation_head)==verb[0]:
        #             main_verb=verb
        #     elif v == verb[8]:
        #         # id = construction_data.index(v)
        #         main_verb=verb

        if noun[6] == 'respect': # respect for nouns
            number = 'p'
        noun_type = 'common' if '_' in noun[1] else 'proper'

        # if 'kriyAmUla' in noun[8]:
        if clean(noun[8]) in ('start','end','kriyAmUla','mod','whole','count'):
            case='d'
            postposition=None
        else:
            case, postposition = preprocess_postposition_new('noun', noun, words_info, main_verb, index_data)

        if '+' in noun[1]:
            processed_nouns = handle_compound_nouns(noun, processed_nouns, category, case, gender, number, person, postposition)

        else:
            term = noun[1]
            if check_is_digit(term):
                if '_' in term:
                    clean_noun = term.strip().split('_')[0]
                else:
                    clean_noun = term
                noun_type = 'digit'
            else:
                clean_noun = clean(noun[1])

            if number == 's' and noun[6] == 'some':
                update_additional_words_dict(index, 'before', 'eka')
            # #print(seman_data,noun[2],'seem')
            # if ('era' in seman_data and noun[2] in ('dom', 'moy', 'yoc')) or \
            #     ('yoc' in seman_data and noun[2] in ('dom', 'moy')) or \
            #     ('moy' in seman_data and noun[2] == 'dom'):
            #     #print('ver')
            #     postposition = None
            if 'era' == noun[2]:
                clean_noun = clean_noun.replace('00','')
                clean_noun=clean_noun +'_vIM_saxI'
                
            # if 'mod' in noun[8]:
            #     postposition=None
            #     processed_postpositions_dict[index] = postposition
            #     case='d'

            if 'era' in seman_data and noun[2] in ('dom','moy','yoc'):
                postposition=None
                processed_postpositions_dict[index] = postposition
                case='d'
            elif 'yoc' in seman_data and noun[2] in ('dom','moy'):
                postposition=None
                processed_postpositions_dict[index] = postposition
                case='d'
            elif 'moy' in seman_data and noun[2] in ('dom'):
                postposition=None
                processed_postpositions_dict[index] = postposition
                case='d'
            elif all(item not in seman_data for item in ('era', 'moy', 'yoc')) and noun[2] == 'dom':
                clean_noun = clean_noun+ '_wArIKa'
            if noun[2]=='clocktime':
                clean_noun = clean_noun + '_baje'
            # #print(postposition,'pppps')
            # if float(index) in processed_postpositions_dict:
            #     del processed_postpositions_dict[float(index)]
            if clean(noun[1]) in ('cp', 'conj', 'disjunct', 'span', 'widthmeas', 'depthmeas', 'distmeas', 'rate', 'timemeas', 'waw', 'calender', 'massmeas', 'heightmeas', 'spatial'):
                postposition=None
                del processed_postpositions_dict[index]
            processed_nouns.append((noun[0], clean_noun, category, case, gender, number, person, noun_type, postposition))
        log(f'{noun[1]} processed as noun with case:{case} gen:{gender} num:{number} noun_type:{noun_type} postposition: {postposition}.')
    return processed_nouns

def process_pronouns(index_data,pronouns, processed_nouns, processed_indeclinables, words_info, verbs_data):
    '''
        Functionality:
            1. Make a pronoun tuple
            2. If the term is kim, there is separate handling
            3. If term is yahAz or vahAz along with discourse data as 'emphasis' we convert it to yahIM, vahIM and treat them as indeclinables which do not require furthur processing
            4. If dependency is r6, then use the dependency_head to fetch the related noun data, and pick fnum, gender and case of this pronoun term same as related noun.
            5. Except for r6 relation, fnum is by default None

        Parameters:
            1. pronouns - List of pronoun data
            2. processed_nouns - List of processed noun data
            3. processed_indeclinables - List of processed indeclinable data
            2. words_info - List of USR info word wise
            3. verbs_data - List of verbs data

        Returns:
            processed_pronouns = List of pronoun tuples where each tuple looks like - (index, word, category, case, gender, number, person, parsarg, fnum)

        For eg.:
            yaha_1,aBiprAya_8,yaha_1,hE_1-pres
            1,2,3,4
            ,,,
            ,,sg,
            2:r6,4:k1,4:k1s,0:main
            ,,Geo_ncert_6stnd_4ch_0031d:coref,
            ,,,
            ,,,
            affirmative

            pronouns     : [(1, 'yaha_1', '', '', '2:r6', '', '', ''), (3, 'yaha_1', '', 'sg', '4:k1s', 'Geo_ncert_6stnd_4ch_0031d:coref', '', '')]
            words_info     : [(1, 'yaha_1', '', '', '2:r6', '', '', ''), (2, 'aBiprAya_8', '', '', '4:k1', '', '', ''), (3, 'yaha_1', '', 'sg', '4:k1s', 'Geo_ncert_6stnd_4ch_0031d:coref', '', ''), (4, 'hE_1-pres', '', '', '0:main', '', '', '')]
            verbs_data     : [(4, 'hE_1-pres', '', '', '0:main', '', '', '')]

        Result:
            processed_nouns     : [(1, 'yaha', 'p', 'd', 'm', 's', 'a', 'kA', 's'), (3, 'yaha', 'p', 'd', 'm', 's', 'a', 0, None)]
        '''

    processed_pronouns = []
    flag=False
    # for verb in verbs_data:
    #     if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
    #         main_verb = verb
    #         break

    for pronoun in pronouns:
        index = pronoun[0]
        term = clean(pronoun[1])
        anim = pronoun[2]
        gnp = pronoun[3]
        relation_head = pronoun[4].strip().split(':')[0]
        relation = pronoun[4].strip().split(':')[1]
        spkview_data = pronoun[6]
        main_verb,flag=process_construction_cp(relation_head,verbs_data,flag,index)
        # if int(relation_head) in index_data and relation=='k1':
        # for verb in verbs_data:
        #     # if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
        #     v = relation_head + ':verbalizer'
        #     if v == verb[8]:
        #         # id = construction_data.index(v)
        #         main_verb=verb
        #         break
        #     elif int(relation_head)==verb[0]:
        #         main_verb=verb
        #         break
        # else:
        #     main_verb=verb
            # elif verb[4]=='':
            
                

        if is_kim(term):
            gender, number, person, case = get_default_GNP()
            
            
            # gender, number, person = extract_gnp(pronoun)
            processed_pronouns, processed_indeclinables = process_kim(index, index_data, relation, anim, gnp,case, pronoun, words_info,
                                                                      main_verb, processed_pronouns, processed_indeclinables, processed_nouns)
        elif is_yax(term):
            gender, number, person, case = get_default_GNP()
            processed_pronouns, processed_indeclinables = process_yax(index, index_data, relation, anim, gnp,case, pronoun, words_info,
                                                                      main_verb, processed_pronouns, processed_indeclinables, processed_nouns)

        else:
            category = 'p'
            case = 'o'
            parsarg = 0

            if term in ['yahAz', 'vahAz'] and spkview_data == 'emphasis':
                term = term.replace('Az', 'IM')
                category = 'indec'
                processed_indeclinables.append((index, term, category))
                break

            case, postposition = preprocess_postposition_new('pronoun', pronoun, words_info, main_verb, index_data)
            
            if postposition != '':
                parsarg = postposition

            fnum = None
            gender, number, person = extract_gnp(pronoun)
            # #print(gender,'ggg')
            if term == 'addressee':
                addr_map = {'respect': 'Apa', 'informal': 'wU', '': 'wU'}
                pronoun_per = {'respect': 'm', 'informal': 'm', '': 'm_h1'}
                pronoun_number = {'respect': 'p', 'informal': 's', '': 'p'}
                word = addr_map.get(spkview_data.strip().lower(), 'wU')
                person = pronoun_per.get(spkview_data.strip().lower(), 'm_h1')
                number = pronoun_number.get(spkview_data.strip(), 'p')
            elif term == 'speaker':
                # #print(number,'ggg')
                word = 'mEM'
            elif term == 'wyax':
                nn_data = is_next_word_noun(index+1, processed_nouns)
               
                if spkview_data=="proximal" and relation=='k2p':
                    word='yahAz'
                elif spkview_data=="proximal" and relation=='k7p':
                    word='yahAz'
                elif spkview_data=='distal' and relation=='k7p':
                    word='vahAz'
                elif spkview_data=="proximal" and relation=='k7t':
                    word='aba'
                elif spkview_data=='distal' and relation=='k7t':
                    word='waba'
                # if spkview_data == "proximal" and relation=='dem':
                #     word = 'ye'
                #     case='o'
                elif spkview_data == "proximal" and relation=='dem':
                    fnoun = int(relation_head)
                    fnoun_data = getDataByIndex(fnoun, processed_nouns, index=0)
                    if fnoun_data:
                        case = fnoun_data[3]
                    word = 'yaha'
                    # case='o' #changed for 10a example
                # elif spkview_data == "distal" and relation=='dem':
                #     word = 've'
                #     case='o'
                elif spkview_data == "distal" and relation=='dem':
                    fnoun = int(relation_head)
                    fnoun_data = getDataByIndex(fnoun, processed_nouns, index=0)
                    if fnoun_data:
                        case = fnoun_data[3]
                    word = 'vaha'
                    # case='o'
                elif spkview_data == "distal" and number=='s':
                    word = 'vaha'
                elif spkview_data == "distal" and number=='p':
                    word='vaha'
                elif spkview_data == "proximal":
                    word = 'yaha'
                # elif spkview_data == "proximal" :
                #     word = 'yaha'
                else:
                    word = term
            
            else:
                word = term

            if relation == "r6":
                fnoun = int(relation_head)
                fnoun_data = getDataByIndex(fnoun, processed_nouns, index=0)
                if fnoun_data:
                    gender = fnoun_data[4]  # To-ask
                    fnum = number = fnoun_data[5]
                    case = fnoun_data[3]
                if term == 'apanA':
                    parsarg = '0'
            # #print(word,)
            if flag:
                del processed_postpositions_dict[float(index)]
            processed_pronouns.append((index, word, category, case, gender, number, person, parsarg, fnum))
            log(f'{term} processed as pronoun with case:{case} par:{parsarg} gen:{gender} num:{number} per:{person} fnum:{fnum}')
    return processed_pronouns

def process_others(other_words):
    '''Process other words. Right now being processed as noun with default gnp'''
    processed_others = []
    for word in other_words:
        gender = 'm'
        number = 's'
        person = 'a'
        processed_others.append((word[0], clean(word[1]), 'other', gender, number, person))
    return processed_others

def process_verbs(verbs_data, seman_data, gnp_data, depend_data, sentence_type, spkview_data, processed_nouns, processed_pronouns,index_data, words_info,k1_not_need, reprocess=False):
    '''
    Functionality:
        1. In the list of verbs data, identify
            a) if it is complex predicate - it is appended in processed_nouns
            b) if verb_type == 'nonfinite': - process the concept and append in processed_verbs
            c) otherwise process main verb and auxilliary verbs and append in respective lists
    Parameters:
         verbs_data: List of verbs data
         seman_data: Semantic data row of USR
         depend_data: Dependency data row of USR
         sentence_type: Sentence type
         spkview_data: Speaker's view data row of USR
         processed_nouns: List of processed_nouns
         processed_pronouns: List of processed_pronouns
         words_info: List of USR info word wise
         reprocess: for first time processing, it is False. In case of changes, it is made True and sent as parameter
        :Returns:
        List of processed_verbs and processed_auxverbs
    '''
    processed_verbs = []
    processed_auxverbs = []
    # #print(words_info,'words info')
    for concept in verbs_data:
        concept_dep_head = concept[4].strip().split(':')[0]
        concept_dep_val = concept[4].strip().split(':')[1]
        # const_data_head=concept[8].strip().split(':')[0]
        # const_data=concept[8].strip().split(':')[1]
        # if words_info[const_data_head][8]!='':
        #     del processed_postpositions_dict[float(concept_dep_head)]

        concept = Concept(index=concept[0], term=concept[1], dependency=concept[4])
        verb_type = identify_verb_type(concept)
        if verb_type == 'nonfinite':
            verb = process_nonfinite_verb(concept, seman_data, depend_data, sentence_type, processed_nouns, processed_pronouns,index_data, words_info,k1_not_need)
            processed_verbs.append(to_tuple(verb))
        else:
            # if process_verb(concept, seman_data, depend_data, sentence_type, spkview_data, processed_nouns, processed_pronouns, reprocess):
            verb, aux_verbs = process_verb(concept, seman_data, gnp_data, depend_data, sentence_type, spkview_data, processed_nouns, processed_pronouns,index_data, reprocess,k1_not_need)
            processed_verbs.append(to_tuple(verb))
            log(f'{verb.term} processed as main verb with index {verb.index} gen:{verb.gender} num:{verb.number} case:{verb.case}, and tam:{verb.tam}')
            processed_auxverbs.extend([to_tuple(aux_verb) for aux_verb in aux_verbs])
    return processed_verbs, processed_auxverbs

def process_adjectives(adjectives, processed_nouns, processed_verbs):
    '''Process adjectives as (index, word, category, case, gender, number)
        '''
    processed_adjectives = []
    gender, number, person, case = get_default_GNP()
    for adjective in adjectives:
        index = adjective[0]
        category = 'adj'
        adj = clean(adjective[1])
        tam=''
        relConcept = int(adjective[4].strip().split(':')[0]) # noun for regular adjcetives, and verb for k1s-samaadhikaran
        relation = adjective[4].strip().split(':')[1]
        if relation == 'k1s':
            if adj =='kim':
                adj = 'kEsA'
            relConcept_data = getDataByIndex(relConcept, processed_verbs)
        else:
            relConcept_data = getDataByIndex(relConcept, processed_nouns)

        if not relConcept_data:
            log(f'Associated noun/verb not found with the adjective {adjective[1]}. Using default m,s,a,o ')
        else:
            gender, number, person, case = get_gnpcase_from_concept(relConcept_data)
            if relation == 'k1s':
                case = 'd'

        if adj == 'kim' and relation == 'krvn':
            adj = 'kEsA'
        tags = find_tags_from_dix_as_list(adj)
        # #print(tags,'tags1')
        for tag in tags:
            if (tag['cat']== 'v'):
                # noun_type = ''
                
                if relation in ('rvks'):
                    # case='d'
                    category='vj'
                    tam = 'adj_wA_huA'
                elif relation in ('rbks'):
                    category='vj'
                    tam = 'adj_yA_huA'
                # log_msg = f'{adj} processed as verbal adjective with index {index} gen:{gender} num:{number} person:{person}  case:{case}'
                # log(log_msg)
                break
        # processed_noun.append(noun)
        if tam!='':
            adjective = (index, adj, category, case, gender, number,tam)
            processed_adjectives.append((index, adj, category, case, gender, number,tam))
            log(f'{adjective[1]} processed as an adjective with case:{case} gen:{gender} num:{number} tam:{tam}')
        else:
            adjective = (index, adj, category, case, gender, number)
            processed_adjectives.append((index, adj, category, case, gender, number))
            log(f'{adjective[1]} processed as an adjective with case:{case} gen:{gender} num:{number}')
    
    return processed_adjectives

def process_kim(index, index_data, relation, anim, gnp,case, pronoun, words_info, main_verb, processed_pronouns, processed_indeclinables, processed_nouns):

    term = get_root_for_kim(relation, anim,gnp,case,)
    if term == 'kyoM':
        processed_indeclinables.append((index, term, 'indec'))
    else:
        category = 'p'
        case = 'o'
        parsarg = 0
        case, postposition = preprocess_postposition_new('pronoun', pronoun, words_info, main_verb, index_data)
        if postposition != '':
            parsarg = postposition

        fnum = None
        gender, number, person = extract_gnp(pronoun)

        if "r6" in pronoun[4]:
            fnoun = int(pronoun[4][0])
            fnoun_data = getDataByIndex(fnoun, processed_nouns, index=0)
            gender = fnoun_data[4]  # To-ask
            fnum = number = fnoun_data[5]
            case = fnoun_data[3]
            if term == 'apanA':
                parsarg = '0'

        if term in ('kahAz'):
            parsarg = 0
        processed_pronouns.append((pronoun[0], term, category, case, gender, number, person, parsarg, fnum))
        log(f'kim processed as pronoun with term: {term} case:{case} par:{parsarg} gen:{gender} num:{number} per:{person} fnum:{fnum}')
    return processed_pronouns, processed_indeclinables

def process_yax(index1, index_data, relation, anim, gnp,case, pronoun, words_info, main_verb, processed_pronouns, processed_indeclinables, processed_nouns):

    # ind = pronoun[4].split(':')[0]
    # val=pronoun[4].split(':')[1]
    # if int(ind) in index_data and val=='k1':
    #     for j in verbs_data:
    #         v = ind + ':verbalizer'
    #         if v == j[8]:
    #             # id = construction_data.index(v)
    #             main_verb=j
    #         elif ind==j[0]:
    #             main_verb=j
                
    term = get_root_for_yax(relation, anim,gnp,case,)
    # if term == 'kyoM':
    #     processed_indeclinables.append((index, term, 'indec'))
    # else:
    category = 'p'
    case = 'o'
    parsarg = 0
    case, postposition = preprocess_postposition_new('pronoun', pronoun, words_info, main_verb, index_data)
    if postposition != '':
        parsarg = postposition

    fnum = None
    gender, number, person = extract_gnp(pronoun)

    if "r6" in pronoun[4]:
        fnoun = int(pronoun[4][0])
        fnoun_data = getDataByIndex(fnoun, processed_nouns, index=0)
        gender = fnoun_data[4]  # To-ask
        fnum = number = fnoun_data[5]
        case = fnoun_data[3]
        if term == 'apanA':
            parsarg = '0'

    if term in ('jahAz'):
        parsarg = 0
    processed_pronouns.append((pronoun[0], term, category, case, gender, number, person, parsarg, fnum))
    log(f'yax processed as pronoun with term: {term} case:{case} par:{parsarg} gen:{gender} num:{number} per:{person} fnum:{fnum}')
    return processed_pronouns, processed_indeclinables

# def process_main_CP(index, term):
#     """
#     >>> process_main_CP(2,'varRA+ho_1-gA_1')
#     [1.9, 'varRA', 'n', 'd', 'm', 's', 'a', 'CP_noun', None]
#     """
#     CP_term = clean(term.split('+')[0])
#     CP_index = index - 0.1
#     gender = 'm'
#     number = 's'
#     person = 'a'
#     postposition = None
#     CP = []
#     tags = find_tags_from_dix(CP_term)  # getting tags from morph analyzer to assign gender and number for agreement
#     if '*' not in tags['form']:
#         gender = tags['gen']
#         number = tags['num']
#         category = tags['cat']
#     CP = [CP_index, CP_term, 'n','d', gender, number, person, 'CP_noun', postposition]
#     return CP

def construction_row(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'op' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
    return depend_data

def construction_row_span(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'start' in text and dep1!='':
            depend_data[j]=dep1
        elif 'end' in text and dep1!='':
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
    return depend_data

def construction_row_cp(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'kriyAmUla' in text or 'verbalizer' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
    # #print(depend_data,'cp')
    return depend_data

def construction_row_meas(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'count' in text or 'unit' in text or 'unit_every' in text or 'unit_value' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
    # #print(depend_data,'meas')
    return depend_data
def construction_row_waw(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'mod' in text or 'head' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            construction_dict_to_leave[ind]=text
            dep1=depend_data[ind]
            depend_data[ind]=dep1
    # #print(depend_data,'waw')
    return depend_data

def construction_row_spatial(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'whole' in text or 'part' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
    # #print(depend_data,'meas')
    return depend_data

def construction_row_calender(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'component_of' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
            
            depend_data[ind]=dep1
    # #print(depend_data,'calen')
    return depend_data

def construction_row_rate(i,construction_data1,depend_data,index_data1):
    dep1=depend_data[i]
    for j, text in enumerate(construction_data1):
        if 'count' in text or 'unit' in text or 'unit_every' in text or 'unit_value' in text and dep1!='':
            # op_indexes.append(i)
            depend_data[j]=dep1
        elif construction_data1[i]!='':
            head=construction_data1[i].split(':')[0]
            # #print(index_data1)
            ind=index_data1.index(int(head))
            dep1=depend_data[ind]
            depend_data[ind]=dep1
            # multi_construction(j,construction_data1,depend_data)
    return depend_data

# def multi_construction():

def new_to_old_convert_construction_conj_dis(index_data,construction_data,conj_concept):
    # op_index=[]
    op_sub_ind=[]
    construction_data1=''
    for i, concept in enumerate(conj_concept):
        
        if 'conj' in concept :
            ind=index_data[i]
            for j, text in enumerate(construction_data):
                # if text!='':
                txt=text.split(':')[0]
                if 'op' in text and ind==int(txt):
                        op_sub_ind.append(str(index_data[j]))
                        
            # op_index.append(str(op_sub_ind))

            # for j,value in enumerate(op_index):
            #     if j==0:
            #         construction_data1='*conj:'+ value.replace(' ','')
            #     else:
            #         construction_data1=' conj:'+ value.replace(' ','')
        elif 'disjunct' in concept :
            ind=index_data[i]
            for j, text in enumerate(construction_data):
                # if text!='':
                txt=text.split(':')[0]
                if 'op' in text and ind==int(txt):
                        op_sub_ind.append(str(index_data[j]))
                        
            # op_index.append(str(op_sub_ind))

            # for j,value in enumerate(op_index):
            #     if j==0:
            #         construction_data1='*disjunct:'+ value.replace(' ','')
            #     else:
            #         construction_data1=' disjunct:'+ value.replace(' ','')
    return op_sub_ind


# def new_to_old_convert_construction_span(index_data,construction_data,span_concept):
#     # op_index=[]
    
#     construction_data1=''
#     for i, concept in enumerate(span_concept):
#         op_sub_ind=[]
#         if 'span' in concept :
#             ind=index_data[i]
#             for j, text in enumerate(construction_data):
#                 # if text!='':
#                 txt=text.split(':')[0]
#                 if 'start' in text and ind==int(txt):
#                         #print(j)
#                         op_sub_ind.append(index_data[j])
#                 elif 'end' in text and ind==int(txt):
#                         #print(j)
#                         op_sub_ind.append(index_data[j])
#             format_ele=[f"{x}@start" if i==0 else f"{x}@end" for i,x in enumerate(op_sub_ind)]
#             val='['+','.join(format_ele) + ']'
#             value=str(val)
#             # op_index.append(str(val))

#             # for j,value in enumerate(op_index):
#             #     if j==0:
#             construction_data1='*span:'+ value.replace(' ','')
#             #     else:
#             #         construction_data1=' span:'+ value.replace(' ','')
#     #print(construction_data1,'cd')
#     return construction_data1

def process_construction(processed_words, root_words,construction_data1, depend_data, gnp_data, index_data,conj_concept):
    # Adding Ora or yA as a tuple to be sent to morph/ adding it at join_compounds only
    # if k1 in conj, all k1s and main verb g - m and n - pl
    # if all k1 male or mix - k1s g - male else g - f
    # cons list - can be more than one conj
    # k1 ka m/f/mix nikalkr k1s and verb ko g milega    index dep:gen
    # map to hold conj kaha aega
    # construction_dict.clear()
    process_data = processed_words
    dep_gender_dict = {}
    a = 'after'
    b = 'before'
    if gnp_data != []:
        gender = []
        for i in range(len(gnp_data)):
            gnp_info = gnp_data[i]
            gnp_info = gnp_info.strip().strip('][')
            gnp = gnp_info.split(' ')
            gender.append(gnp[0])

    if depend_data != []:
        dependency = []
        for dep in depend_data:
            if dep != '':
                dep_val = dep.strip().split(':')[1]
                dependency.append(dep_val)
    index=new_to_old_convert_construction_conj_dis(index_data,construction_data1,conj_concept)
    # #print(construction_data,'conda')
    for i, dep, g in zip(index_data, dependency, gender):
        dep_gender_dict[str(i)] = dep + ':' + g
    
    # #print(construction_data,'cccd')
    # if construction_data != '*nil' and len(construction_data) > 0:
    # construction = construction_data1.strip().split(' ')
    for cons in root_words:
        # conj_type = cons.split(':')[0].strip().lower()
        # index = cons.split('@')[1].strip().strip('][').split(',') if '@' in cons else cons.strip().strip('][').split(',')
        # index = cons.split(':')[1].strip().strip('][').split(',')
        # #print(index)
        length_index = len(index)
        if 'conj' in cons or 'disjunct' in cons:
            cnt_m = 0
            cnt_f = 0
            PROCESS = False
            for i in index:
                # #print(index,'index',dep_gender_dict)
                relation = dep_gender_dict[i]
                dep = relation.split(':')[0]
                gen = relation.split(':')[1]

                if dep == 'k1':
                    PROCESS = True
                    if gen == 'm':
                        cnt_m = cnt_m + 1
                    elif gen == 'f':
                        cnt_f = cnt_f + 1

            if PROCESS:
                if cnt_f == length_index:
                    g = 'f'
                    num = 'p'
                else:
                    g = 'm'
                    num = 'p'
                process_data = set_gender_make_plural(processed_words, g, num)

            update_index = index[length_index - 2]
            # check if update index is NC
            #if true then go till NC_head index update same index in construction dict and remove ppost if any from processed
            for i in index:
                if i == update_index:
                    if is_update_index_NC(i, processed_words):
                        index_NC_head = fetch_NC_head(i, processed_words)
                        i = index_NC_head
                        
                    if 'conj' in cons:
                        temp = (a, 'Ora')
                        # #print(temp,'varsk')
                    elif 'disjunct' in cons:
                        temp = (a, 'yA')
                    break
                else:
                    temp = (a, ',')
                    if float(i) in construction_dict:
                        construction_dict[float(i)].append(temp)
                    else:
                        construction_dict[float(i)] = [temp]

                    # if i in ppost_dict remove ppost rAma kA Ora SAma kA -> rAma Ora SAma kA
                    if float(i) in processed_postpositions_dict:
                        del processed_postpositions_dict[float(i)]

            if float(i) in construction_dict:
                construction_dict[float(i)].append(temp)
            else:
                construction_dict[float(i)] = [temp]

            if float(i) in processed_postpositions_dict:
                del processed_postpositions_dict[float(i)]

        elif cons == 'list':
            length_list = len(index)
            for i in range(len(index)):
                if i == length_list - 1:
                    break

                if i == 0:
                    temp = (b, 'jEse')
                    if index[i] in construction_dict:
                        construction_dict[index[i]].append(temp)
                    else:
                        construction_dict[index[i]] = [temp]
                    temp = (a, ',')

                elif i < length_list - 1:
                    temp = (a, ',')

                if index[i] in construction_dict:
                    construction_dict[index[i]].append(temp)
                else:
                    construction_dict[index[i]] = [temp]
    # #print('process_construction : ',construction_dict)
    return process_data

def process_construction_span(processed_words, construction_data,index_data):
    # construction_dict.clear()
    process_data = processed_words
    dep_gender_dict = {}
    a = 'after'
    b = 'before'
    # construction_data=new_to_old_convert_construction_span(index_data,construction_data1,span_concept)
    # if construction_data != '*nil' and len(construction_data) > 0:
    # construction = construction_data.strip().split(' ')
    for i,cons in enumerate(construction_data):
        # conj_type = cons.split(':')[0].strip().lower()
        # index = cons.split(':')[1].strip(' ').strip().strip('][').split(',')
        # length_index = len(index)
        if 'start' in cons:
            start_idx = index_data[i]
            # #print(processed_postpositions_dict)
            temp = (a, 'se')
            # del processed_postpositions_dict[index_data[i]]
            if float(start_idx) in construction_dict:
                construction_dict[float(start_idx)].append(temp)
            else:
                construction_dict[float(start_idx)] = [temp]
            if float(start_idx) in processed_postpositions_dict:
                del processed_postpositions_dict[float(i)]

        elif 'end' in cons:
            end_idx = index_data[i]
            temp = (a, 'waka')
            # del processed_postpositions_dict[index_data[i]]
            if float(end_idx) in construction_dict:
                construction_dict[float(end_idx)].append(temp)
            else:
                construction_dict[float(end_idx)] = [temp]
            if float(end_idx) in processed_postpositions_dict:
                del processed_postpositions_dict[float(i)]
    return process_data

def process_construction_rate(processed_words, construction_data,index_data):
    # construction_dict.clear()
    process_data = processed_words
    # dep_gender_dict = {}
    a = 'after'
    b = 'before'
    for i,cons in enumerate(construction_data):
        if 'count' in cons and 'per_unit' in construction_data[i+1]:
            start_idx = index_data[i]
            temp = (b, 'prawyeka')
            if float(start_idx) in construction_dict:
                construction_dict[float(start_idx)].append(temp)
            else:
                construction_dict[float(start_idx)] = [temp]
        if float(index_data[i]) in processed_postpositions_dict:
            del processed_postpositions_dict[float(index_data[i])]
            
    return process_data

def process_construction_cp(relation_head,verbs_data,flag,index):
    # construction_dict.clear()
    for verb in verbs_data:
        # if len(verb[4]) > 0 and verb[4].strip().split(':')[1] == 'main' or verb[4].strip().split(':')[1] == 'rcelab' or verb[4].strip().split(':')[1] == 'rcdelim':
        v = relation_head + ':verbalizer'
        if v == verb[8]:
            # id = construction_data.index(v)
            main_verb=verb
            flag=True
            break
        elif int(relation_head)==verb[0]:
            main_verb=verb
            break
    else:
        main_verb=verb
    
    return main_verb,flag

def process_construction_spatial(processed_words, construction_data,index_data):
    # construction_dict.clear()
    process_data = processed_words
    # dep_gender_dict = {}
    a = 'after'
    b = 'before'
    for i,cons in enumerate(construction_data):
        if 'whole' in cons in construction_data[i]:
            start_idx = index_data[i]
            # temp = (b, 'prawyeka')
            # del processed_postpositions_dict[index_data[i]]
            temp = (a, 'meM')
            if float(start_idx) in construction_dict:
                construction_dict[float(start_idx)].append(temp)
            else:
                construction_dict[float(start_idx)] = [temp]
        if float(index_data[i]) in processed_postpositions_dict:
            del processed_postpositions_dict[float(index_data[i])]
            
    return process_data
def process_construction_xvanxva(processed_words, construction_data,index_data):
    # construction_dict.clear()
    process_data = processed_words
    # dep_gender_dict = {}
    a = 'after'
    b = 'before'
    for i,cons in enumerate(construction_data):
        if 'op' in cons in construction_data[i]:
            start_idx = index_data[i]
            # temp = (b, 'prawyeka')
            # del processed_postpositions_dict[index_data[i]]
            temp = (a, '-')
            if float(start_idx) in construction_dict:
                construction_dict[float(start_idx)].append(temp)
            else:
                construction_dict[float(start_idx)] = [temp]
            break
        if float(index_data[i]) in processed_postpositions_dict:
            del processed_postpositions_dict[float(index_data[i])]

    return process_data


def process_auxiliary_verbs(verb: Verb, index_data, concept, spkview_data) -> [Verb]:
    """
    >>> [to_tuple(aux) for aux in process_auxiliary_verbs(Verb(index=4, term = 'kara', gender='m', number='s', person='a', tam='hE', type= 'auxiliary'), concept_term='kara_17-0_sakawA_hE_1')]
    [(4.1, 'saka', 'v', 'm', 's', 'a', 'wA', 'auxiliary'), (4.2, 'hE', 'v', 'm', 's', 'a', 'hE',''auxiliary'')]
    """
    concept_term = concept.term
    concept_index = concept.index
    HAS_SHADE_DATA = False
    auxiliary_term_tam = []
    shade_index = 1
    for data in spkview_data:
        if data != '':
            data = data.strip().strip('][')
            if 'shade' in data and concept_index == index_data[shade_index + 1]:
                term = clean(data.split(':')[1])
                tam = identify_default_tam_for_main_verb(concept_term)
                HAS_SHADE_DATA = True
                break
    shade_index = shade_index + 1
    # ind1=index_data.index(concept_index)
    # if 'shade' in spkview_data[ind1]:
    #     data1 = spkview_data[concept_index].strip().strip('][')
    #     term = clean(data1.split(':')[1])
    #     tam = identify_default_tam_for_main_verb(concept_term)
    #     HAS_SHADE_DATA = True
        

    if HAS_SHADE_DATA:
        if term == 'jA' and tam == 'yA':
            tam = 'yA1'   # to generate gayA from jA-yA
        # else:

        temp = (term, tam)
        auxiliary_term_tam.append(temp)
        # #print(auxiliary_term_tam,'auxxxx')
        verb = set_main_verb_tam_zero(verb)

    auxiliary_verb_terms = identify_auxiliary_verb_terms(concept_term)
    for v in auxiliary_verb_terms:
        term, tam = auxmap_hin(v)
        temp = (term, tam)
        auxiliary_term_tam.append(temp)

    return [create_auxiliary_verb(index, pair[0], pair[1], verb) for index, pair in enumerate(auxiliary_term_tam)]

def process_dep_rbks(concept, words_info, processed_nouns, processed_pronouns):
    finalData = []
    k1_exists, k1_index = find_match_with_same_head(concept.index, 'k1', words_info, index=4)
    k3_exists, k3_index = find_match_with_same_head(concept.index, 'k3', words_info, index=4)
    if k1_exists:
        case = 'o'
        ppost = 'ke xvArA'

        for i in range(len(processed_nouns)):
            data = processed_nouns[i]
            data_index = data[0]
            if data_index == k1_index:
                temp = list(data)
                temp[3] = case
                temp[8] = ppost
                processed_nouns[i] = tuple(temp)
                update_ppost_dict(data_index, ppost)

    elif k3_exists:
        case = 'o'
        ppost = 'ke xvArA'

        for i in range(len(processed_nouns)):
            data = processed_nouns[i]
            data_index = data[0]
            if data_index == k3_index:
                temp = list(data)
                temp[3] = case
                temp[8] = ppost
                processed_nouns[i] = tuple(temp)
                update_ppost_dict(data_index, ppost)

def process_verb(concept: Concept, seman_data, gnp_data, dependency_data, sentence_type, spkview_data, processed_nouns, processed_pronouns,index_data, reprocessing,k1_not_need):
    """
    concept pattern: 'main_verb' - 'TAM for main verb' _Aux_verb+tam...
    Example 1:
    kara_1-wA_hE_1
    main verb - kara,  main verb tam: wA, Aux -hE with TAM hE (identified from tam mapping file)

    Example 2:
    kara_1-yA_1
    main verb - kara,  main verb tam: yA,

    Example 3:
    kara_1-0_rahA_hE_1
    main verb - kara,  main verb tam: 0, Aux verb -rahA with TAM hE, Aux -hE with TAM hE (identified from tam mapping file)

    Example 4:
    kara_1-0_sakawA_hE_1
    main verb - kara,  main verb tam: 0, Aux verb -saka with TAM wA, Aux -hE with TAM hE (identified from tam mapping file)

    *Aux root and Aux TAM identified from auxiliary mapping File
    """
    # if process_main_verb(concept, seman_data, dependency_data, sentence_type, processed_nouns, processed_pronouns, reprocessing):
    verb = process_main_verb(concept, seman_data, gnp_data, dependency_data, sentence_type, processed_nouns, processed_pronouns,index_data, reprocessing,k1_not_need)
    auxiliary_verbs = process_auxiliary_verbs(verb,index_data, concept, spkview_data)
    return verb, auxiliary_verbs
    # else:
    #     return None

def process_nonfinite_verb(concept, seman_data, depend_data, sentence_type, processed_nouns, processed_pronouns,index_data, words_info,k1_not_need):
    '''
    >>process_nonfinite_verb([], [()],[()])
    '''
    gender = 'm'
    number = 's'
    person = 'a'
    verb = Verb()
    verb.index = concept.index
    # is_cp = is_CP(concept.term)
    # if is_cp: #only CP_head as nonfinite verb
    #     draft_concept = concept.term.split('+')[1]
    #     verb.term  = clean(draft_concept)
    # else:
    verb.term = clean(concept.term)

    verb.type = 'nonfinite'
    verb.tam = ''
    relation = concept.dependency.strip().split(':')[1]
    if relation == 'rbks':
        process_dep_rbks(concept, words_info, processed_nouns, processed_pronouns)

    verb.tam = set_tam_for_nonfinite(relation)
    full_tam = verb.tam
    # if getVerbGNP_new(verb.term, full_tam, is_cp, seman_data, depend_data, sentence_type, processed_nouns, processed_pronouns):
    gender, number, person = getVerbGNP_new(verb.term, full_tam,verb.index, seman_data, depend_data, sentence_type, processed_nouns, processed_pronouns,index_data,k1_not_need)
    verb.gender = gender
    verb.number = number
    verb.person = person
    verb.case = 'o' # to be updated - agreement with following noun
    log(f'{verb.term} processed as nonfinite verb with index {verb.index} gen:{verb.gender} num:{verb.number} case:{verb.case}, and tam:{verb.tam}')
    return verb
    # else:
    #     return None

def process_dep_k2g(data_case, main_verb):
    verb = identify_main_verb(main_verb[1])
    if verb in application.repository.constant.kisase_k2g_verbs:
        ppost = 'se'
    else:
        ppost = 'ko'
    return ppost

def process_main_verb(concept: Concept, seman_data, gnp_data, dependency_data, sentence_type, processed_nouns, processed_pronouns,index_data, reprocessing,k1_not_need):
    """
    >>> to_tuple(process_main_verb(Concept(index=2, term='varRA+ho_1-gA_1', dependency='0:main'), ['2:k7t', '0:main'], [(1, 'kala', 'n', 'o', 'm', 's', 'a', 'common', None)], [], False))
    [OK]     : varRA processed as noun with index 1.9 case:d gen:f num:s per:a, noun_type:CP_noun, default postposition:None.
    (2, 'ho', 'v', 'f', 's', 'a', 'gA')
    >>> to_tuple(process_main_verb(Concept(index=2, term='varRA+ho_1-gA_1', dependency='0:main'), ['2:k7t', '0:main'], [(1, 'kala', 'n', 'o', 'm', 's', 'a', 'common', None)], [], True))
    [OK]     : ho reprocessed as verb with index 2 gen:f num:s per:a in agreement with CP
    (2, 'ho', 'v', 'f', 's', 'a', 'gA')
    >>>
    """
    verb = Verb()
    verb.type = "main"
    verb.index = concept.index
    verb.term = identify_main_verb(concept.term)
    # #print(verb.term,gnp_data,'vtt')
    full_tam = identify_complete_tam_for_verb(concept.term)
    verb.tam = identify_default_tam_for_main_verb(concept.term)
    if verb.term == 'hE' and verb.tam in ('pres', 'past'):  # process TAM
        alt_tam = {'pres': 'hE', 'past': 'WA'}
        alt_root = {'pres': 'hE', 'past': 'WA'}
        verb.term = alt_root[verb.tam]  # handling past tense by passing correct root WA
        verb.tam = alt_tam[verb.tam]
    if verb.term == 'jA' and verb.tam == 'yA':
        verb.tam = 'yA1'
    # #print(index_data)
    ind=index_data.index(verb.index)

    if gnp_data[ind] in ('causative','doublecausative'):
        verb.term=identify_causative(verb.term,gnp_data,ind)
        
    # is_cp = is_CP(concept.term)
    # if getVerbGNP_new(concept.term, full_tam, is_cp, seman_data, dependency_data, sentence_type, processed_nouns, processed_pronouns):
    verb.gender, verb.number, verb.person = getVerbGNP_new(concept.term, full_tam,verb.index, seman_data, dependency_data, sentence_type, processed_nouns, processed_pronouns,index_data,k1_not_need)
    return verb
    # else:
    #     return None
def identify_causative(verb,gnp_data,ind):
    with open(application.repository.constant.CAUSATIVE_MAP_FILE, 'r') as file:
        for line in file.readlines():
            # #print(line,'lll')
            causative_mapping = line.strip().split(',')
            if causative_mapping[0] == verb and causative_mapping[1]==gnp_data[ind]:
                return causative_mapping[2]
    # log(f'"{aux_verb}" not found in auxiliary mapping.', 'WARNING')

def create_auxiliary_verb(index, term, tam, main_verb: Verb):
    verb = Verb()
    verb.index = main_verb.index + (index + 1)/10
    verb.gender, verb.number, verb.person = main_verb.gender, main_verb.number, main_verb.person
    verb.term = term
    verb.tam = tam
    if verb.term == 'cAha':
            verb.person = 'm_h'
    verb.type = 'auxiliary'
    log(f'{verb.term} processed as auxiliary verb with index {verb.index} gen:{verb.gender} num:{verb.number} and tam:{verb.tam}')
    return verb
def get_all_form(morph_forms):
    """
    >>> get_first_form("^mAz/mA<cat:n><case:d><gen:f><num:p>/mAz<cat:n><case:d><gen:f><num:s>/mAz<cat:n><case:o><gen:f><num:s>$")
    'mA<cat:n><case:d><gen:f><num:p>/mAz<cat:n><case:d><gen:f><num:s>/mAz<cat:n><case:o><gen:f><num:s>'
    """
    morph=morph_forms.split("$")[1]
    return morph

def get_first_form(morph_forms):
    """
    >>> get_first_form("^mAz/mA<cat:n><case:d><gen:f><num:p>/mAz<cat:n><case:d><gen:f><num:s>/mAz<cat:n><case:o><gen:f><num:s>$")
    'mA<cat:n><case:d><gen:f><num:p>'
    """
    morph=morph_forms.split("/")[1]
    return morph

def get_root_for_kim(relation, anim, gnp,case):
    # kOna is root for - kisakA, kisakI, kisake, kinakA, kinake, kinakI, kOna, kisa, kisane, kise, kisako,
    # kisase, kisake, kisameM, kisameM_se, isapara, kina, inhoMne, kinheM, kinako, kinase, kinpara, kinake, kinameM, kinameM_se, kisI, kisa
    # if gnp=='pl':
    #     number='p'
    # else:
    #     number='s'
    animate = ['anim', 'per']
    if relation in ('k2p', 'k7p'):
        return 'kahAz'
    elif relation == 'k5' :
        return 'kahAz'
    elif relation == 'k7t':
        return 'kaba'
    elif relation == 'rh' :
        return 'kyoM'
    elif relation == 'rt' : #generate kisa
        return 'kOna'
    elif relation == 'krvn': #generate kEse
        return 'kEsA'
    elif relation == 'k1s':
        return 'kEsA'
    elif relation=='dem' and gnp=='' and case=='o':
        return 'kis'
    elif relation=='dem' and gnp=='pl' and case=='o':
        return 'kin'
    elif anim not in animate:
        return 'kyA'
    elif anim in animate:
        return 'kOna'
    elif relation =='k1' or relation =='k2':
        return 'kyA'
    else:
        return 'kim'

def get_root_for_yax(relation, anim, gnp,case):
    # kOna is root for - kisakA, kisakI, kisake, kinakA, kinake, kinakI, kOna, kisa, kisane, kise, kisako,
    # kisase, kisake, kisameM, kisameM_se, isapara, kina, inhoMne, kinheM, kinako, kinase, kinpara, kinake, kinameM, kinameM_se, kisI, kisa
    # if gnp=='pl':
    #     number='p'
    # else:
    #     number='s'
    animate = ['anim', 'per']
    if relation in ('k2p', 'k7p'):
        return 'jahAz'
    elif relation == 'k5' :
        return 'jahAz'
    elif relation == 'k7t':
        return 'jaba'
    # elif relation == 'rh' :
    #     return 'kyoM'
    elif relation == 'rt' : #generate kisa
        return 'jo'
    # elif relation == 'krvn': #generate kEse
    #     return 'kEsA'
    # elif relation == 'k1s':
    #     return 'kEsA'
    elif relation=='dem' and gnp=='' and case=='o':
        return 'jisa'
    elif relation=='dem' and gnp=='pl' and case=='o':
        return 'jina'
    elif anim not in animate:
        return 'jo'
    elif anim in animate:
        return 'jo'
    elif relation =='k1' or relation =='k2':
        return 'jo'
    else:
        return 'jo'

def get_default_GNP():
    gender,number,person,case = 'm','s','a','o'
    
    return gender, number, person, case

def get_gnpcase_from_concept(concept): #computes GNP values from noun or

    if concept[2] == 'v':
        gender = concept[3]
        number= concept[4]
        person = concept[5]
        case =  concept[7]

    elif concept[2] == 'vn':
        gender = concept[4]
        number= concept[5]
        person = concept[6]
        case =  concept[3]

    elif concept[2] in ('n', 'p'):
        gender = concept[4]
        number= concept[5]
        person = concept[6]
        case = concept[3]
    else:
        gender, number, person, case = get_default_GNP()
    return gender, number, person, case

# def get_TAM(term, tam):
#     """
#     >>> get_TAM('hE', 'pres')
#     'hE'
#     >>> get_TAM('hE', 'past')
#     'WA'
#     >>> get_TAM('asdf', 'gA')
#     'gA'
#     """
#     if term == 'hE' and tam in ('pres', 'past'):
#         alt_tam = {'pres': 'hE', 'past': 'WA'}
#         return alt_tam[tam]
#     else:
#         if term == 'jA':
#             tam = 'yA1'
#             return tam
#     return tam

def get_main_verb(term):
    ''' return main verb from a term'''

    pass

def getDataByIndex(value: int, searchList: list, index=0):
    '''search and return data by index in an array of tuples.
        Index should be first element of tuples.
        Return False when index not found.'''
    try:
        res = False
        for dataele in searchList:
            # dataele=list(dataele)
            # if (dataele[(index)]) == value and dataele[7]=='vn':
            #     dataele[3]='d'
            #     res = tuple(dataele)
            if (dataele[(index)]) == value:
                # res = tuple(dataele)
                res = dataele
                break
        return res
    except IndexError:
        log(f'Index out of range while searching index:{value} in {searchList}', 'WARNING')
        return False
    

# def getComplexPredicateGNP(term):
#     CP_term = clean(term.split('+')[0])
#     gender = 'm'
#     number = 's'
#     person = 'a'

#     tags = find_tags_from_dix(CP_term)  # getting tags from morph analyzer to assign gender and number for agreement
#     if '*' not in tags['form']:
#         gender = tags['gen']
#         number = tags['num']
#     return gender, number, person

def getGNP_using_k2(k2exists, searchList):
    casedata = getDataByIndex(k2exists, searchList)
    if (casedata == False):
        log('Something went wrong. Cannot determine GNP for verb.', 'ERROR')
        sys.exit()
    verb_gender, verb_number, verb_person = casedata[4], casedata[5], casedata[6]
    return verb_gender, verb_number, verb_person[0]
        
def getGNP_using_k1(k1exists, searchList):
    # for k1 in k1exists:
    casedata = getDataByIndex(k1exists, searchList)
    if (casedata == False):
        log('Something went wrong. Cannot determine GNP for verb k1 is missing.', 'ERROR')
        sys.exit()
    verb_gender, verb_number, verb_person = casedata[4], casedata[5], casedata[6]
    return verb_gender, verb_number, verb_person

def getVerbGNP_new(concept_term, full_tam,index, seman_data, depend_data, sentence_type, processed_nouns, processed_pronouns,index_data,k1_not_need):
    '''
    '''
    #for imperative sentences
    if sentence_type in ('Imperative','imperative') or 'o' in full_tam:
        verb_gender = 'm'
        verb_number = 's'
        verb_person = 'm'
        return verb_gender, verb_number, verb_person

    #for non-imperative sentences
    # For non-imperative sentences
    k1exists = False
    k2exists = False
    k1_case = ''
    k2_case = ''
    verb_gender, verb_number, verb_person, case = get_default_GNP()
    # if process_nominal_form:
    #     searchList = processed_nouns + processed_pronouns 
    # else:
    searchList = processed_nouns + processed_pronouns

    for cases in depend_data:
        # head_index=cases.split(':')[0]
        case=cases.split(':')[1]
        if cases == '':
            continue
        # elif (case=='k1' or case=='pk1') and head_index==str(index):
        elif (case=='k1' or case=='pk1'):
            k1exists_index = depend_data.index(cases)
            k1exists = index_data[k1exists_index]
            
        # elif cases[-2:]=='k2' and head_index==index:
        elif cases[-2:]=='k2':
            k2exists_index = depend_data.index(cases)
            k2exists = index_data[k2exists_index]

    if k1exists:
        casedata = getDataByIndex(k1exists, searchList)
        if (casedata == False):
            log('Something went wrong. Cannot determine case for k1.', 'ERROR')
        else:
            k1_case = casedata[3]
   

    if k2exists:
        casedata = getDataByIndex(k2exists, searchList)
        if (casedata == False):
            log('Something went wrong. Cannot determine case for k2.', 'ERROR')
        else:
            k2_case = casedata[3]
    
#     if is_cp:
#         cp_term = concept_term.split('+')[0]
#         if not k1exists and not k2exists:
#             verb_gender, verb_number, verb_person = getComplexPredicateGNP(cp_term)
#         elif k1exists and k1_case == 'd':
#             verb_gender, verb_number, verb_person = getGNP_using_k1(k1exists, searchList)
#         elif k1exists and k1_case == 'o' and k2exists and k2_case == 'o':
#             verb_gender, verb_number, verb_person = getComplexPredicateGNP(cp_term)
#         return verb_gender, verb_number, verb_person[0]

    if 'yA' in full_tam:
        if k1exists and k1_case == 'd':
            verb_gender, verb_number, verb_person = getGNP_using_k1(k1exists, searchList)
        elif k1exists and k1_case == 'o' and k2exists and k2_case == 'd':
            verb_gender, verb_number, verb_person = getGNP_using_k2(k2exists, searchList)
        return verb_gender, verb_number, verb_person[0]

    if full_tam in application.repository.constant.nA_list:
        return verb_gender, verb_number, verb_person[0]

    #tam - gA
    elif k1exists:
        verb_gender, verb_number, verb_person = getGNP_using_k1(k1exists, searchList)
        return verb_gender, verb_number, verb_person[0]
    else:
        return verb_gender, verb_number, verb_person[0]

def is_tam_ya(verbs_data):

    ya_tam = '-yA_'
    if len(verbs_data) > 0 and verbs_data != ():
        term = verbs_data[1]
        if ya_tam in term:
            return True
    return False

def is_kim(term):
    if term == 'kim':
        return True

    return False
def is_yax(term):
    if term == 'yax':
        return True

    return False

def is_complex_predicate(concept):
    return "+" in concept

# def is_CP(term):
#     """
#     >>> is_CP('varRA+ho_1-gA_1')
#     True
#     >>> is_CP("kara_1-wA_hE_1")
#     False
#     """
#     if "+" in term:
#         return True
#     else:
#         return False

def is_update_index_NC(i, processed_words):
    for data in processed_words:
        temp = tuple(data)
        if len(temp) > 7 and float(i) == temp[0] and temp[7] == 'NC':
            return True

    return False

def is_nonfinite_verb(concept):
    return concept.type == 'nonfinite'

def has_tam_ya():
    '''Check if USR has verb with TAM "yA".
        It sets the global variable HAS_TAM to true
    '''
    global HAS_TAM
    if HAS_TAM == True:
        return True
    else:
        return False

def has_GNP(gnp_info):
    if len(gnp_info) and ('sg', 'pl') in gnp_info:
        return True
    return False

def has_ques_mark(POST_PROCESS_OUTPUT,sentence_type):
    # interrogative_lst = ["yn_interrogative", "yn_interrogative_negative", "pass-yn_interrogative", "interrogative",
    #                      "Interrogative", "pass-interrogative"]
    if sentence_type[1:] in ("yn_interrogative", "yn_interrogative_negative", "pass-yn_interrogative", "interrogative",
                        "Interrogative", "pass-interrogative"):
        return POST_PROCESS_OUTPUT + '?'
    elif sentence_type[1:] in ('pass_affirmative','affirmative', 'Affirmative', 'negative', 'Negative', 'imperative', 'Imperative',"fragment","term","title","heading"):
        return POST_PROCESS_OUTPUT + '।'
    else:
        return POST_PROCESS_OUTPUT

# def identify_case(verb, dependency_data, processed_nouns, processed_pronouns,index_data):
#     return getVerbGNP_new(verb.term, verb.tam, dependency_data, processed_nouns, processed_pronouns,index_data)

def identify_main_verb(concept_term):
    """
    >>> identify_main_verb("kara_1-wA_hE_1")
    'kara'
    >>> identify_main_verb("varRA+ho_1-gA_1")
    'ho'
    """
    if ("+" in concept_term):
        concept_term = concept_term.split("+")[1]
    con=clean(concept_term.split("-")[0])
    # #print(con,'main verb')
    return con

def identify_default_tam_for_main_verb(concept_term):
    """
    >>> identify_default_tam_for_main_verb("kara_1-wA_hE_1")
    'wA'
    >>> identify_default_tam_for_main_verb("kara_1-0_rahA_hE_1")
    '0'
    """
    # con=concept_term.split("-")[1].split("_")[0]
    if '-' in concept_term:
        con=concept_term.split("-")[1]
        if '_' in con:
            con=con.split("_")[0]
            return con
        else:
            return con
    else:
        return concept_term
    return con

def identify_complete_tam_for_verb(concept_term):
    """
    >>> identify_complete_tam_for_verb("kara_1-wA_hE_1")
    'wA_hE'
    >>> identify_complete_tam_for_verb("kara_1-0_rahA_hE_1")
    'rahA_hE'
    >>> identify_complete_tam_for_verb("kara_1-nA_howA_hE_1")
    'nA_howA_hE'
    >>> identify_complete_tam_for_verb("kara_o")
    'o'
    """
    if 'cAha_1-e_1' in concept_term:
        return 'cAhiye'
    elif "-" not in concept_term:
        return concept_term.split("_")[1]
    tmp = concept_term.split("-")[1]
    tokens = tmp.split("_")
    non_digits = filter(lambda x: not x.isdigit(), tokens)
    tam_v="_".join(non_digits)

    return tam_v

def identify_auxiliary_verb_terms(term):
    """
    >>> identify_auxiliary_verb_terms("kara_1-wA_hE_1")
    ['hE']
    >>> identify_auxiliary_verb_terms("kara_1-0_rahA_hE_1")
    ['rahA', 'hE']
    """
    # #print(term,'ee')
    aux_verb_terms = term.split("-")[1].split("_")[1:]
    # #print(aux_verb_terms,'ee')
    cleaned_terms = map(clean, aux_verb_terms)
    # #print(cleaned_terms,'clt')
    el=list(filter(lambda x: x != '', cleaned_terms))
    # #print(el)
    return el            # Remove empty strings after cleaning

def identify_verb_type(verb_concept):
    '''
    >>identify_verb_type([])
    '''
    #dep_rel = verb_concept[4].strip().split(':')[1] #if using with non-OO program
    dependency = verb_concept.dependency
    dep_rel = dependency.strip().split(':')[1]
    v_type = ''
    if dep_rel == 'main':
        v_type = "main"
    # elif dep_rel in ('rpk', 'rbk', 'rvks', 'rbks', 'rsk', 'rblpk','rblak','rblsk'):
    #     v_type = "nonfinite"
    elif dep_rel in ('rpk', 'rsk','rbk'):
        v_type = "nonfinite"
    # elif dep_rel in ('rvks'):
    #     v_type = "verbal adjective"
    # elif dep_rel in ('rblpk','rblak','rblsk'):
    #     v_type = "nominal_verb"
    else:
        v_type = "main"
    return v_type

def findExactMatch(value: int, searchList: list, index=0):
    '''search and return data by index in an array of tuples.
        Index should be first element of tuples.

        Return False when index not found.'''

    try:
        for dataele in searchList:
            if value == dataele[index].strip().split(':')[1]:
                return (True, dataele)
    except IndexError:
        log(f'Index out of range while searching index:{value} in {searchList}', 'WARNING')
        return (False, None)
    return (False, None)

def findValue(value: int, searchList: list, index=0):
    '''search and return data by index in an array of tuples.
        Index should be first element of tuples.

        Return False when index not found.'''

    try:
        for dataele in searchList:
            if value == dataele[index]:
                return (True, dataele)
    except IndexError:
        log(f'Index out of range while searching index:{value} in {searchList}', 'WARNING')
        return (False, None)
    return (False, None)

def find_tags_from_dix(word):
    """
    >>> find_tags_from_dix("mAz")
    {'cat': 'n', 'case': 'd', 'gen': 'f', 'num': 'p', 'form': 'mA'}
    """
    dix_command = "echo {} | apertium-destxt | lt-proc -ac application/repository/hi.morfLC.bin | apertium-retxt".format(word)
    morph_forms = os.popen(dix_command).read()
    # #print(morph_forms,'dixxxxxxxx')
    p_m=parse_morph_tags(morph_forms)
    return p_m

def find_tags_from_dix_as_list(word):
    """
    >>> find_tags_from_dix("mAz")
    {'cat': 'n', 'case': 'd', 'gen': 'f', 'num': 'p', 'form': 'mA'}
    """
    dix_command = "echo {} | apertium-destxt | lt-proc -ac application/repository/hi.morfLC.bin | apertium-retxt".format(word)
    morph_forms = os.popen(dix_command).read()
    p_m=parse_morph_tags_as_list(morph_forms)
    # #print(p_m,'pmmmmmmmmm')
    return p_m

def find_exact_dep_info_exists(index, dep_rel, words_info):
    for word in words_info:
        dep = word[4]
        dep_head = word[4].strip().split(':')[0]
        dep_val = word[4].strip().split(':')[1]
        if dep_val == dep_rel and int(dep_head) == index:
            return True

    return False

def find_match_with_same_head(data_head, term, words_info, index):
    #  k2exists, k2_index = find_match_with_same_head(data_head, 'k2', words_info, index=4)
     for dataele in words_info:
        dataele_index = dataele[0]
        dep_head = dataele[index].strip().split(':')[0]
        dep_value = dataele[index].strip().split(':')[1]
        if str(data_head) == dep_head and term == dep_value:
            return True, dataele_index
     return False, -1

def parse_morph_tags(morph_form):
    """
    >>> parse_morph_tags("mA<cat:n><case:d><gen:f><num:p>")
    {'cat': 'n', 'case': 'd', 'gen': 'f', 'num': 'p', 'form': 'mA'}
    """
    form = morph_form.split("<")[0]
    matches = re.findall("<(.*?):(.*?)>", morph_form)
    result = {match[0]: match[1] for match in matches}
    result["form"] = form
    return result

# def parse_morph_tags_as_list(morph_form):
#     """
#     >>> parse_morph_tags("mA<cat:n><case:d><gen:f><num:p>")
#     {'cat': 'n', 'case': 'd', 'gen': 'f', 'num': 'p', 'form': 'mA'}
#     """
#     #print(morph_form,'form')
#     form = morph_form.split("<")[0]
#     #print(form,'mmmm')
#     matches = re.findall("<(.*?):(.*?)>", morph_form)
#     result = [(match[0], match[1]) for match in matches]
#     result.append(('form',form))
#     #print(result,'res')
#     return result

def parse_morph_tags_as_list(morph_form):
    """
    Extracts the word and its corresponding morphological tags from the given morph-form string.

    Example:
    >>> parse_morph_tags("mA<cat:n><case:d><gen:f><num:p>")
    [{'form': 'mA', 'cat': 'n', 'case': 'd', 'gen': 'f', 'num': 'p'}]
    """
    # Split the morph-form by '/' to get individual word segments
    word = morph_form.split('/')[0].replace('^','')
    segments = morph_form.split('/')
    
    result = []
    # Iterate over each segment
    for segment in segments:
        form = segment.split("<")[0]  # Extract the word (before the first '<')
        if word==form:
            matches = re.findall("<(.*?):(.*?)>", segment)  # Find all morphological tags
            tag_dict = {match[0]: match[1] for match in matches}  # Convert matches to a dictionary
            tag_dict['form'] = form  # Add the word under the 'form' key
            result.append(tag_dict)  # Add the dictionary to the result list
    # #print(result,'result')
    return result

def generate_input_for_morph_generator(input_data):
    """Process the input and generate the input for morph generator"""
    morph_input_data = []
    for data in input_data:
        if data[2] == 'p':
            if data[8] != None and isinstance(data[8], str):
                morph_data = f'^{data[1]}<cat:{data[2]}><parsarg:{data[7]}><fnum:{data[8]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}><per:{data[6]}>$'
            else:
                morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><parsarg:{data[7]}><gen:{data[4]}><num:{data[5]}><per:{data[6]}>$'
        elif data[2] == 'n' and data[7] in ('proper', 'digit'):
            morph_data = f'{data[1]}'
        # elif data[2] == 'n' and data[7] == 'vn':
        #     morph_data = f'^{data[1]}<cat:{data[7]}><case:{data[3]}>$'
        elif data[2] == 'vn':
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}>$'
        elif data[2] == 'n' and data[7] != 'proper':
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}>$'

        elif data[2] == 'v' and data[8] in ('main','auxiliary'):
            morph_data = f'^{data[1]}<cat:{data[2]}><gen:{data[3]}><num:{data[4]}><per:{data[5]}><tam:{data[6]}>$'
        elif data[2] == 'v' and data[6] == 'kara' and data[8] in ('nonfinite','adverb')     :
            morph_data = f'^{data[1]}<cat:{data[2]}><gen:{data[3]}><num:{data[4]}><per:{data[5]}><tam:{data[6]}>$'
        elif data[2] == 'v' and data[6] != 'kara' and data[8] =='nonfinite':
            morph_data = f'^{data[1]}<cat:{data[2]}><gen:{data[3]}><num:{data[4]}><case:{data[7]}><tam:{data[6]}>$'
        elif data[2] == 'adj':
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}>$'
        elif data[2] == 'vj':
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}><tam:{data[6]}>$'
        elif data[2] == 'indec':
            morph_data = f'{data[1]}'
        elif data[2] == 'other':
            morph_data = f'{data[1]}'
        else:
            morph_data = f'^{data[1]}$'
        morph_input_data.append(morph_data)
    # #print(morph_input_data)
    return morph_input_data

def write_data(writedata):
    """Return the Morph Input Data as a string instead of writing to a file."""
    final_input = " ".join(writedata)
    # Return the generated morph data as a string
    # #print(final_input,'final')
    return final_input

def run_morph_generator(data):
    """ Pass the morph generator through the provided data and return the output."""
    command = [
        "lt-proc",
        "-g",
        "-c",
        "application/repository/hi.gen_LC.bin",
        # "-"
    ]

    # Run the command with input data piped directly
    result = subprocess.run(
        command,
        input=data,
        capture_output=True,
        text=True
    )
    
    # Optionally, handle errors
    if result.returncode != 0:
        raise RuntimeError(f"Error in morph generator: {result.stderr}")
    
    return result.stdout

def generate_morph(processed_words):
    """Run Morph generator"""
    morph_input = generate_input_for_morph_generator(processed_words)
    MORPH_INPUT = write_data(morph_input)
    OUTPUT_FILE = run_morph_generator(MORPH_INPUT)
    return OUTPUT_FILE

def read_output_data(output_file):
    """Check the output file data for post processing"""

    with open(output_file, 'r') as file:
        data = file.read()
    return data

def analyse_output_data(output_data, morph_input):
    output_data = output_data.strip().split(" ")
    combine_data = []
    for i in range(len(output_data)):
        morph_input_list = list(morph_input[i])
        morph_input_list[1] = output_data[i]
        combine_data.append(tuple(morph_input_list))
    return combine_data

def handle_compound_nouns(noun, processed_nouns, category, case, gender, number, person, postposition):
    dnouns = noun[1].split('+')
    # #print(dnouns,'dns')
    for k in range(len(dnouns)):
        index = noun[0] + (k * 0.1)
        noun_type = 'NC'
        clean_dnouns = clean(dnouns[k])
        if k == len(dnouns) - 1:
            noun_type = 'NC_head'
            dict_index = index
            processed_nouns.append(
                (index, clean_dnouns, category, case, gender, number, person, noun_type, postposition))
        else:
            processed_nouns.append((index, clean_dnouns, category, case, gender, number, person, noun_type, ''))

    if noun[0] in processed_postpositions_dict:
        processed_postpositions_dict[dict_index] = processed_postpositions_dict.pop(noun[0])
    if clean(noun[1]) in ('cp', 'conj', 'disjunct', 'span', 'widthmeas', 'depthmeas', 'distmeas', 'rate', 'timemeas', 'waw', 'calender', 'massmeas', 'heightmeas', 'spatial'):
        del processed_postpositions_dict[index]
    return processed_nouns

def handle_unprocessed_all(outputData, processed_nouns):
    """swapping gender info that does not exist in dictionary."""
    output_data = outputData.strip().split(" ")
    has_changes = False
    reprocess_list = []
    dataIndex = 0  # temporary [to know index value of generated word from sentence]
    for data in output_data:
        dataIndex = dataIndex + 1
        if data[0] == '#':
            for i in range(len(processed_nouns)):
                if round(processed_nouns[i][0]) == dataIndex:
                        if processed_nouns[i][7] != 'proper':
                            temp = list(processed_nouns[i])
                            temp[4] = change_gender(processed_nouns[i][4])
                            #temp[4] = 'f' if processed_nouns[i][4] == 'm' else 'm'
                            reprocess_list.append(['n', i, processed_nouns[i][0],temp[4], temp[7]])
                            processed_nouns[i] = tuple(temp)
                            has_changes = True
                            log(f'{temp[1]} reprocessed as noun with new gen:{temp[4]}.')
    return has_changes, reprocess_list, processed_nouns

def handle_unprocessed(index_data,depend_data,outputData, processed_nouns):
    """swapping gender info that does not exist in dictionary."""
    output_data = outputData.strip().split(" ")
    has_changes = False
    # dataIndex = 0  # temporary [to know index value of generated word from sentence]
    for dataIndex,data in enumerate(output_data):
        # #print(data,output_data,'df')
        if data[0] == '#':
            for i in range(len(processed_nouns)):
                # #print(processed_nouns[i][0],'dff')
                if dataIndex in index_data:
                    ind = index_data.index(dataIndex)
                    if round(processed_nouns[i][0]) == ind:
                        # #print(processed_nouns[i][2],depend_data[i].split(':')[1],'klm')
                        if processed_nouns[i][2]=='n' and depend_data[i].split(':')[1]=='k1s':
                            # #print('klm')
                            has_changes = True
                            temp = list(processed_nouns[i])
                            temp[2] = 'adj'
                            # temp[4] = 'f' if processed_nouns[i][4] == 'm' else 'm'
                            processed_nouns[i] = tuple(temp)
                        if processed_nouns[i][7] not in ('proper','NC','CP_noun', 'abs', 'vn'):
                        #if not processed_nouns[i][7] == 'proper' and not processed_nouns[i][7] == 'NC' and not processed_nouns[i][7] == 'CP_noun':
                            has_changes = True
                            temp = list(processed_nouns[i])
                            temp[4] = 'f' if processed_nouns[i][4] == 'm' else 'm'
                            processed_nouns[i] = tuple(temp)
                            log(f'{temp[1]} reprocessed as noun with gen:{temp[4]}.')
                        else:
                            break
    # #print(processed_nouns,'nn')
    return has_changes, processed_nouns

def nextNounData_fromFullData(fromIndex, PP_FullData):
    index = fromIndex
    # #print(index,'ind',PP_FullData)
    for data in PP_FullData:
        if data[0]==index and data[2] == 'n':
            return data

    return ()
def is_next_word_noun(index,processed_nouns):
    for data in processed_nouns:
        if data[0]==index and data[2]=='n':
            return data
            # return data
    else:
        return False

def nextNounData(fromIndex, word_info):
    #for NC go till NC_head and return that tuple
    # index = fromIndex
    # for i in range(len(word_info)):
    #     for data in word_info:
    #         if index == data[0]:
    #             if data[3] != '' and index != fromIndex:
    #                 return data
    index = fromIndex
    # #print(index,'indx')
    for data in word_info:
        # if index == data[0] and data[3] != '':
        data=list(data)
        if index == str(data[0]):
            if 'female' in data[2]:
                data[2]='f'
            elif 'male' in data[2]:
                data[2]='m'
            if 'pl' in data[3]:
                data[3]='p'
            elif data[3]!='':
                data[3]='s'
            data=tuple(data)
            return data
                # if ':' in data[4]:
                #     index = int(data[4][0])
    return False

def fetchNextWord(index, words_info):
    next_word = ''
    for data in words_info:
        if index == data[0]:
            next_word = clean(data[1])
    return next_word

def change_gender(current_gender):
    """
    >>> change_gender('m')
    'f'
    >>> change_gender('f')
    'm'
    """
    return 'f' if current_gender == 'm' else 'm'

def set_gender_make_plural(processed_words, g, num):
    process_data = []
    # for all k1s and main verb change gender to female and number to plural
    for i in range(len(processed_words)):
        word_list = list(processed_words[i])
        if word_list[2] == 'adj':
            # 4th index - gender, 5th index - number
            word_list[4] = g
            word_list[5] = num
        elif word_list[2] == 'v':
            # 3rd index - gender, 4th index - number
            word_list[3] = g
            word_list[4] = num
        process_data.append(tuple(word_list))
    return process_data

def set_main_verb_tam_zero(verb: Verb):
    verb.tam = 0
    return verb

def set_tam_for_nonfinite(dependency):
    '''
    Sets the TAM (Tense-Aspect-Mood) for non-finite verb forms based on the given dependency code.

    Parameters:
        dependency (str): The dependency code indicating the type of non-finite form.

    Returns:
        str: The TAM code for the given non-finite form.

    Examples:
        >>> set_tam_for_nonfinite('rvks')
        'adj_wA_huA'
        >>> set_tam_for_nonfinite('rbks')
        'yA_huA'
        >>> set_tam_for_nonfinite('rsk')
        'wA_huA'
        >>> set_tam_for_nonfinite('rpk')
        'kara'
    '''
    tam = {
        # 'rvks': 'adj_wA_huA',
        'rpk': 'kara',
        'rsk': 'adj_wA_huA',
        # 'rbks': 'adj_yA_huA',
        # 'rblpk': 'nA',
        # 'rbk': 'yA_gayA',
    }.get(dependency, '')
    return tam

def update_ppost_dict(data_index, param):
    # whether entry exists or not, param is updated in ppost_dict
    processed_postpositions_dict[data_index] = param

def extract_tamdict_hin():
    extract_tamdict = []
    try:
        with open(application.repository.constant.TAM_DICT_FILE, 'r') as tamfile:
            for line in tamfile.readlines():
                hin_tam = line.strip()
                if hin_tam:  # Ensure the line is not empty
                    extract_tamdict.append(hin_tam)
        # #print(extract_tamdict)
        return extract_tamdict
    except FileNotFoundError:
        log('TAM Dictionary File not found.', 'ERROR')
        sys.exit()

def extract_gnp_noun(noun_data):
    gender = 'm'
    number = 's'
    person = 'a'

    if len(noun_data):
        noun_term = noun_data[1]
        if check_is_digit(noun_term):
            noun_term = noun_term
        elif '+' in noun_term:
            cn_terms = noun_term.strip().split('+')
            for i in range(len(cn_terms)):
                if i == len(cn_terms) - 1:
                    noun_term = clean(cn_terms[i])
        else:
            noun_term = clean(noun_term)

        #Setting gender
        seman_data = noun_data[2].strip()
        #seman_info_lst = seman_data.split()
        if len(seman_data) > 0:
            if 'female' in seman_data:
                gender = 'f'
            elif 'male' in seman_data:
                gender = 'm'
        else:
            tags = find_tags_from_dix(noun_term)
            # #print(tags,'tags2')
            if '*' not in tags['form']:
                gender = tags['gen']

        #Setting number
        if len(noun_data[3]):
            # number = noun_data[3].strip()[0]
            if noun_data[3] =='':
                number = 's'
            elif noun_data[3]=='pl':
                number = 'p'
            # number = noun_data[3].strip()[3]

        #Setting person
        if noun_term == 'speaker':
            person = 'u'
        elif noun_term == 'addressee':
            person = 'm'
        else:
            person = 'a'
    return gender, number, person

def extract_gnp(data):
    gender = 'm'
    number = 's'
    person = 'a'

    if len(data):
        term = clean(data[1])

        # Setting gender
        seman_data = data[2].strip()
        # seman_info_lst = seman_data.split()
        if len(seman_data) > 0:
            if 'female' in seman_data:
                gender = 'f'
            elif 'male' in seman_data:
                gender = 'm'

        # Setting number
        if len(data[3]):
            if data[3]=='pl':
                number = 'p'
            else:
                number = 's'

        # Setting person
        if term == 'speaker':
            person = 'u'
        elif term == 'addressee':
            person = 'm'
        else:
            person = 'a'
    # #print(number,'gl')
    return gender, number, person

def add_postposition(transformed_fulldata,index_data,depend_data, processed_postpositions):
    '''Adds postposition to words wherever applicable according to rules.'''
    PPFulldata = []
    # #print(depend_data,'dpdd')
    for i, ele in enumerate(depend_data):
        if ele.split(':')[1] == 'rs':
            # #print(index_data,i)
            ind0, ind1 = index_data[i-1], index_data[i]
            if ind0 in processed_postpositions_dict:
                processed_postpositions_dict[ind1] = processed_postpositions_dict.pop(ind0)
    
    # #print(processed_postpositions,'psp')
    for data in transformed_fulldata:
        index = data[0]
        if index in processed_postpositions:
            temp = list(data)
            ppost = processed_postpositions[index]
            if ppost != None and (temp[2] == 'n'or temp[2] == 'vn' or temp[2] == 'other'):
                temp[1] = temp[1] + ' ' + ppost
            data = tuple(temp)
        PPFulldata.append(data)
    return PPFulldata

def add_discourse_elements(discourse_data,spkview_data,sp_data, POST_PROCESS_OUTPUT):
    if len(discourse_data) <= 0:
        return POST_PROCESS_OUTPUT
    
    if isinstance(discourse_data, list):
        for data_values in discourse_data:
            if data_values!='' and 'coref' not in data_values:
                data_values=data_values.split(':')[1]
                # for element in repository.constant.discourse_dict:
                #     if element == data_values:
                # if data_values == 'samuccaya' and spkview_data in repository.constant.spkview_list:
                if 'BI_1' in spkview_data:
                    POST_PROCESS_OUTPUT = 'balki ' + POST_PROCESS_OUTPUT
                    break
                elif 'samAveSI' in spkview_data:
                    POST_PROCESS_OUTPUT = 'isake sAWa-sAWa ' + POST_PROCESS_OUTPUT
                    break
                elif 'alAvA_1' in spkview_data:
                    POST_PROCESS_OUTPUT = 'isake alAvA ' + POST_PROCESS_OUTPUT
                    break
                elif 'awirikwa' in spkview_data:
                    POST_PROCESS_OUTPUT = 'isake awirikwa ' + POST_PROCESS_OUTPUT
                    break
                elif 'nahIM' in spkview_data:
                    POST_PROCESS_OUTPUT = 'nahIM wo ' + POST_PROCESS_OUTPUT
                    break
                
                elif data_values in application.repository.constant.discourse_dict and isinstance(application.repository.constant.discourse_dict[data_values], str):
                    POST_PROCESS_OUTPUT = application.repository.constant.discourse_dict[data_values] + " " + POST_PROCESS_OUTPUT
                
                elif data_values in application.repository.constant.discourse_dict and isinstance(application.repository.constant.discourse_dict[data_values], list):
                    for i, value in enumerate(application.repository.constant.discourse_dict[data_values]):
                        separator = '/' if i != 0 else ' '
                        # separator = '/'
                        POST_PROCESS_OUTPUT = value + separator + POST_PROCESS_OUTPUT
                if 'nA kevala/' in POST_PROCESS_OUTPUT:
                    POST_PROCESS_OUTPUT = POST_PROCESS_OUTPUT.replace('nA kevala/', '')

    else:
        # for data_values in discourse_data:
        if discourse_data:
            # discourse_data=discourse_data.split(':')[1]
            if discourse_data in application.repository.constant.discourse_dict:
                if 'AvaSyakawApariNAma' in discourse_data and sp_data=='nahIM wo':
                    POST_PROCESS_OUTPUT = sp_data + " " + POST_PROCESS_OUTPUT
                elif isinstance(application.repository.constant.discourse_dict[discourse_data], str):
                    POST_PROCESS_OUTPUT = application.repository.constant.discourse_dict[discourse_data] + " " + POST_PROCESS_OUTPUT
                elif isinstance(application.repository.constant.discourse_dict[discourse_data], list):
                    for i in range(len(application.repository.constant.discourse_dict[discourse_data])):
                        if i!=0:
                            POST_PROCESS_OUTPUT = application.repository.constant.discourse_dict[discourse_data][i]+ '/'+ POST_PROCESS_OUTPUT
                        else:
                            POST_PROCESS_OUTPUT = application.repository.constant.discourse_dict[discourse_data][i] + " " + POST_PROCESS_OUTPUT
    return POST_PROCESS_OUTPUT

# def nakeval_balki(output_list):
#     if 'BI_1' in spkview_dict


def add_adj_to_noun_attribute(key, value):
    if key is not None:
        if key in application.repository.constant.noun_attribute:
            application.repository.constant.noun_attribute[key][0].append(value)
        else:
            application.repository.constant.noun_attribute[key] = [[],[]]

def add_verb_to_noun_attribute(key, value):
    if key is not None:
        if key in application.repository.constant.noun_attribute:
            application.repository.constant.noun_attribute[key][1].append(value)
        else:
            application.repository.constant.noun_attribute[key] = [[], []]

def add_spkview(full_data, spkview_dict):
    transformed_data = []
    for data in full_data:
        index = data[0]
        if index in spkview_dict:
            temp = list(data)
            spkview_info = spkview_dict[index]
            for info in spkview_info:
                tag = info[0]
                val = info[1]
                if tag == 'before':
                    temp[1] = val + ' ' + temp[1]
                elif tag == 'after':
                    temp[1] = temp[1] + ' ' + val
                data = tuple(temp)
        transformed_data.append(data)
    return transformed_data

def add_MORPHO_SEMANTIC(full_data, MORPHO_SEMANTIC_DICT):
    transformed_data = []
    for data in full_data:
        index = data[0]
        if index in MORPHO_SEMANTIC_DICT:
            temp = list(data)
            term = MORPHO_SEMANTIC_DICT[index]
            for t in term:
                tag = t[0]
                val = t[1]
                if tag == 'before':
                    temp[1] = val + ' ' + temp[1]
                else:
                    temp[1] = temp[1] + ' ' + val
            data = tuple(temp)
        transformed_data.append(data)
    return transformed_data

def add_construction(transformed_data, construction_dict):
    Constructdata = []
    dependency_check=['k7p','k7t']
    add_words_list=['meM','ko','ke','kI','kA']
    depend_data1=''
    for data in transformed_data:
        index = data[0]
        if len(data)==9:
            depend_data1=data[8]
        if index in construction_dict:
            temp = list(data)
            term = construction_dict[index]
            for t in term:
                tag = t[0]
                val = t[1]
                if tag == 'before':
                    temp[1] = val + ' ' + temp[1]
                else:
                    if val == ',':
                        temp[1] = temp[1] + val
                    elif val == '-':
                        temp[1] = temp[1] + val
                    else:
                        if depend_data1!='' and depend_data1 in add_words_list and depend_data1 in temp[1]:
                            temp[1] = temp[1].split()[0] + ' ' +val
                        else:
                            temp[1] = temp[1] + ' ' +val
            # if clean(temp[1]) not in ('cp','conj','disjunct','span','widthmeas','depthmeas','distmeas','rate','timemeas','waw','calender','massmeas','heightmeas','spatial'):
            #     # del(temp)
            data = tuple(temp)
        Constructdata.append(data)
        
    return Constructdata

def add_additional_words(additional_words_dict, processed_data):
    additionalData = []
    for data in processed_data:
        index = data[0]
        if index in additional_words_dict:
            temp = list(data)
            term = additional_words_dict[index]
            for t in term:
                tag = t[0]
                val = t[1]
                if tag == 'before':
                    temp[1] = val + ' ' + temp[1]
                else:
                    temp1=temp[1].split()
                    if len(temp1)>=2 and temp1[1]=='ko':
                        temp1[1] = val
                        temp[1] = ' '.join(temp1)
                    else:
                        temp[1] = temp[1] + ' ' + val
            data = tuple(temp)
        additionalData.append(data)
    return additionalData

def fetch_NC_head(i, processed_words):
    for data in processed_words:
        temp = tuple(data)
        if int(temp[0]) == int(i) and temp[7] == 'NC_head':
            return temp[0]

def auxmap_hin(aux_verb):
    """
    Finds auxiliary verb in auxiliary mapping file. Returns its root and tam.
    >>> auxmap_hin('sakawA')
    ('saka', 'wA')
    """
    # #print(aux_verb)
    # try:
    with open(application.repository.constant.AUX_MAP_FILE, 'r') as tamfile:
        for line in tamfile.readlines():
            # #print(line,'lll')
            aux_mapping = line.strip().split(',')
            if aux_mapping[0] == aux_verb:
                return aux_mapping[1], aux_mapping[2]
    log(f'"{aux_verb}" not found in auxiliary mapping.', 'WARNING')
    #     return None, None       # TODO Figure out the fallback
    # except FileNotFoundError:
    #     log('auxiliary Mapping File not found.', 'ERROR')
    #     sys.exit()

def update_additional_words_dict(index, tag, add_word):
    value = (tag, add_word)
    value_found = False
    if index in additional_words_dict:
        value_list = additional_words_dict[index]
        for data in value_list:
            if data[0] == tag and data[1] == add_word:
                value_found = True
        if not value_found:
            additional_words_dict[index].append(value)
    else:
        additional_words_dict[index] = [value]

def to_tuple(verb: Verb):
    return (verb.index, verb.term, verb.category, verb.gender, verb.number, verb.person, verb.tam, verb.case, verb.type)

def postposition_finalization(processed_nouns, processed_pronouns,processed_foreign_words, words_info):
    for data in words_info:
        data_index = data[0]
        dep = data[4].strip().split(':')[1]
        head = data[4].strip().split(':')[0]

        if dep == 'r6':
            for noun in processed_nouns:
                index = noun[0]
                case = noun[3]
                if head == str(index) and case == 'o':
                    update_ppost_dict(data_index, 'ke')

            for pronoun in processed_pronouns:
                index = pronoun[0]
                case = pronoun[3]
                if head == str(index) and case == 'o':
                    update_ppost_dict(data_index, 'ke')

            # for nominal_v in process_nominal_form:
            #     index = nominal_v[0]
            #     case = nominal_v[3]
            #     if head == str(index) and case == 'o':
            #         update_ppost_dict(data_index, 'ke')
            # for f_word in processed_foreign_words:
            #     index = f_word[0]
            #     case = f_word[3]
            #     if head == str(index) and case == 'o':
            #         update_ppost_dict(data_index, 'ke')

def collect_processed_data(index_data,processed_foreign_words,processed_pronouns, processed_nouns, processed_adjectives, processed_verbs,
                           processed_auxverbs, processed_indeclinables, processed_others):
    """collect sort and return processed data."""
    # sorted_data=sorted(processed_foreign_words+processed_pronouns + processed_nouns + processed_adjectives + processed_verbs + processed_auxverbs + processed_indeclinables + processed_others)
    combined_data = sorted(processed_foreign_words + processed_pronouns + processed_nouns + processed_adjectives +
                     processed_verbs + processed_auxverbs + processed_indeclinables + processed_others)

    # Initialize an empty list to hold the sorted data
    sorted_data = []

    # Create a set from index_data for quick lookup
    # index_set = set(map(float, index_data))  # Convert indices to float for comparison

    # Filter and sort combined data based on the order in index_data
    for index in index_data:
        # index = int(index)
        sorted_data.extend([item for item in combined_data if int(item[0]) == index])
    return sorted_data
    # return sorted_data

def join_compounds(transformed_data, construction_data):
    '''joins compound words without spaces'''
    resultant_data = []
    prevword = ''
    previndex = -1

    for data in transformed_data:
        if (data[0]) == previndex and data[2] == 'n':
            temp = list(data)
            temp[1] = prevword + ' ' + temp[1]
            data = tuple(temp)
            resultant_data.pop()
        resultant_data.append(data)
        previndex = data[0]
        prevword = data[1]
    return resultant_data

def populate_morpho_semantic_dict(index_data,gnp_info, PPfull_data,words_info):
    populate_morpho_semantic_dict = False
    morpho_seman = ['compermore','comperless','comper_more', 'comper-more', 'comper_less', 'comper-less', 'superl', 'mawupa', 'mawup','dviwva']
    a = 'after'
    b = 'before'
    
    for i,term in enumerate(gnp_info):
        input_string = gnp_info[i]
        # matches = re.findall(r'\[(.*?)\]', input_string)
        # strings = [s.strip() for s in matches]

        # for term in strings:
        # #print(morpho_seman)
        if term in morpho_seman:
            populate_morpho_semantic_dict = True
            if term == 'superl':
                temp = (b, 'sabase')

            elif term in ('compermore','comper_more', 'comper-more'):
                # #print('var')
                temp = (b, 'aXika')
            # elif term in ('quantless'):
            #     # #print('var')
            #     temp = (a, 'se kama')
            # elif term in ('quantmore'):
            #     # #print('var')
            #     temp = (a, 'se aXika')
            elif term in ('comperless','comper_less', 'comper-less'):
                temp = (b, 'kama')
            elif term == 'dviwva':
                dup_word = clean(words_info[i][1])
                # #print(dup_word,'dupw')
                if dup_word in PPfull_data[i][1]:
                    dup_word = '-' + dup_word
                    # Convert the specific element to a list
                    # PPfull_data[i] = list(PPfull_data[i])
                    # # Make the modification
                    # PPfull_data[i][1] = PPfull_data[i][1].replace(dup_word, dup_word1)
                    # # Convert back to a tuple
                    # PPfull_data[i] = tuple(PPfull_data[i])
                    temp = (a, dup_word)
            else:
                # fetch GNP of next noun
                # curr_index = 
                # #print(index_data[i+1],i,'ndd')
                # #print(PPfull_data)
                noun_data = nextNounData_fromFullData(index_data[i+1], PPfull_data)
                # #print(noun_data)
                if noun_data != ():
                    g = noun_data[4]
                    n = noun_data[5]
                    p = noun_data[6]
                    if g == 'f':
                        temp = (a, 'vAlI')
                    elif n == 'p':
                        temp = (a, 'vAle')
                    elif n == 's':
                        temp = (a, 'vAlA')
            if index_data[i] in MORPHO_SEMANTIC_DICT:
                MORPHO_SEMANTIC_DICT[index_data[i]].append(temp)
            else:
                MORPHO_SEMANTIC_DICT[index_data[i]] = [temp]
    return populate_morpho_semantic_dict,PPfull_data

def join_indeclinables(transformed_data, processed_indeclinables, processed_others):

    """Joins Indeclinable data with transformed data and sort it by index number."""
    return transformed_data + processed_indeclinables + processed_others

# def rearrange_sentence(fulldata,coref_list):
#     '''Function comments'''
#     finalData = fulldata
#     final_words = [x[1].strip() for x in finalData]
#     r_s=" ".join(final_words)
#     return r_s

def rearrange_sentence(fulldata, coref_list):
    '''Function to rearrange sentence based on coreference list'''
    
    # Create a dictionary for quick lookup from coref_list
    coref_dict = {index: value for index, value in coref_list}
    finalData = []
    
    for item in fulldata:
        index = item[0]  # Get the index from the pp_full list
        word = item[1]  # Get the word
        
        # Check if the current index exists in the coref_dict
        if index in coref_dict:
            # Append the coreference word in parentheses
            word += f" ({coref_dict[index].split()[0]})"
        
        # Reconstruct the tuple with the modified word
        modified_item = (item[0], word, *item[2:])
        
        finalData.append(modified_item)
    # Join the words for the final rearranged sentence
    # final_words = [x[1].strip() for x in finalData]
    # r_s = " ".join(final_words)
    final_words = []
    for i in range(len(finalData)):
        word = finalData[i][1].strip()
        
        # If the word ends with a hyphen, join without space
        if i > 0 and final_words[-1].endswith('-'):
            final_words[-1] = final_words[-1] + word
        else:
            final_words.append(word)
    
    r_s = " ".join(final_words)
    # #print(r_s,'rsss')
    return r_s

def collect_hindi_output(source_text):
    """Take the output text and find the hindi text from it."""
    hindi_format = WXC(order="wx2utf", lang="hin")
    if source_text and '_' in source_text:
        source_text = source_text.replace('_', ' ')

    generate_hindi_text = hindi_format.convert(source_text)
    return generate_hindi_text
#         previndex = data[0]
#         prevword = data[1]
#
#     return resultant_data

# def process_coref(index_data,processed_words,input_text):
#     coref_list = []
#     folder_path = sys.argv[1].split('/')[0]
#     for i in range(len(input_text)):
#         sub_coref_list=[]
#         if 'coref' in input_text[i] and '.' in input_text[i]:
#             file_name_line = input_text[i]
#             file_name = file_name_line.split('.')[0]
#             digit = file_name_line.split('.')[1].split(':')[0]
#             file_path = os.path.join(folder_path, f'{file_name}')
#             # Add .txt to file name if file not found
#             if not os.path.exists(file_path):
#                 file_path += '.txt'
#             if not os.path.exists(file_path):
#                 raise FileNotFoundError(f"File '{file_path}' not found")
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 file_contents = file.readlines()

#             ind=file_contents[2].split(',')
#             cleaned_ind = [item.strip() for item in ind]
#             for k,val in enumerate(cleaned_ind): 
#                 if val == digit:
#                     sub_coref_list.append(index_data[i])
#                     coref_word = clean(file_contents[1].split(',')[k])
#                     sub_coref_list.append(coref_word)
#         elif 'coref' in input_text[i]:
#             sub_coref_list.append(index_data[i])
#             indx=int(input_text[i].split(':')[0])
#             for processed_word in processed_words:
#                 if processed_word[0]==indx:  # Check if indx is composed entirely of digits
#                     coref_word = processed_word[1]
#                     sub_coref_list.append(coref_word)
#                     break
#         if sub_coref_list!=[]:
#             coref_list.append(sub_coref_list)
#     return coref_list

# def process_coref(val, index_data,processed_words, json_data):
#     coref_list = []

#     for i, sentence in enumerate(json_data):
#         sub_coref_list = []
#         tokens = sentence["tokens"]

#         for token in tokens:
#             if "coref" in token["discourse_rel"]:  # Check if the token has a coreference relation
#                 discourse_head = token["discourse_head"]

#                 if '.' in discourse_head:  # If '.' is present in discourse_head
#                     # Split to extract relevant parts (similar to file_name and digit)
#                     file_name = discourse_head.split('.')[0]  # This was previously file_name
#                     digit = discourse_head.split('.')[1]  # Similar to digit


#                     if val == digit:
#                         sub_coref_list.append(index_data[i])  # Add the index data
#                         coref_word = clean(file_contents[1].split(',')[k])  # Get coref word
#                         sub_coref_list.append(coref_word)

#                 else:  # No '.' in discourse_head, simpler case
#                     sub_coref_list.append(index_data[i])  # Add index data
#                     indx = int(token["discourse_rel"])  # Extract coref index

#                     # Find the coref word in processed_words based on the index
#                     for processed_word in processed_words:
#                         if processed_word[0] == indx:  # If the index matches
#                             coref_word = processed_word[1]
#                             sub_coref_list.append(coref_word)
#                             break

#             if sub_coref_list:  # Append to coref_list if there's any coreference info
#                 coref_list.append(sub_coref_list)

#     return coref_list

# def get_file_data_from_json(file_name, json_data):
#     # Search for the specific file-like structure inside the JSON data.
#     for sentence in json_data:
#         if sentence.get("usr_id") == file_name:
#             # Return relevant fields as if they were lines in a file
#             tokens = [token["concept"] for token in sentence["tokens"]]
#             indices = [str(token["index"]) for token in sentence["tokens"]]
#             return ["", ",".join(tokens), ",".join(indices)]
#     return None

# def reset_global_dicts():
#     global additional_words_dict, processed_postpositions_dict, construction_dict, spkview_dict, MORPHO_SEMANTIC_DICT
#     additional_words_dict.clear()
#     processed_postpositions_dict.clear()
#     construction_dict.clear()
#     spkview_dict.clear()
#     MORPHO_SEMANTIC_DICT.clear()

if __name__ == '__main__':
    import doctest
    doctest.run_docstring_examples(identify_complete_tam_for_verb, globals())

# ==============================================