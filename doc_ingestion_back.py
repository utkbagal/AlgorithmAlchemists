import os
import fnmatch
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader, Docx2txtLoader, PyPDFLoader
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from openai import AzureOpenAI
import re
from langchain_text_splitters import CharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from time import sleep
from pathlib import Path
import docx2txt

def list_all_files_and_dirs(directory, result_list):
    for path in Path(directory).iterdir():
        if path.is_dir():
            #result_list.append(f"**Directory:** {path}")
            list_all_files_and_dirs(path, result_list)  # Recursively list the contents of the directory
        else:
            result_list.append(path)

def invoke_list_all_files_and_dirs(directory):
    result_list = []
    # Call the function with the desired directory
    list_all_files_and_dirs(directory, result_list)

    return result_list


def check_new_index(ix_name:str):
    index_name = ix_name
    print(ix_name)

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")

    if index_name in pc.list_indexes().names():
        return 'IndexAlreadyPresent'

def create_new_index(ix_name:str):
    index_name = ix_name
    print(ix_name)

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")

    if index_name not in pc.list_indexes().names():
        print("Index does not exist, creating...")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric='cosine',
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )


def find_ids_in_index(ix_name:str):
    index_name = ix_name
    print(ix_name)

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")
    index_info = pc.describe_index(index_name)

    index = pc.Index(host=index_info['host'])
    return 'not yet fixed'

    # for ids in index.list():
    #    print(ids)


def delete_index(ix_name:str):

    index_name = ix_name
    print(ix_name)

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")

    if index_name not in pc.list_indexes().names():
        return "Index does not exist!"
    else:
        pc.delete_index(index_name)
        return "Index deleted successfully!"
def store_vectors(chunks):
    print('Ingesting data...')

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")
    
    index_name = 'aa-docs-db'
    index = pc.Index(index_name)

    for i, doc in enumerate(chunks):
        print('loading chunk#', i)
        text_content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        response = client.embeddings.create(
            input=text_content,
            model="text-embedding-ada-002"
        )
        # print(type(response))
        # embedding = response['data'][0]['Embedding']
        embedding = response.data[0]
        metadata = {
            'source': doc.metadata['source'],
            'text': text_content
        }
        # print(metadata)
        # Store the embedding in Pinecone
        index.upsert([(f"{doc.metadata['source']}-{i}", embedding.embedding, metadata)])
        sleep(1)  # To avoid hitting rate limits

def split_pages(pages):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separator=" ")
    texts = text_splitter.split_documents(pages)
    print(f'created {len(texts)} chunks')
    return texts

def load_docs(docs_lst):
    # Call the function with the desired directory
    for filename in docs_lst:
        print(filename)
        if fnmatch.fnmatch(filename, '*.pdf') or fnmatch.fnmatch(filename, '*.PDF'):
            loader = PyPDFLoader(filename)
            # document_data = loader.load()
            pages = loader.load_and_split()
            print('data loading completed...')
            print('splitting the loaded data...')

            chunks = split_pages(pages)
            print('splitting completed...')

            store_vectors(chunks)

        if fnmatch.fnmatch(filename, '*.txt') or fnmatch.fnmatch(filename, '*.TXT'):
            loader = TextLoader(filename)
            document_data = loader.load()
            print('data loading completed for ', filename)
            print('splitting the loaded data...')

            chunks = split_pages(document_data)
            print('splitting completed...')

            store_vectors(chunks)

        if fnmatch.fnmatch(filename, '*.doc') or fnmatch.fnmatch(filename, '*.docx') or fnmatch.fnmatch(filename, '*.DOC') or fnmatch.fnmatch(filename, '*.DOCX'):
            print(filename)
            loader = Docx2txtLoader(filename)
            document_data = loader.load_and_split()
            print('data loading completed for ', filename)
            print('splitting the loaded data...')

            chunks = split_pages(document_data)
            print('splitting completed...')

            store_vectors(chunks)
    return 'Successfully Stored Vectors!'


def ingestion():
    directory_path = 'demo/docs'
    docs_list = invoke_list_all_files_and_dirs(directory_path)
    ingestion_status = load_docs(docs_list)
    return ingestion_status


if __name__ == '__main__':
    #ids = find_ids_in_index('aa-docs-db')
    #print(ids)
    #msg = delete_index('aa-docs-db')
    #print(msg)
    #create_new_index('aa-docs-db')
    #print('********* loading data *********')
    # docs_list = invoke_list_all_files_and_dirs(directory)
    # load_docs(docs_list)
    msg = ingestion()
    print('Ingestion completed...')