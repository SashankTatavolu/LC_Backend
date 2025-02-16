# TAM_DICT_FILE = 'tam_mapping.dat'
TAM_DICT_FILE = 'application/repository/tam_mapping_new.dat'
AUX_MAP_FILE = 'application/repository/auxillary_mapping.txt'
CAUSATIVE_MAP_FILE='application/repository/causative_mapping.txt'

# data lists
INDECLINABLE_WORDS = [
        'eKana','waWA','Ara','paranwu','kinwu','evaM','waWApi','kiCu',
        'wo','yaxi','wabe','awaH','kAraNa','kenanA','yeBAbe',
        'waKana','waKani','bA', 'nAhale','anyaWA', 'yaKana', 'naile',
        'yAwe','yaxi', 'aWabA','Aja','nA', 'yawa', 'wawa', 'yA','nahIM',]

UNITS = ['semI', 'kimI', 'mItara', 'lItara', 'kilomItara', 'kilolItara']

kriyAmUla=['viswqwa','prawIkRA','varNana']

# NON_FINITE_VERB_DEPENDENCY = ['rpk', 'rsk','rbk', 'rvks', 'rbks', 'rblpk', 'rblsk']
NON_FINITE_VERB_DEPENDENCY = ['rpk', 'rsk','rbk']
ADJECTIVE_DEPENDENCY = ['card', 'mod','meas', 'ord', 'intf','rvks','rbks']
# VERBAL_ADJECTIVE = ['rvks','rbks']
PRONOUN_TERMS = ['addressee', 'speaker', 'kyA', 'Apa','wyax', 'jo', 'koI', 'kOna', 'mEM','merA', 'saba', 'vaha', 'wU', 'wuma', 'yaha', 'kim','ve','ye','yax']
# NOMINAL_VERB_DEPENDENCY = ['rt', 'rh', 'k7p', 'k7t', 'k2']
NOMINAL_VERB_DEPENDENCY = ['rt', 'rh', 'k7p', 'k7t', 'k2','rblpk','rblsk','rblak','k1s']
# constants.py

noun_attribute = dict()
USR_row_info = [
    'root_words', 'index_data', 'seman_data', 'gnp_data', 'depend_data',
    'discourse_data', 'spkview_data', 'scope_data'
]
nA_list = [
    'nA_paDa', 'nA_padZA', 'nA_padA', 'nA_hE', 'nA_WA', 'nA_hogA', 'nA_cAhie',
    'nA_cAhiye'
]
spkview_list_b = [
    'jI', 'lagAwAra', 'kevala' ,'karIba','TIka','mAwra','basa','sirPa',
]
spkview_list_a = [
    'hI', 'BI', 'jI', 'wo','sI','ki','waka', 'lagaBaga', 'lagAwAra'
]
kisase_k2g_verbs = ['bola', 'pUCa', 'kaha', 'nikAla', 'mAzga']
reciprocal_verbs = ['mila', 'pyAra']
kisase_k5_verbs = ['dara', 'baca', 'rakSA']
kahAz_k5_verbs = ['A', 'uga', 'gira']

discourse_dict = {
    'samuccaya': ['Ora', 'evaM', 'waWA', 'nA kevala'],
    'AvaSyakawApariNAma': 'wo',
    'kAryakAraNa': ['kyoMki', 'cUzki', 'cUMki'],
    'pariNAma': ['isIlie', 'isalie', 'awaH', 'isake pariNAmasvarUpa', 'isI kAraNa', 'isa kAraNa'],
    'viroXI_xyowaka': 'jabaki',
    'vyaBicAra': ['waWApi', 'hAlAzki', 'Pira BI','isake bAvajZUxa'],
    'viroXI': ['lekina', 'kiMwu', 'paraMwu', 'isake viparIwa', 'viparIwa'],
    'anyawra': ['yA', 'aWavA'],
    'samuccaya x': ['isake alAvA', 'isake awirikwa', 'isake sAWa-sAWa', 'isake sAWa sAWa'],
    'arWAwa':['arWAwa','xUsre SabxoM meM'],
    'uwwarakAla':['bAxa meM', 'isake bAxa meM'],
    'kAryaxyowaka':'wAki',
    'uxaharaNasvarUpa':'uxAharaNa ke lie',
}
# spkview_list_for_discource=['BI_1','samAveSI','alAvA','awirikwa']
