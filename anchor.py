import json
import os
from pathlib import Path
import shelve
from simhash import Simhash
from alternate_parser import Parser
import hashlib
from math import log
import pickle

# add anchor text to document its pointing to

'''
Done:

STRUCTURE:
Url Hash Table: //shelf for now
UrlHash -> (Url, incoming urls count)

INVERTED INDEX: //bin for now
Term -> (HashedUrl, Frequency)

ToDo:
AnchorText Index:

Positioning index:

'''


class Indexer:
    doc_id = 0
    dump_id = 0
    total_count = 0

    def __init__(self, target_directory):
        self.url_count = 0
        self.index = {}
        self.stored_simhash = False

        self.weights = [5, 4, 3, 2, 1]
        # title, h1, h2, h3, strong

        # when you run your first fresh index
        if not os.path.exists('stored_urls_path.json'):
            self.simhash = {}  # ik not efficent for now but just stores unique simhashes
        else:
            self.stored_simhash = True
            json_stored_path = open('stored_urls_path.json', 'r')
            self.simhash = json.load(json_stored_path)  # loaded simhash

        self.url_id = shelve.open('url_id.shelve', writeback=True)
        self.fill_index_with_content(target_directory)

        if self.stored_simhash:
            json_stored_path.close()
        else:
            with open('stored_urls_path.json', 'w') as js:
                json.dump(self.simhash, js)

        print("saving url id")
        self.url_id.close()

    def dump_current_index(self):
        print(f'dumping {Indexer.dump_id}')
        os.makedirs("dump", exist_ok=True)
        json_dump = f'dump/index{Indexer.dump_id}.jsonl'
        self.index = dict(sorted(self.index.items()))
        with open(json_dump, 'w') as dump:
            for key, value in self.index.items():
                json.dump({key: value}, dump)
                dump.write('\n')
        self.url_count = 0
        self.index = dict()
        Indexer.dump_id += 1

    def fill_index_with_content(self, target_directory):
        base = Path(target_directory)
        for subdir in base.iterdir():  # each worker will work only with one and dump
            if subdir.is_dir():
                for file in subdir.iterdir():
                    self.url_count += 1
                    Indexer.total_count += 1
                    content = Parser().parse_content(file)
                    if content:
                        url, tokens, anchor_dict, fields = content
                        #print(f'parsing {Indexer.total_count}: {file} {url}')
                        if not self.similar_exist(tokens):
                            # this is used for calculating tf
                            doc_size = len(tokens)
                            url_hash = hashlib.sha256(url.encode()).hexdigest()
                            self.add_posting_token(
                                tokens, url_hash, doc_size, fields)
                        if self.url_count > 10000:
                            self.dump_current_index()  # dumps the current index
        self.dump_current_index()
    def add_posting_token(self, tokens, url_hash, doc_size, fields):
        '''just adds the token count and the hashed url <hashedurl, tf or occurences / total # terms >'''
        count = dict()
        bigram_count = dict()  # To track bigram frequency
        weighted = dict()

        anchor_set = self.url_id[url_hash][1]
        page_rank = self.url_id[url_hash][3]

        for index, tokens_in_field in enumerate(fields):
            weight = self.weights[index]
            #    print(f'field {index}')
            for token in tokens_in_field:
                weighted[token] = weight

        for token in tokens:
            if token not in count:
                count[token] = 1
            else:
                count[token] += 1

        scorings = self.calculate_some_relevance(weighted, doc_size, count)

        for key in count:
            in_anchor = 0.4 if key in anchor_set else 0

            if key not in self.index:
                #    print(f'SCORINGS {key}: {scorings[key]}')
                self.index[key] = [(url_hash, scorings[key]*0.3+in_anchor+0.3*page_rank)]
            else:
                self.index[key].append((url_hash, scorings[key]*0.3+in_anchor+0.3*page_rank))

        # counts term frequencies for each word in the bigram
        for i in range(len(tokens) - 1):
            bigram = tokens[i] + " " + tokens[i + 1]
            if bigram not in bigram_count:
                bigram_count[bigram] = 1
            else:
                bigram_count[bigram] += 1

        # print(f'SCORINGS {scorings}')
        for key, value in bigram_count.items():
            split_key = key.split(' ')
            in_anchor = 0.4 if (split_key[0] in anchor_set) and (split_key[1] in anchor_set) else 0
            if key not in self.index:
                self.index[key] = [
                    (url_hash, (bigram_count[key] * (scorings[split_key[0]] + scorings[split_key[1]]) / 2)*0.3 + in_anchor + 0.3*page_rank)]
            else:
                self.index[key].append(
                    (url_hash, (bigram_count[key] * (scorings[split_key[0]] + scorings[split_key[1]]) / 2)*0.3 + in_anchor + 0.3*page_rank))

    def calculate_some_relevance(self, weighted_content, doc_size, tf_content):
        FIELD_WAIT_RATIO = 0.6
        TF_RATIO = 0.4
        final_token_weight = {}
        for k, tf in tf_content.items():
            weight = weighted_content.get(k, 0)
            if weight == 0:
                weighted_tf = (1 + log(tf)) * TF_RATIO if tf > 0 else 0  # changed to multiply by TF_Ratio
            else:
                weighted_tf = FIELD_WAIT_RATIO * (1 + log(weight)) * TF_RATIO * \
                              (1 + log(tf)) if tf > 0 else 0
            final_token_weight[k] = weighted_tf
        return final_token_weight

    def similar_exist(self, tokens):  # have to change url_id later
        '''checks the simhash values and returns if a similar exits value exists or not'''

        try:
            simhash = self._get_simhash(tokens)
            sim_val = simhash.value

            # this is the part where we just check if this was one of the valid simhashes we encountered before
            if self.stored_simhash:
                if str(sim_val) in self.simhash:
                    return False
                else:
                    return True

            if not self.simhash:
                self.simhash[str(sim_val)] = 0
                return False
            else:
                for simhash_val in self.simhash:
                    value = Simhash(int(simhash_val))
                    if simhash.distance(value) <= 2:
                        print("Similar detected for the above url")
                        return True

            self.simhash[str(sim_val)] = 0
            return False
        except:
            print("overflow error")
            return False

    def _get_simhash(self, tokens):
        shortened_tokens = [token[:30] if len(
            token) > 30 else token for token in tokens]
        return Simhash(" ".join(shortened_tokens[:150]))

    def _save_url_id(self):
        with shelve.open('url_id.shelve') as f:
            for key, value in self.url_id.items():
                print(f'{key}: {value}')
                if value[0]:
                    f[key] = value


if __name__ == "__main__":
    a = Indexer("/Users/sathvikkaruturi/Downloads/DEV")
