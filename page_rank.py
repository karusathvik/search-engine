import shelve

def calculate_pagerank():
    print("calculating pagerank")
    
    outlinks_dict = dict()
    d = 0.85

    with shelve.open('url_id.shelve') as url_id:
        for key, value in url_id.items():
            outlinks_dict[key] = value[2]
        print("got outlinks")

    pages = list(outlinks_dict.keys())
    N = len(pages)
    ranks = {page: 1 for page in pages}  #initial pagerank starts from 1


    for page in pages:
        if not outlinks_dict[page]:
            outlinks_dict[page] = pages  #since dangling node jumps to a random page as stated in the lecture

    for iteration in range(100): #iterate at most 100 times
        print(iteration)
        new_ranks = dict()
        count = 0
        total = len(pages)
        for page in pages:
            print(f'{count} out of {total}')
            rank_sum = 0
            for other_page, other_outlinks in outlinks_dict.items():
                if page in other_outlinks:
                    rank_sum += ranks[other_page] / len(other_outlinks)
            count += 1

            new_ranks[page] = (1 - d) / N + d * rank_sum

        # if change in all the pageranks are small enough, stop iteration
        if max(abs(new_ranks[page] - ranks[page]) for page in pages) < 1e-6:
            print("converged")
            break

        ranks = new_ranks

    with shelve.open('url_id.shelve') as url_id:
        for key, value in ranks.items():
            url_id[key][3] = value


if __name__ == "__main__":
    calculate_pagerank()