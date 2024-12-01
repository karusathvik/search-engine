from alternate_parser import Parser
import hashlib
import os
import pickle
import shelve
import copy
import time
import json
import heapq
from math import log

#TODO: fix bigram/normal word looks up for those that do not exist

class Query:
    def __init__(self):
        self.parser = Parser()
        self.offsets = shelve.open("offsets.shelve")
        self.url_id = shelve.open("url_id.shelve")

        self.bin_dicts = {}
        self.load_bins()

    def load_bins(self):
        bin_folder = "bins"
        for filename in os.listdir("bins"):
            filepath = os.path.join(bin_folder, filename)
            if filename.endswith(".jsonl"):  # Only process JSONL files
                self.bin_dicts[filename[4:5]] = open(filepath, 'r')

    def print_first_10_pages(self, common_docs):
        # for the UI test
        start_time = time.time()
        for i, doc in enumerate(common_docs):
            if i < 10:  # Limit to first 10 items
                print(f'{self.url_id[doc[0]][0]}')

            else:
                break
        end_time = time.time()
        # print(f'time to print {end_time - start_time}')
        # return link

    def get_user_input(self, query):
        # try:
        start_time = time.time()

        parse_time = time.time()
        parsed_query = self.parser.tokenize_stem_strip(query)
        end_p_time = time.time()
        # print(f'time to parse {end_p_time - parse_time}')

        # print(f'parsed query {parsed_query}')
        if len(parsed_query) <= 2:  # just need to look through one word
            if len(parsed_query) == 2:
                print(' '.join(parsed_query))
                lookup = self.lookup_word(' '.join(parsed_query))
            else:
                lookup = self.lookup_word(parsed_query[0])

            sort_time = time.time()

            end_time = time.time()
            # print(f'time to sort {end_time - sort_time}')
            self.print_first_10_pages(lookup)

            end_time = time.time()
            elapsed_time = end_time - start_time  # Calculate elapsed time
            print(
                f"Time taken to execute: {elapsed_time:.6f} seconds")
        else:
            all_bigrams = self.generate_bigrams(parsed_query)
            common_docs = {}
            common_doc_set = None
            run = 0

            for bigram in all_bigrams:
                content = self.lookup_word(' '.join(bigram))
                if run == 0:
                    for posting in content:
                        common_docs[posting[0]] = posting[1]
                    run += 1
                else:
                    temp = dict()
                    for posting in content:
                        if posting[0] in common_docs:
                            temp[posting[0]] = common_docs[posting[0]] + posting[1]
                    common_docs = temp

            top_10 = heapq.nlargest(
                10, common_docs.items(), key=lambda x: x[1])


            self.print_first_10_pages(top_10)
            end_time = time.time()  # End the timer
            elapsed_time = end_time - start_time  # Calculate elapsed time
            print(
                f"Time taken to execute 2: {elapsed_time:.6f} seconds")
        # except KeyError as e:
        #     print(f'No results')

    def generate_bigrams(self, parsed_query):
        return tuple(zip(parsed_query, parsed_query[1:]))

    # def lookup_shorter_queries(self, words):
    #     start_time = time.time()
    #     key = words[0]

    #     start_offsets = self.offsets[words][0]
    #     end_offsets = self.offsets[words][1]

    #     bin_to_open = self.bin_dicts[key]
    #     bin_to_open.seek(start_offsets)

    #     raw_content = bin_to_open.read(end_offsets - start_offsets)
    #     content = json.loads(raw_content)

    #     end_lookup = time.time()
    #     print(f'time to lookup : {end_lookup - start_time}')

    #     return content[words]

    def lookup_word(self, word):
        key = word[0]
        #print(f'word {word}')
        print(word)
        start_offsets = self.offsets[word][0]
        end_offsets = self.offsets[word][1]

        bin_to_open = self.bin_dicts[key]
        bin_to_open.seek(start_offsets)

        raw_content = bin_to_open.read(end_offsets - start_offsets)

        content = json.loads(raw_content)

        return content[word]

    def close_bins(self):
        for key, file in self.bin_dicts.items():
            file.close()


if __name__ == "__main__":
    a = Query()
    # profiler = cProfile.Profile()
    # profiler.enable()
    a.get_user_input(input("Search: "))
    # profiler.disable()
    # profiler.print_stats(sort="time")
    a.close_bins()
