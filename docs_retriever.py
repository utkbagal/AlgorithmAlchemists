import os
from openai import AzureOpenAI
from pinecone import Pinecone, ServerlessSpec
from time import sleep
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter, Language, RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
from langchain_core.runnables import RunnablePassthrough


llm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")

def query_llm(context, question):

    prompt = f"{context}\n\nQuestion: {question}"
    response = llm.invoke(prompt)

    return response.content


def split_into_chunks(src_txt):
    cobol_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.COBOL, chunk_size=2000, chunk_overlap=200
    )
    return cobol_splitter.create_documents(src_txt)


def generate_txt(input_str):
    que = '''As a Cobol language expert, analyze and create a short summary for given piece of cobol code.
    Keep the answer concise and technical. Include (only if relevant) what does this piece of code do, input variables, output variables and any calls it makes.'''
    generated_response = query_llm(input_str, que,)
    return generated_response


def load_into_vector_db(index_name, module_name, source_text, summary):
    index = pc.Index(index_name)
    vectors = client.embeddings.create(
        input=source_text+'\n summary of above piece of code:'+summary,
        model="text-embedding-ada-002"
    )

    embedding = vectors.data[0]
    metadata = {
        'source': module_name,
        'text': source_text,
        'summary': summary
    }
    index.upsert([(module_name, embedding.embedding, metadata)])
    sleep(1)  # To avoid hitting rate limits


def format_docs(docs):
    return"\n\n".join(doc.page_content for doc in docs)

def run_retriever(index_name, module_name, query: str, ):
    print('Retrieving...')

    vectors = client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    )

    embeddings = AzureOpenAIEmbeddings()
    # embeddings = client.embeddings

    vectorstore = PineconeVectorStore(pinecone_api_key=os.getenv("PINECONE_API_KEY"),
                                      index_name=index_name, embedding=embeddings)

    template = """Use the following pieces of context to answer the question about the cobol program
    in context at the end. If you don't know the answer, just say that you could not find relevant information, 
    don't try to make up an answer, just return whatever context was provided in the answer. Keep the answer as concise as possible.

    {context}

    Question: {question}

    Helpful Answer: """

    custom_rag_prompt = PromptTemplate.from_template(template)
    # retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    # combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)

    rag_chain = (
            {"context": vectorstore.as_retriever() | format_docs, "question": RunnablePassthrough()}
            | custom_rag_prompt
            | llm
    )
    result = rag_chain.invoke(query)
    return result

if __name__ == '__main__':
    print('loading data...')

    loader = TextLoader("demo/source/app/cbl/CBACT01C.cbl")
    document_data = loader.load()
    print('data loading completed...')

    cobol_chunks = split_into_chunks([document_data[0].page_content])

    print(f'created {len(cobol_chunks)} chunks')

    print('splitting completed...')
    print(cobol_chunks[0].page_content)

    #for i in range(len(cobol_chunks)):
    #    response = generate_txt(cobol_chunks[i].page_content)
    #    load_into_vector_db('aa-db-source','CBACT01C.cbl', source_text=cobol_chunks[i].page_content,summary=response)
    #    print(response)

    res = run_retriever(index_name='aa-docs-db', query="what does GOTO statement do in a Cobol program?", module_name='CBACT01C.cbl')
    print(res.content)