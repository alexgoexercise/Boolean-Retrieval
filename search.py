#!/usr/bin/python3
import re
import nltk
import sys
import getopt
from nltk import PorterStemmer
from nltk import word_tokenize

class Node:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.next = None
        self.skip = None  # Pointer to the skip node

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    """
    Below part of the code is the declaration of the functions that will be used in the search process
    """

    # Function to retrieve the posting list of the full set
    def get_full_set_postings(dictionary, postings_file):
        # wait to see how to get the full set

    # Function of looking up for the posting list of a certain term giving the address of the term
    # The posting list is reconsctructed as a linked list with skip pointers, the head of the linked list is returned
    def get_postings(term, dictionary, postings_file):
        if term in dictionary:
            frequency, offset = dictionary[term]
            postings_file.seek(offset)
            posting_list_raw = postings_file.readline().split()
            skip_count = int(posting_list_raw[0])
            posting_list = [int(i) for i in posting_list_raw[1:]]
            posting_linked_list = construct_linked_list(skip_count, posting_list)
            return posting_linked_list
        else:
            return None

    # Function of constructing a linked list from document IDs and skip count
    def construct_linked_list(skip_count, posting_list):
        head = None
        current = None
        current_skip = None
        counter = 0  # Start counter at 0
        for doc_id in posting_list:
            if head is None:
                head = Node(doc_id)
                current = head
            else:
                current.next = Node(doc_id)
                current = current.next
            # Set skip pointer and reset counter when it reaches skip_count
            if counter == skip_count:
                if current_skip is not None:
                    current_skip.skip = current
                    current_skip = current
                counter = 1  # Reset counter to 1 after setting skip to count correctly for the next skip interval
            else:
                counter += 1
            # Initialize current_skip after the first node is created to ensure the first skip starts from the head
            if current_skip is None:
                current_skip = head
                counter = 1  # Start counting for skip from the first node
        return head

    # Function of searching up for the term frequency from the dictionary
    def get_term_frequency(term, dictionary):
        if term in dictionary:
            return dictionary[term][0]
        else:
            return 0

    # Function that computes the intersection of two posting lists with skip pointers
    def intersect_postings(p1, p2):
        dummy = Node(None)  # Dummy head to simplify insertion
        current = dummy

        while p1 and p2:
            if p1.doc_id == p2.doc_id:
                current.next = Node(p1.doc_id)
                current = current.next
                p1 = p1.next
                p2 = p2.next
            elif p1.doc_id < p2.doc_id:
                # Use skip pointer if it's beneficial; otherwise, move to the next
                if p1.skip and p1.skip.doc_id < p2.doc_id:
                    while p1.skip and p1.skip.doc_id < p2.doc_id:
                        p1 = p1.skip
                else:
                    p1 = p1.next
            else:
                # Use skip pointer if it's beneficial; otherwise, move to the next
                if p2.skip and p2.skip.doc_id < p1.doc_id:
                    while p2.skip and p2.skip.doc_id < p1.doc_id:
                        p2 = p2.skip
                else:
                    p2 = p2.next
        return dummy.next

    # Function that computes the union of two posting lists
    def union_postings(p1, p2):
        # Dummy head node to simplify insertion logic
        dummy = Node(None)
        current = dummy

        while p1 or p2:
            # Determine which node to add next
            if p1 == p2:
                next_node = p1
                p1 = p1.next
                p2 = p2.next
            elif not p2 or (p1 and p1.doc_id < p2.doc_id):
                next_node = p1
                p1 = p1.next
            else:
                next_node = p2
                p2 = p2.next

            # Add the selected node to the result list
            current.next = Node(next_node.doc_id)
            current = current.next
        # Return the start of the merged list, skipping the dummy head
        return dummy.next

    # Function that computes the negation of a posting list (to the full set)
    def negate_postings(p, full_set):
        dummy = Node(None)
        current = dummy

        while p or full_set:
            # If the current document ID is in the full set but not in the posting list, add it to the result
            if full_set and (not p or full_set.doc_id < p.doc_id):
                current.next = Node(full_set.doc_id)
                current = current.next
                full_set = full_set.next
            # If the current document ID is in both the posting list and the full set, skip both
            elif p.doc_id == full_set.doc_id:
                p = p.next
                full_set = full_set.next
            # If the current document ID is in the posting list but not in the full set, skip it
            # However, this case should not happen because the full set should be a superset of the posting list
            else:
                p = p.next
        return dummy.next

    # Function that computes the AND NOT operation between two posting lists
    def and_not_postings(p1, p2):
        dummy = Node(None)
        current = dummy

        while p1 or p2:
            # If the current document ID is in the first list but not in the second list, add it to the result
            if p1 and (not p2 or p1.doc_id < p2.doc_id):
                current.next = Node(p1.doc_id)
                current = current.next
                if p1.skip and (not p2 or p1.skip.doc_id < p2.doc_id):
                    p1 = p1.skip
                else:
                    p1 = p1.next
            # If the current document ID is in both lists, skip it
            elif p1.doc_id == p2.doc_id:
                p1 = p1.next
                p2 = p2.next
            # If the current document ID is in the second list but not in the first list, skip it
            else:
                if p2.skip and (not p1 or p2.skip.doc_id < p1.doc_id):
                    p2 = p2.skip
                else:
                    p2 = p2.next
        return dummy.next

    # This Function uses shunting yard algorithm to convert the infix expression to postfix expression
    def shunting_yard(infix_tokens):
        # Define operator precedence
        precedence = {'NOT': 3, 'AND_NOT': 3, 'AND': 2, 'OR': 1}
        # Define which operators are binary (take two operands)
        binary_operators = {'AND', 'OR', 'AND_NOT'}

        # Output queue and operator stack
        output_queue = []
        operator_stack = []

        # Process each token
        i = 0
        while i < len(infix_tokens):
            token = infix_tokens[i]
            # Consider the special case of 'AND NOT' as a single operator
            # Convert 'AND NOT' to 'AND_NOT' as a single operator to optimise the search speed
            if token == 'AND' and i + 1 < len(infix_tokens) and infix_tokens[i + 1] == 'NOT':
                token = 'AND_NOT'
                i += 1  # Skip the next 'NOT' token

            if token in precedence:  # Operator
                # While there's an operator on the stack with higher precedence, pop it to the output queue
                while (operator_stack and precedence.get(operator_stack[-1], 0) > precedence[token] and
                       operator_stack[-1] != '('):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
            elif token == '(':  # Left parenthesis
                operator_stack.append(token)
            elif token == ')':  # Right parenthesis
                # Pop operators from stack to queue until we hit the left parenthesis
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                operator_stack.pop()  # Remove the left parenthesis
            else:  # Operand
                output_queue.append(token)
            i += 1

        # Pop any remaining operators from the stack to the queue
        while operator_stack:
            output_queue.append(operator_stack.pop())

        # Return the postfix expression as a list of tokens
        return output_queue

    def normalise_and_stem(tokens):
        Operator = ['AND', 'OR', 'NOT', '(', ')']
        normalised_tokens = []
        stemmer = PorterStemmer()
        for token in tokens:
            if token in Operator:
                normalised_tokens.append(token)
                continue
            # Convert to lower case
            token = token.lower()
            # Remove stop words
            normalised_tokens.append(stemmer.stem(token))
        return normalised_tokens

    # This function evaluates the postfix expression and computes the final search result
    # A linked list containing the final result if returned
    def evaluate_postfix(postfix, dictionary, postings_file):
        full_set = get_full_set_postings(dictionary, postings_file)
        operand_stack = []
        for token in postfix:
            if token not in {'AND', 'OR', 'NOT', 'AND_NOT'}:
                # If the token is an operand, push the posting list to the stack
                operand_stack.append(get_postings(token, dictionary, postings_file))
            else:
                # If the token is an operator, pop the required number of operands from the stack,
                # perform the operation, and push the result back to the stack
                if token == 'NOT':
                    right_operand = operand_stack.pop()
                    result = negate_postings(right_operand, full_set)
                elif token == 'AND':
                    right_operand = operand_stack.pop()
                    result = intersect_postings(right_operand, operand_stack.pop())
                elif token == 'AND_NOT':
                    right_operand = operand_stack.pop()
                    result = and_not_postings(operand_stack.pop(), right_operand)
                elif token == 'OR':
                    right_operand = operand_stack.pop()
                    result = union_postings(right_operand, operand_stack.pop())
                operand_stack.append(result)
        return operand_stack.pop()

    # Function that checks if the query is valid
    def is_valid_query(query):
        # Regular expression to match valid tokens with proper whitespace
        token_pattern = re.compile(r'(?:\s*\b(?:AND|OR)\b\s+NOT\s+|\s*\b(?:AND|OR|NOT)\b\s+|\s*\(|\)\s*|\w+\s*)')
        tokens = token_pattern.findall(query)

        # Reconstruct the query from tokens to remove extra spaces
        reconstructed_query = ''.join(tokens).strip()

        # Check if the reconstructed query matches the original query (to ensure proper whitespace usage)
        if reconstructed_query != query.strip():
            return False  # Invalid spacing or unrecognized tokens

        # Check for invalid sequences such as 'NOT AND', 'NOT OR', 'AND AND', etc.
        invalid_sequences = ['NOT AND', 'NOT OR', 'AND AND', 'OR OR']
        for seq in invalid_sequences:
            if seq in reconstructed_query:
                return False  # Found an invalid sequence
        return True

    # Tokenize the query in a custom way to handle period and apostrophe in the query
    def custom_tokenize(text):
        # Preprocessing: Protect specific punctuation with placeholders
        protected_text = text.replace('.', 'R_PERIOD').replace("'", "R_APOSTROPHE")

        # Tokenize
        tokens = word_tokenize(protected_text)

        # Postprocessing: Restore the protected punctuation
        restored_tokens = [token.replace('R_PERIOD', '.').replace('R_APOSTROPHE', "'") for token in tokens]

        return restored_tokens

    # Function that checks if the input query is valid
    # It returns FALSE if the query is invalid, otherwise it returns TRUE
    # Cases such as 'AND AND', 'OR OR' are examined in this function to ensure the query is valid
    def is_valid_query(tokens):
        # Start with expecting a term, NOT, or '('
        expected_tokens_start = {'TERM', 'NOT', '('}

        # Rules for token sequences
        valid_next_tokens = {
            'TERM': {'AND', 'OR', ')'},
            'AND': {'TERM', 'NOT', '('},
            'OR': {'TERM', 'NOT', '('},
            'NOT': {'TERM', '('},
            '(': {'TERM', 'NOT', '('},
            ')': {'AND', 'OR', ')'},
        }

        accepted_tokens = {'TERM', 'AND', 'OR', 'NOT', '(', ')'}

        # Convert all non-operator tokens to 'TERM'
        parsed_tokens = ['TERM' if token not in accepted_tokens else token for token in tokens]

        for i, token in enumerate(parsed_tokens):
            if token not in expected_tokens_start:
                print(f'Unexpected token: {token}')
                return False  # Found an unexpected token

            # Update expected tokens based on the current token
            expected_tokens = valid_next_tokens.get(token, set())

        if parsed_tokens[-1] in {'AND', 'OR', 'NOT'}:
            print('The query should not end with an operator')
            return False

        return True

    # Function that process the query list and write the result to the result file
    def process_query(queries, dictionary, postings_file, results_file):
        for query in queries:
            infix_tokens = custom_tokenize(query)
            # Check if the query is valid
            if not is_valid_query(infix_tokens):
                results_file.write('The input is invalid' + '\n')
                continue
            # Normalise and stem the tokens
            tokens = normalise_and_stem(infix_tokens)
            # Convert the infix expression to postfix
            postfix = shunting_yard(tokens)
            # Evaluate the postfix expression to get the final result
            result = evaluate_postfix(postfix, dictionary, postings_file)
            # Write the result to the result file
            if result:
                doc_ids = []
                current_node = result
                while current_node:
                    doc_ids.append(str(current_node.doc_id))
                    current_node = current_node.next
                results_file.write(' '.join(doc_ids) + '\n')
            else:
                results_file.write('\n')

    # Function to read term, frequency and offset from a line in dictionary
    def read_dictionary_line(line):
        # Split the line by space to get term, frequency and offset
        term, frequency, offset = line.split(' ')
        term = term.strip()  # Remove leading/trailing white spaces
        frequency = frequency.strip()  # Remove leading/trailing white spaces
        offset = offset.strip()  # Remove leading/trailing white spaces

        # Convert frequency and offset from strings to integers
        frequency = int(frequency)
        offset = int(offset)

        return term, frequency, offset

    """ 
    Below part of the code is the main part of the function that executes the search
    """
    # Read in the queries
    qf = open(queries_file, 'r')
    queries = qf.readlines()

    # Reconstructing the dictionary from the file into memory
    dictionary = {}
    df = open(dict_file, 'r')
    dictionary_raw = df.readlines()
    for line in dictionary_raw:
        term, frequency, offset = read_dictionary_line(line)
        dictionary[term] = (frequency, offset)

    # Create a file to write the results
    rf = open(results_file, 'w')

    # Process the queries and write to the result file
    process_query(queries, dictionary, postings_file, rf)


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
