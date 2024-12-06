from pathlib import Path

def list_all_files_and_dirs(directory, result_list):
    for path in Path(directory).iterdir():
        if path.is_dir():
            result_list.append(f"**Directory:** {path}")
            list_all_files_and_dirs(path, result_list)  # Recursively list the contents of the directory
        else:
            result_list.append(f"**File:** {path}")


def invoke_list_all_files_and_dirs(directory_path):
    result_list = []
    # Call the function with the desired directory
    list_all_files_and_dirs(directory_path, result_list)

    files_list = [x for x in result_list if 'Directory:' not in x]
    # Join the list into a single string with each path on a new line
    # result_string = "\n\n".join(result_list)
    result_string = "\n\n".join(files_list)
    return result_string
    # Initialize an empty list to store the results
if __name__ == "__main__":
    result_string = ''
    directory = 'demo/source'
    result_string = invoke_list_all_files_and_dirs(directory)
    # Print the result string
    print(result_string)