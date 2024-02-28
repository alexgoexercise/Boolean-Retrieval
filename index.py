import os
import math
import pickle
import nltk
from nltk.corpus import reuters
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import sys
import getopt

# Define a Node class to represent each element in the linked list
class Node:
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
    # Define block size and memory limit
    block_size = 1000  # Adjust based on memory constraints
    memory_limit = 10000  # Adjust based on available memory

    # Initialize an empty dictionary to hold the index
    index = {}
    # Initialize an empty dictionary to hold document frequencies
    doc_freq = {}
    # Initialize an empty dictionary to hold postings lists
    postings_lists = {}

    # Initialize NLTK's Porter stemmer
    stemmer = PorterStemmer()
    
    # Process each document in the specified directory
    print(os.listdir(in_dir))
    for doc_id, filename in enumerate(os.listdir(in_dir)):
        with open(os.path.join(in_dir, filename), 'r') as f:
            # Tokenize the document into words
            words = word_tokenize(f.read())
            # Apply stemming to each word
            stemmed_words = [stemmer.stem(word.lower()) for word in words]
            
            # Update document frequency counts
            unique_words = set(stemmed_words)
            for word in unique_words:
                if word in doc_freq:
                    doc_freq[word] += 1
                else:
                    doc_freq[word] = 1

            # Process each word in the document
            for word in stemmed_words:
                if word not in postings_lists:
                    postings_lists[word] = Node(doc_id)
                else:
                    current_node = postings_lists[word]
                    while current_node.next:
                        current_node = current_node.next
                    current_node.next = Node(doc_id)

                # Sort document IDs within the posting list
                postings_lists[word] = sort_postings_list(postings_lists[word])

                # Check memory limit
                if sys.getsizeof(postings_lists) > memory_limit:
                    write_block_to_disk(postings_lists, len(index), out_dict, out_postings)
                    postings_lists = {}

    # Write the last block to disk
    write_block_to_disk(postings_lists, len(index), out_dict, out_postings)

def sort_postings_list(head):
    # Convert linked list to list for sorting
    postings_list = []
    current_node = head
    while current_node:
        postings_list.append(current_node.doc_id)
        current_node = current_node.next

    # Sort the list
    postings_list.sort()

    # Reconstruct linked list
    sorted_head = None
    for doc_id in postings_list:
        if sorted_head is None:
            sorted_head = Node(doc_id)
            current_node = sorted_head
        else:
            current_node.next = Node(doc_id)
            current_node = current_node.next

    return sorted_head

def write_block_to_disk(postings_lists, block_number, dictionary_file, postings_file):
    sorted_terms = sorted(postings_lists.keys())
    with open(dictionary_file, 'a') as dict_file, open(postings_file, 'a') as postings_file:
        for term in sorted_terms:
            postings_list = postings_lists[term]
            # Write term and its pointer to dictionary file
            dict_file.write(f"{term}: {block_number}\n")
            # Write postings list to postings file
            while postings_list:
                postings_file.write(f"{postings_list.doc_id} ")
                postings_list = postings_list.next
            postings_file.write("\n")

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
