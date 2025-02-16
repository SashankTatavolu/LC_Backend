import json
from application.repository.common_v4 import *
# import updated.repository.constant

spkview_list = ['BI_1', 'samAveSI', 'alAvA', 'awirikwa']
discourse_list = ['samuccaya', 'AvaSyakawApariNAma', 'kAryakAraNa', 'pariNAma', 'viroXIxyowaka', 'vyaBicAra', 
                  'viroXI', 'anyawra', 'samuccaya x', 'arWAwa', 'uwwarkAla', 'kAryaxyowaka', 'uxaharaNasvarUpa']

def extract_discourse_values(data, segment_id):
    # Initialize a list to store discourse values and a flag for specific data
    discourse_values = []
    # #print(data)
    # Assuming 'data' is a JSON string
    data = json.loads(data)
    sp_data = ''
    #print('nnnnnnnm')
    # Iterate through each entry in the JSON data
    for entry in data:
        # usr_sub_id = entry.get('usr_id')
        rows = entry.get('tokens', [])
        # #print(discourse_head)
        # Collect discourse values from each row
        for row in rows:
            discourse_value = row.get('discourse_rel', '')
            discourse_head = row.get('discourse_head', '')
            if discourse_value:
                #print(discourse_head)
                if segment_id == discourse_head.split('.')[0] and 'coref' not in discourse_value:
                    spkview_value = row.get('speaker_view', '')

                    # Check if specific conditions are met
                    if 'AvaSyakawApariNAma' in discourse_value and 'nahIM' in spkview_value:
                        sp_data = 'nahIM wo'
                        return discourse_value, sp_data
                    
                    # Return default values if conditions are not met
                    
                    return discourse_value, None

    # Return default values if no matching discourse value is found
    
    return None, None

def extract_spkview_values(data, segment_id, POST_PROCESS_OUTPUT):
    # Iterate through each entry in the JSON data
    data = json.loads(data)
    for entry in data:
        usr_sub_id = entry.get('usr_id')
        rows = entry.get('tokens', [])

        # Collect discourse values from each row
        for row in rows:
            discourse_value = row.get('discourse_rel', '')
            discourse_head = row.get('discourse_head', '')
            spkview_value = row.get('speaker_view', '')
            
            if discourse_value and ':' in discourse_value:
                disc_value = discourse_value.split(':')[1]
                if discourse_value in discourse_list and spkview_value in spkview_list:
                    # discourse_id = discourse_value.split('.')[0]
                    if segment_id == discourse_head.split('.')[0]:
                        # Process based on spkview_value
                        if 'BI_1' in spkview_value:
                            POST_PROCESS_OUTPUT = 'nA kevala ' + POST_PROCESS_OUTPUT
                            return POST_PROCESS_OUTPUT

                        # Additional conditions can be uncommented and modified as needed
                        # if 'nahIM' in spkview_value and 'AvaSyakawApariNAma' in discourse_value:
                        #     POST_PROCESS_OUTPUT = 'nahIM wo ' + POST_PROCESS_OUTPUT
                        #     return POST_PROCESS_OUTPUT

                        # if 'samAveSI' in spkview_value:
                        #     POST_PROCESS_OUTPUT = 'isake sAWa-sAWa ' + POST_PROCESS_OUTPUT
                        #     return POST_PROCESS_OUTPUT

                        # if 'alAvA_1' in spkview_value:
                        #     POST_PROCESS_OUTPUT = 'isake alAvA ' + POST_PROCESS_OUTPUT
                        #     return POST_PROCESS_OUTPUT

                        # if 'awirikwa' in spkview_value:
                        #     POST_PROCESS_OUTPUT = 'isake awirikwa ' + POST_PROCESS_OUTPUT
                        #     return POST_PROCESS_OUTPUT

                        # if disc_value == 'AvaSyakawApariNAma':
                        #     POST_PROCESS_OUTPUT = 'yaxi ' + POST_PROCESS_OUTPUT
                        #     return POST_PROCESS_OUTPUT

                        # if disc_value == 'vyaBicAra':
                        #     POST_PROCESS_OUTPUT = 'yaxyapi ' + POST_PROCESS_OUTPUT
                        #     return POST_PROCESS_OUTPUT

    # Return POST_PROCESS_OUTPUT if no conditions are met
    return POST_PROCESS_OUTPUT

def process_coref(val, index_data,processed_words,json_data,discourse_data,coref_list):
    json_data = json.loads(json_data)
    #print(discourse_data,'dddddddddd')
    #print(json_data)
    for i in range(len(discourse_data)):
        sub_coref_list=[]
        if 'coref' in discourse_data[i] and '.' in discourse_data[i]:
            discourse_id=discourse_data[i].split('.')[0]
            discourse_head=discourse_data[i].split('.')[1].split(':')[0]
            
            for j, sentence in enumerate(json_data):
                usr_sub_id = sentence.get('usr_id')
                tokens = sentence.get("tokens",[])
                if usr_sub_id == discourse_id:
                    for token in tokens:
                        #print(discourse_head,'dhhh')
                        ind=token.get('index')
                        if str(ind) == discourse_head:
                            sub_coref_list.append(index_data[i])  # Add the index data
                            concpt=token.get('concept')
                            coref_word = clean(concpt)  # Get coref word
                            sub_coref_list.append(coref_word)
                            #print(sub_coref_list,'cpcccc')
                            break

        elif 'coref' in discourse_data[i]:  # No '.' in discourse_head, simpler case
            # for j, sentence in enumerate(json_data):
            #     sub_coref_list = []
            #     usr_sub_id = sentence.get('usr_id')
            #     tokens = sentence.get("tokens",[])
            #     if val==usr_sub_id:
            #         for token in tokens:
            #             sub_coref_list.append(index_data[i])  # Add index data
            #             indx = token.get('discourse_head', '')  # Extract coref index
            #             indx=int(indx)
            #             # Find the coref word in processed_words based on the index
            #             for processed_word in processed_words:
            #                 #print(processed_word)
            #                 if processed_word[0] == indx:  # If the index matches
            #                     coref_word = processed_word[1]
            #                     sub_coref_list.append(coref_word)
            #                     #print(sub_coref_list,'kkkk')
            #                     break
            sub_coref_list.append(index_data[i])
            indx=int(discourse_data[i].split(':')[0])
            for processed_word in processed_words:
                if processed_word[0]==indx:  # Check if indx is composed entirely of digits
                    coref_word = processed_word[1]
                    sub_coref_list.append(coref_word)
                    break

        if sub_coref_list:  # Append to coref_list if there's any coreference info
            coref_list.append(sub_coref_list)

    return coref_list
# # Example usage:
# json_input = [
#     {
#         "text": "यद्यपि राम बहुत बीमार था",
#         "usr_id": "Test_1_0008",
#         "sent_type": "affirmative",
#         "tokens": [
#             {
#                 "index": 1,
#                 "concept": "rAma",
#                 "tam": None,
#                 "is_combined_tam": False,
#                 "type": None,
#                 "dep_rel": "-",
#                 "dep_head": "-",
#                 "sem_category": "per/male"
#             },
#             {
#                 "index": 2,
#                 "concept": "bahuwa_1",
#                 "tam": None,
#                 "is_combined_tam": False,
#                 "type": None,
#                 "dep_rel": "-",
#                 "dep_head": "-"
#             },
#             {
#                 "index": 3,
#                 "concept": "bImAra_1",
#                 "tam": None,
#                 "is_combined_tam": False,
#                 "type": None,
#                 "dep_rel": "-",
#                 "dep_head": "-"
#             },
#             {
#                 "index": 4,
#                 "concept": "hE_1",
#                 "tam": "pres",
#                 "is_combined_tam": True,
#                 "type": None,
#                 "dep_rel": "-",
#                 "dep_head": "-",
#                 "discourse_head": "sent_2.3",
#                 "discourse_rel": "vyaBicAra"
#             }
#         ]
#     },
#     {
#         "text": "फिर भी वह स्कूल गया।",
#         "usr_id": "Test_1_0009",
#         "sent_type": "affirmative",
#         "tokens": [
#             {
#                 "index": 1,
#                 "concept": "$wyax",
#                 "tam": None,
#                 "is_combined_tam": False,
#                 "type": "pron",
#                 "dep_rel": "-",
#                 "dep_head": "-",
#                 "discourse_head": "sent_1.1",
#                 "discourse_rel": "coref",
#                 "speaker_view": "distal"
#             },
#             {
#                 "index": 2,
#                 "concept": "skUla_1",
#                 "tam": None,
#                 "is_combined_tam": False,
#                 "type": None,
#                 "dep_rel": "-",
#                 "dep_head": "-"
#             },
#             {
#                 "index": 3,
#                 "concept": "jA_1",
#                 "tam": "yA_1",
#                 "is_combined_tam": True,
#                 "type": None,
#                 "dep_rel": "-",
#                 "dep_head": "-"
#             }
#         ]
#     }
# ]


# segment_id = "sent_2.3"
# POST_PROCESS_OUTPUT = "default_output"

# # Extract discourse values
# discourse_value, sp_data = extract_discourse_values(json_input, segment_id)
# #print(f"Discourse Value: {discourse_value}, SP Data: {sp_data}")

# # Extract speaker view values
# output = extract_spkview_values(json_input, segment_id, POST_PROCESS_OUTPUT)
# #print(f"Post Process Output: {output}")