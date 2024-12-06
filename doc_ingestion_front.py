import os
import streamlit as st
import fnmatch
from langchain_community.document_loaders import TextLoader
from get_repo_structure import invoke_list_all_files_and_dirs
from doc_ingestion_back import create_new_index, delete_index, find_ids_in_index, check_new_index, ingestion


st.set_page_config(layout="wide")
if 'disabled2' not in st.session_state:
    st.session_state.disabled2 = True
if 'disabled3' not in st.session_state:
    st.session_state.disabled3 = True
if 'disabled4' not in st.session_state:
    st.session_state.disabled4 = True
if 'stage' not in st.session_state:
    st.session_state.stage = 0
if 'ix_status' not in st.session_state:
    st.session_state.ix_status = 0
if 'ingestion_status' not in st.session_state:
    st.session_state.ingestion_status = 0

index_status = ''
msg = ''
def enable2():
    st.session_state.disabled2 = False


def enable3():
    st.session_state.disabled3 = False


def enable4():
    st.session_state.disabled4 = False

def disable3():
    st.session_state.disabled3 = True
def disable4():
    st.session_state.disabled4 = True

def ix_status0():
    st.session_state.ix_status = 0


def ix_status1():
    st.session_state.ix_status = 1


def ingestionStatus0():
    st.session_state.ingestion_status = 0
def ingestionStatus1():
    st.session_state.ingestion_status = 1

def set_stage(stage):
    st.session_state.stage = stage


st.title(':rainbow[Algorithm Alchemists]')
st.header('AI powered :blue[Code Analyzer for Legacy systems]')
st.subheader(':violet[Module 1: Business Context/documents loader]')
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    with st.form("my_form1"):
        st.header('Step 1')
        index_name = st.text_input("Please enter an Index Name")
        st.write("A new index will be created in Vector DB if an index with entered name is not available:")

        submitted1 = st.form_submit_button("Submit", on_click=set_stage, args=(1,))

        if submitted1 and len(index_name) == 0:
            st.write(":red[INVALID Vector DB Index Name]")
            disable3()
        if submitted1 and len(index_name) > 0:
            enable2()
            disable3()
            index_status = check_new_index(index_name)
            if index_status == 'IndexAlreadyPresent':
                ix_status1()
                st.write(":orange[An index with same name is already present in DB!]")
            else:
                create_new_index(index_name)
                st.write(":green[Index Created Successfully!]")

        if st.session_state.ix_status == 1:
            enable4()
            submitted4 = st.form_submit_button("Delete Index", on_click=set_stage, args=(2,),
                                               disabled=st.session_state.disabled4)
            if submitted4:
                ix_status0()
                disable4()
                msg = delete_index(index_name)
            st.write(msg)

with col2:
    with st.form("my_form2"):
        st.header('Step 2')
        st.write("Please place your documents in folder :blue['demo/docs']")
        st.write("Documents available to load:")
        repo_files = invoke_list_all_files_and_dirs('demo/docs')
        st.write(repo_files)
        submitted2 = st.form_submit_button("Confirm", on_click=set_stage, args=(3,), disabled=st.session_state.disabled2)
        if submitted2:
            enable3()
            ingestionStatus0()
            st.write(":green[Documents are ready to be loaded into Vector DB]")

with col3:
    with st.form("my_form3"):
        st.header('Step 3')
        st.write("Documents will loaded into Vector DB.")
        st.write("While analysing the source code, these documents will serve additional context (business context/technical terminology etc.)")
        submitted3 = st.form_submit_button("Load", on_click=set_stage, args=(4,), disabled=st.session_state.disabled3)
        if submitted3:
            disable3()
            ingestion_status = ''
            if st.session_state.ingestion_status != 1:
                ingestion_status = ingestion()
                ingestionStatus1()
            st.write(f":blue[{ingestion_status}]")