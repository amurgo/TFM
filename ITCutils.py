import os
import re
import json
import pickle
import pandas as pd
import nltk
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from bs4 import Tag


def dict2json(dict_obj, file_name):
    """
    Save a dict to a json file in output_folder with a file_name given

    :param dict_obj: dictionary origin
    :param file_name: full path and file name destination  (path/some_name.json)
    :return: None
    """

    print("Saving to a file.")

    with open(file_name, 'w') as file_open:
        json.dump(dict_obj, file_open)

    print("\tDictionary saved at {}".format(file_name))


def json2dict(file_name):
    """
    Return dict where json file in output_folder with a file_name is loaded

    :param file_name: full path and file name origin  (path/some_name.json)
    :return: dictionary object
    """

    with open(file_name) as json_file:
        dict_obj = json.load(json_file)

    return dict_obj


def files_list_getter(path_name, extension, debug_flag=False):
    """
    Return a list of files in 'path_name' with a specific 'extension'
    If debug_flag is True -> print their name
    """
    files_list = []

    for file_name in os.listdir(path_name):
        if file_name.endswith('.' + extension):
            files_list.append(file_name)

    print("{} '{}' files found in '{}' folder".format(len(files_list), extension, path_name))

    if debug_flag:
        for file_name in files_list:
            print('\t' + file_name)

    return files_list


def headings_list_extractor(doc, debug_flag=False):
    """
    From a doc (docx Document Object) return headings list ([heading_text, heading_style])
    If debug_flag is True -> print list
    """
    headings_list = []

    for para in doc.paragraphs:
        try:
            if para.style.name.startswith('Heading') and re.search(r'^\w', para.text):
                headings_list.append([para.text, para.style.name])

                if debug_flag:
                    print('{} -> {}'.format(para.text, para.style.name))
        except:
            pass

    if len(headings_list) == 0:
        print('No headings found in document!')

    return headings_list


def chapter_text_extractor(doc, text_string, text_style, debug_flag=False):
    """
    From a doc (docx Document Object) return text (string) from one chapter
    with specific 'text_string' and 'text_style'

    Search until another paragraph with same style is found and extract all text in-between

    If debug_flag is True -> print chapter
    """

    chapter_list = []
    initial_para = -1

    for i, para in enumerate(doc.paragraphs):
        try:
            if (initial_para == -1) \
                    and (para.style.name == text_style) \
                    and (re.search(text_string.lower(), para.text.lower())):
                initial_para = i
                chapter_list.append(para.text)
            elif (initial_para != -1) and not (para.style.name == text_style):
                chapter_list.append(para.text)
            elif (initial_para != -1) and (para.style.name == text_style):
                break

        except:
            pass

    if initial_para == -1:
        print("'{}' with '{}' style not found!".format(text_string, text_style))
        return ''

    if debug_flag:
        print('\n'.join(chapter_list))

    return '\n'.join(chapter_list)


class DicText:
    def __init__(self):
        self.docs = {}
        self.utils = {'codes_dict': {},  # dict with file_name:code (key:value)
                      'files_list': [],  # list with file_name values
                      'last_code': 0,  # int with maximum code used in docs (0->no docs)
                      'last_update': str(datetime.today()),  # datetime from last dict update
                      'n_docs': 0}  # number of docs in dict

    def add(self, file_name, section_name, text_str, debug_flag=False, confirm=True):
        """
        Add information from a file_name (section_name: text_str) to a DictText object.
        Create new code and/or section if needed

        If debug_flag is True -> print dict update
        """

        section_list = ['file_name', 'text', 'headings', 'summary', 'lang', 'xml', 'TSM', 'policies']

        # Check section name
        if section_name not in section_list:
            print("'{}' is a section_name not valid, please change it to a valid name:\n{}"
                  .format(section_name, section_list))

        # Info from a new file
        if file_name not in self.utils['files_list']:

            # Check if file_name is a 4-digit code and then it keeps this file_name as key in DicText
            # new file, otherwise just as before, add one to last_code value
            # Need to verify if adding new information it is done in good order
            if re.findall(r'^\d{4}\Z', file_name[:-4]):
                if int(self.utils['last_code']) < int(file_name[:4]):
                    self.utils['last_code'] = file_name[:4]
                code_file = file_name[:4]

            else:
                self.utils['last_code'] = '{:04d}'.format(int(self.utils['last_code'])+1)
                code_file = self.utils['last_code']

            self.docs[code_file] = \
                dict(zip(section_list, [file_name] + [''] * len(section_list[1:])))
            self.utils['files_list'].append(file_name)
            self.utils['codes_dict'][file_name] = code_file
            self.utils['n_docs'] += 1

            if debug_flag:
                print("New information for '{}' file added".format(file_name))

        # Info from an existing file
        else:
            code_file = str(self.utils['codes_dict'][file_name])

            # Check for previous information
            if self.docs[code_file][section_name] != '' and confirm == True:
                # User confirmation message
                user_confirmation = input("Dict already has information in '{}' section for '{}' file!!\n"
                                          .format(section_name, file_name) +
                                          "This action will delete it for new one, are you sure? [y/n]  ")

                if user_confirmation == 'y':
                    pass

                else:
                    print('Execution cancelled')

        # Update section
        self.docs[code_file][section_name] = text_str

        # Update datetime
        self.utils['last_update'] = str(datetime.today())

        if debug_flag:
            print("'{}' section updated successfully".format(section_name))

    def load(self, file_name):
        print("Loading from {} file. ".format(file_name), end='')
        with open(file_name) as json_file:
            dict_obj = json.load(json_file)

        self.docs = dict_obj['docs']
        self.utils = dict_obj['utils']
        print('Done.')

    def save(self, file_name):
        print("Saving to a file.")
        dict_obj = dict(docs=self.docs, utils=self.utils)
        with open(file_name, 'w') as file_open:
            json.dump(dict_obj, file_open)

        print("\tDictext saved at {}".format(file_name))


def xml_headings_list_extractor(heading_text, soup_obj, debug_flag=False):
    """
    :param heading_text:
    :param soup_obj:
    :param debug_flag:
    :return:
    """
    list_not_headings = ['Link', 'P', 'NormalParagraphStyle']
    headings_list = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

    # Search chapter tag supposing heading_text is title beginning
    heading_tag_list = [x.parent for x in soup_obj.find_all(text=re.compile('^' + heading_text, re.I))
                        if x.parent.name not in list_not_headings]

    # Two or more heading candidates found
    if len(heading_tag_list) > 1:

        # If all candidates have a tag included in 'headings_list' -> chose the lower one
        if len([x for x in heading_tag_list if x.name.lower() in headings_list]) == len(heading_tag_list):
            heading_tag_list.sort(key=lambda x: x.name[1:])

        else:
            print('Unable to find heading tags: found {} heading tags candidates'.format(len(heading_tag_list)))

            if debug_flag:
                for candidate in heading_tag_list:
                    print('\t{}'.format(candidate))
            return 1, 1

    # No heading candidates found
    elif len(heading_tag_list) == 0:
        print("Unable to find heading tags, are you sure '{}' is a heading?".format(heading_text))
        return -1, -1

    heading_list = [x.string for x in soup_obj.find_all(heading_tag_list[0].name)]
    heading_tags = [x for x in soup_obj.find_all(heading_tag_list[0].name)]

    if debug_flag:
        print('Found {} headings:'.format(len(heading_list)))
        print(heading_list)

    return heading_list, heading_tags


def xml_table_parser(table_xml):
    headers_list = []
    data_list = []
    rows = table_xml.find_all('TR')

    for row in rows:

        # Add headers
        headers = row.find_all('TH')
        if len(headers) > 0:
            temp_head = []
            for header_element in headers:
                if len(header_element.get_text().strip()) > 0:
                    temp_head.append(header_element.get_text().strip())

            if temp_head != [] and temp_head not in headers_list:
                for x in temp_head:
                    if x not in headers_list:
                        headers_list.append(x)

        # Add elements
        cols = row.find_all('TD')
        if len(cols) > 0:
            cols = [ele.text.strip() for ele in cols]
            if len([ele for ele in cols if ele]) > 0:
                data_list.append([ele for ele in cols if ele])

    return headers_list, data_list


def xml_chapter_text_extractor(heading_tag, debug_flag=False):
    """
    :param heading_tag:
    :param debug_flag:
    :return:
        chapter plain text (except tables)
        chapter_list -> text in list
        table_list   -> for each table in chapter: [[headers], [[content_row_0]...[content_row_n]]]
    """
    # TODO some text are not extracted:
    #     Cambodia National Silk Strategy (49) -> Plan of action
    #     Nepal paper NES -> Global trends

    # Search until another tag with same name of heading_tag is found and extract all text in-between

    # List with tags names to get_text
    tag_names_list = ['L', 'Sect', 'Figure']

    chapter_list = [heading_tag.string]
    table_list = []

    for next_tag in heading_tag.next_siblings:
        if next_tag.name == heading_tag.name and next_tag.string != heading_tag.string:
            break

        elif next_tag.string and next_tag.string != '\n' or next_tag.name in tag_names_list:
            chapter_list.append(re.sub('\\n+', '\\n', next_tag.get_text()))

        # Extract tables content in 'table_list' and insert anotation in 'chapter_list'
        elif isinstance(next_tag, Tag) and (next_tag.find_all('Table') or next_tag.name == 'Table'):
            if next_tag.find_all('Table'):
                tables = next_tag.find_all('Table')
            else:
                tables = [next_tag]
            for table_xml in tables:
                headers_list, data_list = xml_table_parser(table_xml)
                chapter_list.append("------> Table number: {} <------".format(len(table_list)))
                table_list.append([headers_list, data_list])

    if debug_flag:
        print('\n'.join(chapter_list))

    return '\n'.join(chapter_list), chapter_list, table_list


class Breaker(Exception):
    # Exception class defined to handle it as a breaker for loops into loops
    pass


def xml_document_extractor(soup_obj):
    """
    Extract all chapters until find a title in list 'heading_not2extract_list'
    :param soup_obj:
    :return:
    """

    document_list = []
    extraction_list = []
    # List with last headings not to extract
    heading_not2extract_list = ['appendix', 'reference']

    # Search headings from 'executive summary' title
    _, heading_tags = xml_headings_list_extractor('executive summary', soup_obj)

    for heading_tag in heading_tags:
        try:
            for heading_not2extract in heading_not2extract_list:
                if heading_not2extract in heading_tag.string.lower():
                    raise Breaker
            extraction_list.append(heading_tag)
        except Breaker:
            break

    for heading_tag in extraction_list:
        _, chapter_list, _ = xml_chapter_text_extractor(heading_tag)
        document_list += chapter_list

    return '\n'.join(document_list)


def countries_getter():
    """
    Get set of countries/gentiles from wikipedia.
    If not possible print out message and load backup set from input file
    """

    try:
        # html wiki with countries/gentiles table scrapping
        wiki_countries = 'https://en.wikipedia.org/wiki/List_of_adjectival_and_demonymic_forms_for_countries_and_nations'
        page = requests.get(wiki_countries)
        soup = BeautifulSoup(page.content, features='lxml')

        # read table as DataFrame
        country_df = pd.read_html(str(soup.find_all(class_='wikitable sortable')[0]))[0]

        # Build list from all columns data
        country_list = []
        for col_name in country_df.columns:
            country_list += list(country_df[col_name])

        # List of not countries words in order to delete from text sensitive words
        words_not_country = ['plurinational', 'state', 'islands', 'island', 'american', 'antigua', 'ocean',
                             'territory', 'central', 'african', 'republic', 'democratic', "people's", 'east',
                             'european', 'union', 'southern', 'territories', 'man', 'ivory', 'coast', 'heard',
                             'islamic',
                             'british', 'french', 'federated', 'states', 'north', 'northern', 'new', 'south', 'africa',
                             'city', 'united', 'kingdom', 'america', 'western', 'great', 'residents', 'islanders',
                             'singular', 'cocos', 'europeans', 'islander', 'channel', 'people',
                             'americans',
                             'citizen', 'citizens', 'africans', 'poles', 'resident', 'virgin'
                             ]
        stopwords = nltk.corpus.stopwords.words('english')

        # Converts '/' to ' ' in order to get both alternatives words when appeared
        country_sep = [re.sub(r'\/', ' ', x) for x in country_list]

        # Lowercase and word cleaning (stopwords and '[]() characters')
        countries_clean = [x.lower() for y in country_sep for x in re.sub(r',|\[\w\]|\(|\)', '', y).split(' ')
                           if x.lower() not in stopwords]
        # Build set preventing word duplication
        countries_set = {x for x in countries_clean if x not in words_not_country}

        return countries_set

    except:
        backup_path = 'input/countries_words_2021-01-19.bak'
        print('Countries_getter() error loading countries list from internet: loading list from backup file:'
              '\n\t{}'.format(backup_path))

        with open(backup_path, 'rb') as file_open:
            countries_set = pickle.load(file_open)

        return countries_set


def text_cleaning(text):
    """
    Word cleaning (word stripping + len>=3), lematizing and filtering english words
    not stopwords
    """
    text = text.lower()

    # Get english words (WordNet) and stopwords to filter with
    words_wordnet = {x.lower() for x in set(nltk.corpus.words.words())}
    stopwords = nltk.corpus.stopwords.words('english')

    words_itc_take = {'academia', 'afcta', ' agoa', 'aleb', 'asycuda', 'bedco', 'cbl', 'cfc', 'cma',
                      'comesa', 'coordination', 'csa', 'dtis', 'efta', 'eif', 'fao', 'fdi', 'fta', 'gap', 'gdp', 'gni',
                      'gsp', 'gvc',
                      'ict', 'itc', 'imf', 'ldc', 'lpi', 'mnc', 'msme', 'msmes', 'nes', 'ngo', 'nsdp',
                      'oda', 'oecd',
                      'poa', 'prsp', 'ses', 'sez', 'sme', 'smes', 'sop', 'sps', 'stdr', 'sitc',
                      'tbt', 'tisi', 'tsn', 'tvet', 'unctad', 'undaf', 'undp', 'unwto',
                      'wdi', 'wef', 'wipo', 'wto', 'wttc'
                      }

    # Build word sets to take into account making union between two set words
    words_take_set = words_wordnet | words_itc_take

    # Get countries words fo filter with
    countries_words = countries_getter()

    words_itc_remove = {'abu', 'asa', 'ca', 'cape', 'dhabi', 'goi', 'paulo', 'reg', 'sao', 'shall', 'tom', 'wim', 'wu'}

    # Build word sets to remove
    words_remove_set = countries_words | words_itc_remove

    # Define lemmatizer
    wordnet_lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

    text_strip = ' '.join([x.strip('".,;:-():!?-‘’ ') for x in text.split(' ')])
    # Filter words without numbers and 3 or more letters long -> list of words
    words_list_filt_long = re.findall(r'(\b[a-zA-Z]{3,}\b|\bun\b|\bit\b|\beu\b)', text_strip)
    # Lemmitize words list except ITC acronyms
    words_list_lem = [wordnet_lemmatizer.lemmatize(x) if x not in words_itc_take else x for x in words_list_filt_long]
    # Filter not stopwords
    words_list_filt_stop = [word for word in words_list_lem if word not in stopwords]
    # Filter not countries words+custom dictionary
    words_list_filt_count = [word for word in words_list_filt_stop if word not in words_remove_set]
    # Filter words in WordNet+custom dictionary
    words_list_clean = [word for word in words_list_filt_count if word in words_take_set]

    return words_list_clean


def decoder(code_4digit):
    """
    Transform a 4-digit string code or a number into a filename (document_global)
    Use dict from pickle file
    Errors from dict search are controlled and displayed

    :param code_4digit: string (4-letter) or number
    :return: old filename string (None if any error occurs)
    """

    with open('../data/recoder_dict_tradefocus.bak', 'rb') as file_open:
        deco_dict = pickle.load(file_open)

    old_filename = 'None'

    try:

        if type(code_4digit) == type('string'):
            old_filename = deco_dict[code_4digit]
            print(old_filename)
        elif type(code_4digit) == type(4):
            old_filename = deco_dict['{:04d}'.format(code_4digit)]
            print(old_filename)
        else:
            print('Input type not recognized, please enter a 4-digit number or a 4-word string')

    except Exception as e:
        print('Error decoding!!! \n\t{}:{}'.format(type(e).__name__, str(e)))

    return old_filename


def coder(input_str, field='document_global'):
    """
    Look for input_str in field from TradeFocus table and display
    name, document_global and code_name fields in DataFrame format

    :param input_str: string to search (partial or complete match)
    :param field: column to look for from TradeFocus table
    :return: outcome dataframe
    """
    docs_TF_pd = pd.read_excel('../data/recordsTradeFocus_4-digits.xlsx')

    with pd.option_context('display.max_colwidth', -1):
        return(
            docs_TF_pd[docs_TF_pd[field].str.contains(input_str)]
                                [['name', 'document_global', 'code_name']])
