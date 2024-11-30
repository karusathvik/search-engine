# in progress
import json
import hashlib
import os
import pickle
import heapq
import shelve

from math import log

'''
TODO: change indexer to store sizes to use the seek operation 
    this is the only way to ever create a merge 
'''
total_links = 0
url_id = 'url_id.shelve'

with shelve.open(url_id) as urls:
    for key in urls.keys():
        total_links += 1

#idf = log (total_links / len[term] which is # of docs containing that term)

files = []
heap = []  # will use heapq to push and pop entries in
json_iterators = []


for i in range(6):
    print(i)
    file = open(f'dump/index{i}.jsonl', 'r')
    files.append(file)
    iterator = (json.loads(line)
                for line in file)  # will read json line by line
    json_iterators.append(iterator)

    try:
        first_entry = next(iterator)
        key, value = next(iter(first_entry.items()))
        # automatically put the smallest key on the root
        heapq.heappush(heap, (key, value, i))
    except StopIteration:
        pass

bin_order = '0123456789abcdefghijklmnopqrstuvwxyz'
current_bin = 0
current_index = dict()
os.makedirs("bins", exist_ok=True)
count = 0  # debugging purpose

offsets = shelve.open("offsets.shelve")

while heap:
    smallest_key, postings, file_no = heapq.heappop(heap)
    print(f'{count}: {smallest_key}')

    # used while in case none of the tokens start with the next alphabet
    while not smallest_key.startswith(bin_order[current_bin]):
        print("next bin")
        with open(f'bins/bin_{bin_order[current_bin]}.jsonl', 'w') as final_index:

            #this is the idf part . tf was calculated in alternate_indexer
            for key, value in current_index.items():
                size = len(value) + 1  # size of the posting list
                for posting in value:
                     posting[1] *= log(total_links/size)
                value = sorted(value, key=lambda x: x[1], reverse=True)

                start_offset = final_index.tell()
                json.dump({key: value}, final_index)
                final_index.write("\n")
                end_offset = final_index.tell()
                offsets[key] = (start_offset, end_offset)



        current_bin += 1
        current_index = dict()

    if smallest_key in current_index:
        current_index[smallest_key].extend(postings)
    else:
        current_index[smallest_key] = postings

    try:
        next_entry = next(json_iterators[file_no])
        key, value = next(iter(next_entry.items()))
        heapq.heappush(heap, (key, value, file_no))
    except StopIteration:
        pass
    count += 1
offsets.close()



#have to the tf-idf for the z bin so figure why this is binary later
with open(f'bins/bin_{bin_order[current_bin]}.bin', 'wb') as final_index:
    pickle.dump(current_index, final_index)
