def count_usr_entries(file_path):
    usr_count = 0
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip().startswith("<sent_id="):
                usr_count += 1
    return usr_count

file_path = '/home/sashank/Downloads/LC/Language_Communicator_Backend/application/data_insertions/sept-7-2022ICF-HD/sept-7-2022ICF-HD_hin_usr.txt'
usr_count = count_usr_entries(file_path)
print(f"Total number of USR entries: {usr_count}")
