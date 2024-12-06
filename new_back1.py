import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from openai import AzureOpenAI
from get_repo_structure import invoke_list_all_files_and_dirs
from git_fetch import track_file, clone_repository
import re
from nltk.tokenize import word_tokenize
from docs_retriever import run_retriever


def find_full_filename(input_string, search_term):
    # Split the input string into lines
    lines = input_string.split('\n')

    # Iterate over each line
    for line in lines:
        # Check if the search term is in the line
        if search_term.lower() in line.lower():
            # Extract and return the full file name
            parts = line.split('\\')
            return parts[-1]
def extract_components(cobol_program):
    # Example patterns for copybooks, declgens, and subprograms (adjust as needed)

    copybook_pattern = r'COPY\s+([\w\-]+)\.'
    subprogram_pattern = r'CALL\s+["\']([\w\-]+)["\']'
    subroutine_pattern = r'PERFORM\s+([\w\-]+)'
    declgen_pattern = r'EXEC SQL INCLUDE\s+([^\s]+)\s+END-EXEC'

    copybooks = re.findall(copybook_pattern, cobol_program, re.IGNORECASE)
    subprograms = re.findall(subprogram_pattern, cobol_program, re.IGNORECASE)
    subroutines = re.findall(subroutine_pattern, cobol_program, re.IGNORECASE)
    declgens = re.findall(declgen_pattern, cobol_program, re.IGNORECASE)
    if 'SQLCA' in declgens:
        declgens.remove('SQLCA')

    #copybook_pattern = re.compile(r'COPY\s+(\S+)\s*\.')
    #declgen_pattern = re.compile(r'EXEC\s+SQL\s+INCLUDE\s+(\S+)\s*\.')
    #subprogram_pattern = re.compile(r'CALL\s+"(\S+)"')

    #copybooks = copybook_pattern.findall(cobol_program)
    #declgens = declgen_pattern.findall(cobol_program)
    #subprograms = subprogram_pattern.findall(cobol_program)

    modules_dict = {
        "copybooks": copybooks,
        "declgens": declgens,
        "subprograms": subprograms
    }
    print(modules_dict)
    return copybooks, declgens, subprograms, modules_dict


def load_component(component_name,storage_path):
    print(component_name)
    try:
        repo_files = invoke_list_all_files_and_dirs(storage_path)
        filename = find_full_filename(repo_files,component_name)
        print(filename)
        if filename:
            file_text = track_file(storage_path, filename)
            return file_text
    except FileNotFoundError:
        return ""


def load_all_components(copybooks, declgens, subprograms, storage_path):
    components = {}

    for copybook in copybooks:
        components[copybook] = load_component(copybook, storage_path)

    for declgen in declgens:
        components[declgen] = load_component(declgen, storage_path)

    for subprogram in subprograms:
        components[subprogram] = load_component(subprogram, storage_path)

    return components


def prepare_context(cobol_program, components):
    context = cobol_program
    for name, content in components.items():
        context += f"\n\n{name}:\n{content}"
    return context


def query_llm(context, question):
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
    prompt = f"{context}\n\nQuestion: {question}"
    response = llm.invoke(prompt)

    return response.content


def analyze_cobol_program(prog_name, cobol_program, question, storage_path):
    # Step 1: Extract components
    copybooks, declgens, subprograms, modules_dict = extract_components(cobol_program)

    modules_dict["program"] = [prog_name]
    # Step 2: Load components from storage
    components = load_all_components(copybooks, declgens, subprograms, storage_path)

    # Step 3: Prepare context
    context = prepare_context(cobol_program, components)

    tokens = word_tokenize(context)
    print(len(tokens))

    retrieved_info = ''
    retrieved_query_answer = ''
    #"""
    # Step 4: Query LLM for unclear vars/terms
    que1 = '''Consider that you need to provide complete logic of the provided cobol program and context provided. 
    Please come up with list of business variables/terms without meaningful context or which you are not able to understand(not cobol statements). Be concise, do not include anything extra than final list. Do not include lines of code.
    Mention clearly if you did not find meaningful context for any variable and only list them out. Do not make it up.'''

    ans = query_llm(context, que1)
    #print('11111111111111111111111----->', ans)
    que2 = '''Provide concise meaning/understanding for below variables/business terms
    with respect to context provided?'''

    # retrieve info from docs for unclear vars/terms
    retrieved_info = run_retriever(index_name='aa-docs-db',
                                   query=que2 + ans, module_name=prog_name)
    #print('22222222222222222222222----->', retrieved_info)
    # retrieve context from docs wrt user question.

    retrieved_query_answer = run_retriever(index_name='aa-docs-db',
                                           query=question, module_name=prog_name)
    #print('33333333333333333333333----->', retrieved_query_answer)
    context = retrieved_info + retrieved_query_answer + context
    print(context)
    # final generate final response:
    #"""

    ans = query_llm(context, question)
    return ans


def generate_dsl(response):
    que = 'Convert provided code logic into DSL so that Graph TD DSL can be used to create flowchart/graph TD using mermaid.js class. Provide only DSL Output.'
    flowchart_dsl = query_llm(response, que)
    return flowchart_dsl


def generate_flowchart(response):
    que = 'Write a html page to display gicen DSL as flowchart/graph TD with help of mermaid.js class. Do not provide additional explanation.'
    flowchart_file = query_llm(response, que)
    return flowchart_file

# Example usage
if __name__ == "__main__":
    loader = TextLoader("C:/Users/2000110656/PycharmProjects/Cobol_Analyser/demo/source/app/cbl/COBIL00C.cbl")
    prog_name = 'COBIL00C'
    cobol_program = loader.load()
    cobol_program_text = cobol_program[0].page_content
    question = "what does this program do?"
    # question = "when field EMP_SALARY is increased by 1000? Do not include lines from code"
    storage_path = "../Cobol_Analyser/demo/source/"

    answer = analyze_cobol_program(prog_name, cobol_program_text, question, storage_path)
    #print(answer)
