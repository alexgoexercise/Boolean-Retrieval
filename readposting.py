def read_file_with_pointer(file_path, pointer):
    try:
        with open(file_path, 'r') as file:
            # Move the file pointer to the specified position
            file.seek(pointer)
            # Read and print the content from the specified position to the end of the file
            content = file.readline()
            print(content)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage:
file_path = "temp_posting"  # Replace with your file path
pointer = 8564 # Replace with the desired pointer position
read_file_with_pointer(file_path, pointer)
