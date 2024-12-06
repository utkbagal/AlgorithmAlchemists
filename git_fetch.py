import shutil
import git
import os
import time


def clone_repository(repo_url, clone_dir):
    try:
        # Clone the repository
        delete_folder(clone_dir)
        git.Repo.clone_from(repo_url, clone_dir)
        print(f'Repository cloned to: {clone_dir}')
    except Exception as e:
        print(f'An error occurred: {e}')


def track_file(directory, target_filename):
    print(f"Tracking '{target_filename}' in '{directory}' and its subdirectories...")

    while True:
        found = False
        for root, dirs, files in os.walk(directory): #--> Walk through the directory and its subdirectories
            if target_filename in files:
                found = True
                file_path = os.path.join(root, target_filename)
                print(f"File found: {file_path}")# -->path for search file
                with open(file_path, 'r', encoding='utf-8') as file:#---> Read the content of the file
                    content = file.read()
                    print("File content:")
                    #print(content)
                    return content

        if found:
            break
        time.sleep(1) # Sleep for a while before checking again


def delete_folder(folder_path):
    try:
        # Change permissions recursively
        for root, dirs, files in os.walk(folder_path):
            for name in files:
                file_path = os.path.join(root, name)
                os.chmod(file_path, 0o777)  # Change permission for files
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.chmod(dir_path, 0o777)  # Change permission for directories

        # Now delete the folder
        shutil.rmtree(folder_path)
        print(f"Successfully deleted the folder: {folder_path}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    clone_dir = 'demo/source'
    repo_url = 'https://github.com/IBM/cobol-is-fun.git'
    directory_to_watch = 'demo\source\mypy'
    file_to_track = 'fxsort.cbl'
    #delete_folder(clone_dir)
    #clone_repository(repo_url,clone_dir)
    source=track_file(clone_dir,file_to_track)
    print(source)
