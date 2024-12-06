import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from git_fetch import track_file, clone_repository
from new_back1 import analyze_cobol_program, generate_dsl, generate_flowchart
from get_repo_structure import invoke_list_all_files_and_dirs
from pathlib import Path

st. set_page_config(layout="wide")
if 'stage' not in st.session_state:
    st.session_state.stage = 0


def set_stage(stage):
    st.session_state.stage = stage


if 'answer1' not in st.session_state:
    st.session_state.answer1 = ''

if 'answer2' not in st.session_state:
    st.session_state.answer2 = ''


def answer1(ans):
    st.session_state.answer1 = ans


def answer2(ans):
    st.session_state.answer2 = ans


st.title(':rainbow[Algorithm Alchemists]')
st.header('AI powered :blue[Code Analyzer for Legacy systems]')

col1, col2 = st.columns([1, 3])
with col1:
    with st.form("my_form1"):
        st.write("Please Enter Code Repo Details:")
        repo_url = st.text_input("Please enter Github Repo URL")
        #repo_access_key = st.text_input("Access key to the Code repo")
        # Every form must have a submit button.
        submitted1 = st.form_submit_button("Submit", on_click=set_stage, args=(1,))
        if submitted1:
            st.write("Repo", repo_url, )
    if st.session_state.stage > 0:
            st.write("Source files from repository:", repo_url, )
            clone_dir = 'demo/source'
            clone_repository(repo_url,clone_dir)
            directory_path = "demo/source"
            repo_files = invoke_list_all_files_and_dirs(clone_dir)
            st.write(f"**{repo_files}**")

with col2:
    with st.form("my_form2"):
        task_selected = st.radio(
            "What would you like to do:",
            ["Query specific code module","Analyze specific code module completely"],
            #["Query specific code module","Analyze specific code module", "Analyze all modules from a directory"],
             )
        user_query = ''
        if task_selected == 'Query specific code module':
            module_name = st.text_input("Please enter Module name that you want to query")
            user_query = st.text_input("Please enter your question")
        if task_selected == 'Analyze specific code module completely':
            module_name = st.text_input("Please enter Module name that you want to query")

        submitted2 = st.form_submit_button("Submit", on_click=set_stage, args=(2,))
        if st.session_state.stage > 1 and len(user_query) > 0:
            clone_dir = 'demo/source'
            src_module_name = module_name
            if src_module_name in repo_files:
                response = track_file(clone_dir,src_module_name)
            else:
                st.write('Invalid module name:', src_module_name)
            a = ''
            #if task_selected == 'Query specific code module':
            #    question = 'Consider that you need to provide complete logic of the provided cobol program and context provided. Please come up with list of business variables/terms (not cobol statements) and your understanding about them. Be concise, do not include anything extra than final list. Do not include lines of code. Mention clearly if you did not find meaningful context for any variable and only list them out. Do not make it up.'
            #    answer = analyze_cobol_program(src_module_name, response, question, clone_dir)
            #    ht = 25 * len(answer.splitlines())
            #    st.write("Before I proceed with analysis, here are some terms/variables which are not very clear to me. Please provide some context for those below so that I can interpret the code more efficiently!")
            #    a = st.text_area(value=answer, label="Modify below if required:",height=ht)
            #    #a = st.text_area(value=answer)
            #    print(a)
        if st.session_state.stage > 1 and len(user_query) > 0:

            if task_selected == 'Query specific code module':
                #st.write(f"**{response}**")
                question = 'As a COBOL language expert, analyse the cobol program in context of following question.'
                question = question + user_query + 'Please be concise with answer. Do not answer if input does not contain any COBOL statements and just mention *input is not a COBOL code*. Try to include Business terms as much as possible'
                if st.session_state.stage == 2:
                    ans1 = analyze_cobol_program(src_module_name, response, question, clone_dir)
                    answer1(ans1)
                else:
                    answer = st.session_state.answer1
                st.write(f"**{st.session_state.answer1}**")
    with st.form("my_form3"):
        if st.session_state.stage > 1 and task_selected == 'Analyze specific code module completely' and len(module_name) > 0:
            clone_dir = 'demo/source'
            src_module_name = module_name
            response = track_file(clone_dir,src_module_name)
            #st.write(f"**{response}**")
            question = '''Can you explain complete logic of the program? no need to be descriptive. Do not miss out any details. Do not include lines of code.'
            Try to include Business terms as much as possible.'''
            if st.session_state.stage == 2:
                ans2 = analyze_cobol_program(src_module_name, response, question, clone_dir)
                answer2(ans2)
            else:
                answer = st.session_state.answer2
            st.write(f"**{st.session_state.answer2}**")


        submitted3 = st.form_submit_button("Generate Flowchart", on_click=set_stage, args=(3,))
        if st.session_state.stage > 2:
            # st.write(f"**{response}**")
            flowchart_dsl = generate_dsl(answer)

            flowchart_file = generate_flowchart(flowchart_dsl)
            source_code = flowchart_file
            lines = source_code.splitlines()
            num_lines = len(lines) * 50
            components.html(source_code,  height=num_lines)
            #print(source_code)
            #st.write(f"**{source_code}**")
