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
    current_dir = os.getcwd()
    temp_posting_path = os.path.join(current_dir, "temp_posting")
    temp_dict_path = os.path.join(current_dir, "temp_dict")

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
                    write_block_to_disk(postings_lists, doc_freq, temp_dict_path, temp_posting_path)
                    with open(temp_dict_path, 'a') as dict_file: # Open the dictionary file in append mode for writing
                        # Store the pointer to the starting term of the next block of dictionary
                        block_pointers.append(dict_file.tell())
                    # print(block_pointers)
                    postings_lists = {}
                    doc_freq = {}
    
    # Write the last block to disk
    write_block_to_disk(postings_lists, doc_freq, temp_dict_path, temp_posting_path)
    n_way_merge(block_pointers, temp_dict_path, temp_posting_path, out_dict, out_postings) 

def write_block_to_disk(postings_lists, doc_freq, dictionary_file, postings_file):
    # Sort all keys before writing to disk
    sorted_terms = sorted(postings_lists.keys())
    with open(dictionary_file, 'a') as dict_file, open(postings_file, 'a') as postings_file:
        # Keep track of the current position in the postings file for pointer info
        current_position = postings_file.tell()
        
        for term in sorted_terms:
            postings_list = postings_lists[term]
            doc_frequency = doc_freq[term]

            # Store the term, its document frequency, and the pointer to posting list file in dictionary file
            dict_file.write(f"{term} {doc_frequency} {current_position} {dict_file.tell()}\n")

            postings_list_data = []
            while postings_list:
                postings_list_data.append(postings_list.doc_id)
                postings_list = postings_list.next
           
            # Convert the list to a string and write to file
            postings_file.write(' '.join(postings_list_data) + '\n')

            # Update the current position in the postings file
            current_position = postings_file.tell()

        dict_file.write(f"-----BLOCK_END-----\n")
        postings_file.write(f"-----BLOCK_END-----\n")

def n_way_merge(block_pointers, read_dictionary_file, read_postings_file, write_dictionary_file, write_postings_file):
    # Merge and transfer content from temporary to final files
    block_handles = [open(read_dictionary_file, 'r') for _ in range(len(block_pointers))]
    posting_handles = [open(read_postings_file, 'r') for _ in range(len(block_pointers))]
    final_dictionary = open(write_dictionary_file, 'a')
    final_posting = open(write_postings_file, 'a')

    while True:
        current_terms = []  # stores the term, index tuple
        posting_pointers = []  # stores the posting list pointer of a term
        doc_freq = [] # stores the document frequency of term
        term_lengths = [] # stores the term length used for skipping
        index = 0

        # Read initial term information from each block and store its posting pointers
        print("Current terms under consideration")
        for i, pointer in enumerate(block_pointers[:]):
            block_handles[i].seek(pointer)
            term_len = block_handles[i].readline()
            term_info = term_len.strip().split(' ')
            term = term_info[0].strip()
            print(term)
            if term == '-----BLOCK_END-----':
                block_pointers.remove(pointer)
                continue
            term_lengths.append(term_len)
            doc_freq.append(int(term_info[1]))
            posting_pointers.append(int(term_info[2]))
            current_terms.append((term, index))
            index += 1
        
        # All blocks have reached the end
        print("This is the list of current block pointers")
        print(block_pointers)
        if not block_pointers:
            break

        print("This is cuurent list of terms after processing")
        print(current_terms)
        
        # Find all terms to be merged
        sorted_terms = sorted(current_terms, key=lambda x: x[0])
        # print("sorted_terms")
        # print(sorted_terms)
        # print(sorted_terms[0])
        # print(sorted_terms[0][0])
        smallest_term = sorted_terms[0][0]

        # Find their corresponding posting list and doc_freq of the terms
        terms_to_merge = []
        posting_to_merge = [] 
        doc_freq_to_merge = []
        for term in sorted_terms:   
            if term[0] == smallest_term:
                # print("Checking sorting term")
                # print(term)
                # print(term[1])
                # print(posting_pointers[term[1]])
                terms_to_merge.append(term)
                posting_to_merge.append(posting_pointers[term[1]])
                doc_freq_to_merge.append([doc_freq[term[1]]])
            else:
                break
        # print(posting_to_merge)
        # print(doc_freq_to_merge)
        print("These are the current terms for merging")
        print(terms_to_merge)

        print("Block pointer after update")
        # Advancing pointers
        for term in terms_to_merge:
            index = term[1]
            block_pointers[index] += len(term_lengths[index])
            print(block_pointers[index])

        # Merging step
        # Merge posting
        merged_postings = []
        # List of all posting lists to be merged
        posting_list = []
        for i, ptr in enumerate(posting_to_merge):
            posting_handles[i].seek(ptr)
            posting_string = posting_handles[i].readline().strip()
            posting = [int(x) for x in posting_string.split()]
            posting_list.append(posting)
        for posting in posting_list:
            for i in posting:
                merged_postings.append(i)
        # print(merged_postings) 
                
        # Merge doc_freq
        final_doc_freq = sum(sum(sublist) for sublist in doc_freq_to_merge)
        # print(final_doc_freq)
        # print("Here are the list of freq to merge")
        # print(doc_freq_to_merge)
        # print(final_doc_freq)
        # Write merged dictionary and posting lists to final files
        final_pointer = final_posting.tell()
        final_posting.write(' '.join(str(posting_id) for posting_id in merged_postings) + '\n')
        final_dictionary.write(f"{smallest_term}: {final_doc_freq}, {final_pointer}\n")



    for handle in block_handles + posting_handles:
        handle.close()

    # Print the merged postings list
    # print("Merging completes!\n")
        
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
