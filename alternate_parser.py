from nltk.stem import PorterStemmer  # for stemming
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import hashlib
import re
import nltk
import json
from bs4 import BeautifulSoup
import lxml
import sys
import time
sys.setrecursionlimit(
    10000)  # have to set this higher since Beautiful Soup uses recursion to parse the HTML and if its too nested it can exceed the default


class Parser:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.lemmanize = WordNetLemmatizer()
        # nltk.download('stopwords')
        # nltk.download('wordnet')
        # self.stop_words = set(stopwords.words('english')) # should keep stopwords in index, we can filter stopwords out of the query if needed

    def parse_content(self, path):
        if not str(path).endswith(".json"):
            return None
        with open(path, 'r') as f:
            file_content = f.read()
            data = self.get_json(file_content)
            url = data["url"]
            content = data["content"]

            if "encoding" in data and data["encoding"] not in ['ascii', 'utf-8']:
                return None

            if content.strip().startswith('<?xml'):
                html_content = BeautifulSoup(content, "lxml-xml")  # parse XML
            else:
                html_content = BeautifulSoup(content, "lxml")  # parse HTML

            tokens = self.tokenize_stem_strip(
                html_content.get_text(separator=" ", strip=True))  # changed to get the text
            anchor_dict = self.get_links(html_content)

            # ex <title>, <h1> ...
            field_tokens = self.get_field_content(html_content)
            return (url, tokens, anchor_dict, field_tokens)

    def get_json(self, data):
        try:
            # some files are not properly formatted JSONs
            return json.loads(data)
        except json.JSONDecodeError as e:
            print(f'Failed to load json')
            return {"url": "", "content": ""}

    def get_links(self, soup_content):
        # added this so items like calendars and login pages do not have artificially high
        # returns dict in format of {hash1: {anchor_text_tokens1}, hash2: {anchor_text_tokens2},...}
        link_anchor_dict = {}
        for link in soup_content.find_all('a'):
            rel = link.get('rel')
            href = link.get('href')
            if href and (not rel or "nofollow" not in rel):
                href_hash = hashlib.sha256(href.encode()).hexdigest()
                anchor_tokens = set(
                    self.tokenize_stem_strip(link.text.strip()))
                if href in link_anchor_dict:
                    link_anchor_dict[href_hash] = link_anchor_dict[href_hash].update(
                        anchor_tokens)
                else:
                    link_anchor_dict[href_hash] = anchor_tokens
        return link_anchor_dict

    def get_field_content(self, soup_content):
        '''returns a 2d list [{....}, {...}] each indicating a title'''
        tags = ['title', 'h1', 'h2', 'h3', 'strong']

        page_text = [
            set(self.tokenize_stem_strip(element.get_text(strip=True))) if (
                element := soup_content.find(tag)) else set()
            for tag in tags]
        # print(page_text)
        return page_text

    def tokenize_stem_strip(self, text):
        ''' This will handle parsing the text by first by removing contractions, normalizing, removing stopwords, and then tokenizing '''

        tokens = []
        # print(f'TEXT {text}')

        start_time = time.time()
        tokenize_text = word_tokenize(text)

        for token in tokenize_text:
            token = (re.sub(r"\b\w+'\w+\b", '', token)
                     ).lower()  # removes contractions
            # if token not in self.stop_words: #normalizes
            is_alpha = bool(re.fullmatch(r'[a-zA-Z0-9]+', token))
            invalid_num = bool(token.isdigit() and len(token) > 9)
            invalid_str = bool(len(set(token)) == 1 and len(token) > 3)

            if token and is_alpha and not invalid_num and not invalid_str:
                #tokens.append(self.stemmer.stem(self.lemmanize.lemmatize(token.strip()))) #removed lemmanize cuz of speed issue
                tokens.append(self.stemmer.stem(token.strip()))

        return tokens
