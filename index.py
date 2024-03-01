import os
import math
import pickle
import nltk
from nltk.corpus import reuters
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import sys
import getopt
import linecache

# Define a Node class to represent each element in the linked list
class Posting:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.next = None
        self.skip = None  # Pointer to the skip node

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

def load_block_from_disk(block_file):
    with open(block_file, 'rb') as f:
        return pickle.load(f)

def write_merged_index_with_skip_pointers_to_disk(merged_index, output_file):
    with open(output_file, 'wb') as f:
        pickle.dump(merged_index, f)

def build_index(in_dir, out_dict, out_postings):   
    memory_limit = 100000  # Adjust based on available memory

    # doc_freq dictionary, to be kept in memory
    doc_freq = {}
    # postings_list dictionary, to be stored in harddisk after memory limit exceeding
    postings_lists = {}
    # List to store pointers to starting terms in each block for merging
    block_pointers = [0] # initialized to 0 for start of first block

    # Initialize NLTK's Porter stemmer
    stemmer = PorterStemmer()
    
    # Open the files in increasing numerical order of the filenames
    sorted_filenames = sorted(os.listdir(in_dir), key=int)

    for filename in sorted_filenames:
        with open(os.path.join(in_dir, filename), 'r') as f:
            
            # Tokenize content in file into a list of tokensp
            words = word_tokenize(f.read())
            # Stem each token into a term 
            stemmed_words = [stemmer.stem(word.lower()) for word in words]
            terms = set(stemmed_words)
            
            # Update document frequency of terms
            for term in terms:
                doc_freq[term] = doc_freq.get(term, 0) + 1
            
                if term not in postings_lists:
                    postings_lists[term] = Posting(filename)
                else:
                    current_node = postings_lists[term]
                    while current_node.next:
                        current_node = current_node.next
                    current_node.next = Posting(filename)

                if sys.getsizeof(postings_lists) + sys.getsizeof(doc_freq) > memory_limit:
                    write_block_to_disk(postings_lists, doc_freq, out_dict, out_postings)
                    with open(out_dict, 'a') as dict_file: # Open the dictionary file in append mode for writing
                        # Store the pointer to the starting term of the next block
                        block_pointers.append(dict_file.tell())
                    postings_lists = {}
                    doc_freq = {}

    # Write the last block to disk
    write_block_to_disk(postings_lists, doc_freq, out_dict, out_postings)
    n_way_merge(block_pointers, out_dict, out_postings) 

def write_block_to_disk(postings_lists, doc_freq, dictionary_file, postings_file):
    sorted_terms = sorted(postings_lists.keys())
    with open(dictionary_file, 'a') as dict_file, open(postings_file, 'a') as postings_file:
        # Keep track of the current position in the postings file
        current_position = postings_file.tell()
        
        for term in sorted_terms:
            postings_list = postings_lists[term]
            doc_frequency = doc_freq[term]

            # Store the term, its document frequency, and the pointer to posting list file in dictionary file
            dict_file.write(f"{term}: {doc_frequency}, {current_position}\n")

            postings_list_data = []
            while postings_list:
                postings_list_data.append(postings_list.doc_id)
                postings_list = postings_list.next
           
            # Convert the list to a string and write to file
            postings_file.write(' '.join(postings_list_data) + '\n')

            # Update the current position in the postings file
            current_position = postings_file.tell()

        dict_file.write(f"-----BLOCK_END-----\n")

# def n_way_merge(block_pointers, dictionary_file, postings_file):
#     # This list holds many copies of blocks in dictionary and postings
#     block_handles = [open(dictionary_file,'r') for _ in range(len(block_pointers))]
#     posting_handles = [open(postings_file,'r') for _ in range(len(block_pointers))]

#     current_terms = [] # stores the term, index tuple
#     posting_pointers = [] # stores the posting list pointer of a term

#     for i, pointer in enumerate(block_pointers):
#         block_handles[i].seek(pointer)
#         term_info = block_handles[i].readline().strip().split(':')
#         term = term_info[0].strip()
#         # print(term_info)
#         # print(term_info[1])
#         # print(term_info[1].split(','))
#         # print(term_info[1].split(',')[1])
#         # print(term_info[1].split(',')[1].strip())
#         posting_pointers.append(term_info[1].split(',')[1].strip())
#         current_terms.append((term,i))

#     # Find all terms whose posting lists are to be merged
#     sorted_terms = sorted(current_terms, key=lambda x: x[0])
#     smallest_term = sorted_terms[0][0]
#     terms_to_merge = [sorted_terms[0]]
#     for term in sorted_terms[1:]:
#         if term[0] == smallest_term:
#             terms_to_merge.append(term)
#         else:
#             break

#     # Merging step
#     merged_postings = []

#     # Initialize pointers for each posting list
#     pointers = [0] * len(terms_to_merge)

#     # Convert pointers to integers
#     for i, term in enumerate(terms_to_merge):
#         posting_ptr = int(posting_pointers[term[1]])
#         posting_handles[term[1]].seek(posting_ptr)
#         pointers[i] = posting_ptr

#     # Continue merging until all pointers reach the end of their posting lists
#     while any(pointer != -1 for pointer in pointers):
#         # Find the smallest value among the next values of all posting lists
#         min_value = float('inf')
#         min_index = -1
#         for i, pointer in enumerate(pointers):
#             if pointer != -1:
#                 posting_handles[terms_to_merge[i][1]].seek(pointer)
#                 next_value = int(posting_handles[terms_to_merge[i][1]].readline().strip())
#                 if next_value < min_value:
#                     min_value = next_value
#                     min_index = i
        
#         # Append the smallest value to the merged_postings list
#         merged_postings.append(min_value)
        
#         # Move the pointer of the posting list with the smallest value to the next position
#         pointers[min_index] = posting_handles[terms_to_merge[min_index][1]].tell()
#         next_value = posting_handles[terms_to_merge[min_index][1]].readline().strip()
#         if next_value == "":
#             pointers[min_index] = -1

#         print(merged_postings)
#         print("Merging completes!\n")
#     # At this point, merged_postings will contain the merged and sorted posting list for all terms

def n_way_merge(block_pointers, dictionary_file, postings_file):
    # Open handles for dictionary and postings files
    block_handles = [open(dictionary_file, 'r') for _ in range(len(block_pointers))]
    posting_handles = [open(postings_file, 'r') for _ in range(len(block_pointers))]

    current_terms = []  # stores the term, index tuple
    posting_pointers = []  # stores the posting list pointer of a term

    # Read initial term information from each block and store pointers
    for i, pointer in enumerate(block_pointers):
        block_handles[i].seek(pointer)
        term_info = block_handles[i].readline().strip().split(':')
        term = term_info[0].strip()
        posting_pointers.append(term_info[1].split(',')[1].strip())
        current_terms.append((term, i))

    # Find all terms whose posting lists are to be merged
    sorted_terms = sorted(current_terms, key=lambda x: x[0])
    smallest_term = sorted_terms[0][0]
    terms_to_merge = [sorted_terms[0]]
    for term in sorted_terms[1:]:
        if term[0] == smallest_term:
            terms_to_merge.append(term)
        else:
            break

    # Merging step
    merged_postings = []

    # Initialize pointers for each posting list
    posting_pointers = [0] * len(terms_to_merge)

    # Continue merging until all pointers reach the end of their posting lists
    while any(pointer < len(posting_pointers[i]) for i, pointer in enumerate(posting_pointers)):
        # Find the smallest value among the next values of all posting lists
        min_value = float('inf')
        min_index = -1
        for i, pointer in enumerate(posting_pointers):
            if pointer < len(posting_pointers[i]):
                if posting_handles[terms_to_merge[i][1]].closed:
                    continue
                posting_handles[terms_to_merge[i][1]].seek(pointer)
                next_value = list(map(int, posting_handles[terms_to_merge[i][1]].readline().strip().split()))
                if next_value[pointer] < min_value:
                    min_value = next_value[pointer]
                    min_index = i

        # Append the smallest value to the merged_postings list
        merged_postings.append(min_value)

        # Move the pointer of the posting list with the smallest value to the next position
        if min_index != -1:
            posting_pointers[min_index] += 1

    # Close all file handles
    for handle in block_handles + posting_handles:
        handle.close()

    # Print the merged postings list
    print(merged_postings)
    print("Merging completes!\n")


def main():
    # Set default values
    input_directory = output_file_dictionary = output_file_postings = None

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-i':  # input directory
            input_directory = a
        elif o == '-d':  # dictionary file
            output_file_dictionary = a
        elif o == '-p':  # postings file
            output_file_postings = a
        else:
            assert False, "unhandled option"

    # Check if required arguments are provided
    if input_directory is None or output_file_postings is None or output_file_dictionary is None:
        usage()
        sys.exit(2)

    # Build index
    build_index(input_directory, output_file_dictionary, output_file_postings)
    print("Indexing completed.")

if __name__ == "__main__":
    main()
