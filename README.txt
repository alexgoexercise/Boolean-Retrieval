This is the README file for A0000000X's submission
Email(s): e0795130@u.nus.edu
e0774464@u.nus.edu

== Python Version ==

I'm (We're) using Python Version <3.10.12 or replace version number> for
this assignment.

== General Notes about this assignment ==

General Description:
This code consists of two parts: index construction which is handled by index.py and search which is handled by search.py.
The index is stored in the hard disk and is loaded when the search is performed.
The search is handled by search.py and is performed by processing the query and returning the index of relevant documents.

Main Algorithm used:
The main algorithm used in the index construction is SPIMI: Single-pass in-memory indexing.
When the memory limit is reached, the index is written to the hard disk and the memory is cleared.
Main step:
1. Two temporary files temp_dict and temp_posting are used to store the dictionary and posting lists temporarily.
2. When the memory limit is reached, the dictionary and posting lists are written to these two files in blocks.
3. After all the files are processed, the temp_dict and temp_posting files are merged to form the
final dictionary and posting lists.

The main algorithm used in the search is Boolean Retrieval Model.
Shunting Yard Algorithm is used to interpret the query by converting it into postfix notation.
Main step:
1. The query is tokenized and converted into postfix notation using the shunting yard algorithm.
2. The postfix notation is then processed to return the index of relevant documents.

Things to Notice:
1.
The dictionary and posting lists are stored in the form of .txt file, which is prone to attacks if
someone tries to modify the files. Hence, please try not to touch or modify those files.
2.
The query handling part of this program is not designed to handle malicious checks. For example, unbalanced parenthesis, etc.
There is a simple query validity check, however, it only handles a few extreme cases of wrong input that I can think of.
3.
As noticed by our team, the formatting of text files between Windows and MacOS is different, especially when it
comes to handeling new lines. Hence, the program may not work properly if the text files are generated in Windows and
run in MacOS or vice versa. Please make sure to run the program in the same OS that the text files are generated in.

== Files included with this submission ==

main files to be executed:
index.py: This is the python program that constructs the index and store them into hard disk.
search.py: This is the python program that processes the query and returns the index of relevant documents.

other files:
README.txt: This file is served as an explanation of the submission.
sanity-queries.txt: This file contains the queries that are used to test the search.py program.
ESSAY.txt: This file contains the answers to the essay questions.

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[ x ] I/We, A0242210A, A0239866J certify that I/we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I/we
expressly vow that I/we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==

shunting yard: https://tylerpexton-70687.medium.com/the-shunting-yard-algorithm-b840844141b2#:~:text=The%20Shunting%2Dyard%20algorithm%20works,expression%20from%20left%20to%20right.

