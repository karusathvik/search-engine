import shelve
import time

def calculate_pagerank():
    print("Calculating PageRank...")

    outlinks_dict = dict()
    d = 0.85

    # Build outlinks_dict with only valid outlinks
    with shelve.open('url_id.shelve') as url_id:
        url_hash = set(url_id.keys())
        for key, value in url_id.items():
            outlinks_dict[key] = [outlink for outlink in value[2] if outlink in url_hash]
        print("Got outlinks.")

    pages = list(outlinks_dict.keys())
    N = len(pages)
    ranks = {page: 1 for page in pages}  # Initial PageRank starts from 1

    # Precompute incoming links
    incoming_links = {page: [] for page in pages}
    for page, outlinks in outlinks_dict.items():
        for outlink in outlinks:
            incoming_links[outlink].append(page)
    print("Precomputed incoming links.")

    # Iterate for PageRank calculation
    for iteration in range(500):  # Iterate at most 100 times
        new_ranks = dict()
        dangling_rank_sum = sum(ranks[page] for page in pages if not outlinks_dict[page])
        #accounts for pageranks added by dangling nodes
        count = 0
        total = len(pages)

        for page in pages:
            rank_sum = sum(ranks[other_page] / len(outlinks_dict[other_page]) for other_page in incoming_links[page])
            new_ranks[page] = (1 - d) / N + d * (rank_sum + dangling_rank_sum / N)

            count += 1

        # if change in all the pageranks are small enough, stop iteration
        if max(abs(new_ranks[page] - ranks[page]) for page in pages) < 1e-6:
            print("Converged")
            break

        ranks = new_ranks

    #these are precomputed
    min = 1.1728017378631037e-05
    big = 0.008724411736476662
    diff = big - min

    with shelve.open('url_id.shelve') as url_id:
        for key, value in ranks.items():
            data = url_id[key]
            data[3] = (value-min)/diff
            '''
            #this is for anchor set, so we remove the bad anchor set values
            if data[1] and any(word in data[1] for word in ['read', 'next', 'previou', 'post', 'home']):
                data[1] = set()
            '''
            url_id[key] = data

if __name__ == "__main__":
    calculate_pagerank()
