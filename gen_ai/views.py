from django.http import HttpResponse
from django.template import loader
from genai.credentials import Credentials
from genai.model import Model
from genai.schemas import GenerateParams
from django.shortcuts import render,redirect
import pdfplumber
import pandas as pd
import docx2txt
import os
import chromadb
import uuid
from .models import params,summ
from chromadb.config import Settings
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO
from django.contrib.auth import login, logout

pd.set_option('display.max_columns', None)

current_directory = os.getcwd()



creds = Credentials("pak-Z6XDyVA-pB3SKkNx00aKzSmy2BVbbvf1xdx0a2-n4xs", api_endpoint="https://bam-api.res.ibm.com/v1")
client = chromadb.PersistentClient(path=f"{current_directory}/collection",settings=Settings(allow_reset=True))
#client = chromadb.PersistentClient(path=f"s3://my-bucket-anan/collection/",settings=Settings(allow_reset=True))

binary_params = GenerateParams(decoding_method="greedy", max_new_tokens=3, temperature=0.1)
binary = Model("google/flan-ul2", params=binary_params, credentials=creds)


def generate_unique_id():
    return str(uuid.uuid4())    

def update_from_doc(collection_name,data,input_source,input_title):
    collection = client.create_collection(name=collection_name)
    for i in data:
        print(i)
        collection.add(
        ids=generate_unique_id(),
        documents=[i],
        metadatas=[{"source":input_source,"title":input_title}],)   



def make_prompt_binary(context,params):
   return (f"""{params}\n"""
          + f"Information :\n{context}.\n\n")

def count_occurence(chunks,params):
    occurence_list=[]
    for i in chunks:
        prompt_text_binary=make_prompt_binary(i,params)
        print(prompt_text_binary)
        binary_response = binary.generate([prompt_text_binary])   
        binary_gen = binary_response[0].generated_text
        occurence_list.append(binary_gen)
        print(binary_gen)
    yes_count=occurence_list.count('yes')
    total_count=len(occurence_list)
    percent_match=round((yes_count/total_count)*100,2)
    return percent_match

def generateparams(decoding,token,temp,model,creds):
    model_param=GenerateParams(decoding_method=decoding, max_new_tokens=token, temperature=temp)
    output = Model(model, params=model_param, credentials=creds)
    return output

def generate_answer(alice,lines):
    alice_response = alice.generate([lines])   
    alice_gen = alice_response[0].generated_text
    return alice_gen

def extract_text_from_excel(file_path):

    excel_file = pd.ExcelFile(file_path)


    all_split_dataframes = []
    split_dataframes = []


    for sheet_name in excel_file.sheet_names:

        df = excel_file.parse(sheet_name)

        rows_per_split = 15
        if len(df)<rows_per_split:
            split_dataframes.append(df)
        else:    
            num_splits = len(df) // rows_per_split
            
    
            for i in range(num_splits):
                start_row = i * rows_per_split
                end_row = (i + 1) * rows_per_split
                split_df = df.iloc[start_row:end_row, :]
                split_dataframes.append(split_df)
            
            if len(df) % rows_per_split != 0:
                remaining_rows = df.iloc[end_row:, :]
                split_dataframes[-1] = pd.concat([split_dataframes[-1], remaining_rows], axis=0)
    
    
        all_split_dataframes.extend(split_dataframes)


    return all_split_dataframes

def extract_text_from_docx(file_path):
    text=''
    text = docx2txt.process(file_path)
    chunks=get_overlapped_chunks(text, 1000, 300)
    return chunks


def extract_text_from_csv(file_path):
    text = pd.read_csv(file_path)
    df = pd.DataFrame(text)
    split_dataframes = []
    rows_per_split = 15
    if len(df)<rows_per_split:
            split_dataframes.append(df)
    else:        
        num_splits = len(df) // rows_per_split
        for i in range(num_splits):
            start_row = i * rows_per_split
            end_row = (i + 1) * rows_per_split
            split_df = df.iloc[start_row:end_row, :]
            split_dataframes.append(split_df)
    
        if len(df) % rows_per_split != 0:
            remaining_rows = df.iloc[end_row:, :]
            split_dataframes[-1] = pd.concat([split_dataframes[-1], remaining_rows], axis=0)


    return split_dataframes

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    chunks=get_overlapped_chunks(text, 1000, 300)
    return chunks

def extract_text_from_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        chunks=get_overlapped_chunks(text, 1000, 300)
        return chunks
    except Exception as e:
        return str(e)

def get_overlapped_chunks(textin, chunksize, overlapsize):  
    return [textin[a:a+chunksize] for a in range(0,len(textin), chunksize-overlapsize)]  

def to_text(file_name,name):
    file_extension = name.split('.')[-1].lower()
    if file_extension == 'xlsx':
        return extract_text_from_excel(file_name)
    elif file_extension == 'csv':
        return extract_text_from_csv(file_name)
    elif file_extension == 'txt':
        return extract_text_from_text(file_name)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_name)
    elif file_extension == 'pdf':
        return extract_text_from_pdf(file_name)
    else:
        print('Unknown File Type')

#--------------------------------------functions to update starts here--------------------------#         
 
def extract_text_from_excel_update(file_path):

    excel_file = pd.ExcelFile(file_path)


    all_split_dataframes = []
    split_dataframes = []

    for sheet_name in excel_file.sheet_names:

        df = excel_file.parse(sheet_name)


        rows_per_split = 15
        if len(df)<rows_per_split:
            split_dataframes.append(df)
        else:    
            num_splits = len(df) // rows_per_split
            

            for i in range(num_splits):
                start_row = i * rows_per_split
                end_row = (i + 1) * rows_per_split
                split_df = df.iloc[start_row:end_row, :]
                split_dataframes.append(split_df)

            if len(df) % rows_per_split != 0:
                remaining_rows = df.iloc[end_row:, :]
                split_dataframes[-1] = pd.concat([split_dataframes[-1], remaining_rows], axis=0)


        all_split_dataframes.extend(split_dataframes)
    text_list=[]
    for idx, split_df in enumerate(all_split_dataframes):
         print(f"Split DataFrame {idx + 1}:")
         print(split_df)
         text_xlx='my_xlx'+split_df.to_csv(index=False)
         text_list.append(text_xlx)
    return text_list


def extract_text_from_docx_update(file_path):
    text=''
    text = docx2txt.process(file_path)
    chunks=get_overlapped_chunks(text, 1000, 300)
    return chunks

def extract_text_from_csv_update(file_path):
    text = pd.read_csv(file_path)
    df = pd.DataFrame(text)
    split_dataframes = []
    rows_per_split = 15
    if len(df)<rows_per_split:
        split_dataframes.append(df)
    else:    
        num_splits = len(df) // rows_per_split


        for i in range(num_splits):
            start_row = i * rows_per_split
            end_row = (i + 1) * rows_per_split
            split_df = df.iloc[start_row:end_row, :]
            split_dataframes.append(split_df)


        if len(df) % rows_per_split != 0:
            remaining_rows = df.iloc[end_row:, :]
            split_dataframes[-1] = pd.concat([split_dataframes[-1], remaining_rows], axis=0)


    text_list=[]
    for idx, split_df in enumerate(split_dataframes):
        print(f"Split DataFrame {idx + 1}:")
        print(split_df)
        text_csv='my_csv'+split_df.to_csv(index=False)
        text_list.append(text_csv)
        print()
    return text_list

def extract_text_from_pdf_update(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    chunks=get_overlapped_chunks(text, 1000, 300)
    return chunks

def extract_text_from_text_update(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        chunks=get_overlapped_chunks(text, 1000, 300)
        return chunks
    except Exception as e:
        return str(e)


def to_text_update(file_name,name):
    file_extension = name.split('.')[-1].lower()
    if file_extension == 'xlsx':
        return extract_text_from_excel_update(file_name)
    elif file_extension == 'csv':
        return extract_text_from_csv_update(file_name)
    elif file_extension == 'txt':
        return extract_text_from_text_update(file_name)
    elif file_extension == 'docx':
        return extract_text_from_docx_update(file_name)
    elif file_extension == 'pdf':
        return extract_text_from_pdf_update(file_name)
    else:
        print('Unknown File Type')    

def process_text(text,collection):
    if text.strip():
        results = collection.query(
        query_texts=[text],
        n_results=3
)
    return results

def make_prompt(instruction, context, question_text):
   return (f"""{instruction}\n"""
          + f"Information :\n{context}\n"
          + f"{question_text}?\n")

def generate_answer_update(alice,instruction,relevant,text,example):
    print('entered')
    context = '\n'.join(relevant)
    pre_prompt_text = make_prompt(instruction,context, text)
    prompt_text=f"{pre_prompt_text}\n{example}"
    lines=prompt_text
    print(lines)
    alice_response = alice.generate([lines])   
    alice_gen = alice_response[0].generated_text
    print(f"Watson : \n{alice_gen}")
    return alice_gen

def web_to_text(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    page_title = soup.title.text
    page_body=soup.body.text
    output_text = re.sub(r'\n+', '\n', page_body)
    chunks_output=get_overlapped_chunks(output_text, 1000, 300)
    chunk=[]
    for item in chunks_output:
        modified_item = f"{page_title}. {item}"
        chunk.append(modified_item)
    return chunk   



 #--------------------Views start here--------------------------#        
 # 
def user_login(request):
    # Implement login logic here
    pass

def user_logout(request):
    logout(request)
    return redirect('home')   

def home(request):     
    if request.method == 'POST':
        query = request.POST.get('query_input')      
        alice=generateparams('sample',1000,0.6,'meta-llama/llama-2-70b-chat',creds)
        answer=generate_answer(alice,f"{query}?")
        return render(request,'home.html',{"query":query,"answer":answer})
    else:
        query = ''
        answer = ''   
        return render(request,'home.html',{})

def classification(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        # selected_option=request.POST.get('exampleRadios')
        # file_path_custom=request.POST.get('customField')
        # custompercent=request.POST.get('custompercent')
        search_params=request.POST.get('custom_path')
        split_string = search_params.rsplit(',', 1)
        result = f"Check whether the given information contains data related to {split_string[0]} or {split_string[1]}. If the information contains data related to {split_string[0]} or {split_string[1]} return output as yes else return output as no"
        chunks=to_text(myfile,myfile.name)
        percentage=int(count_occurence(chunks,result))
        print(percentage)
        context={
            'file_name': myfile.name,
            'file_size':myfile.size,
            'percent':percentage,
                 }
        return render(request, 'classification.html', context)

    return render(request, 'classification.html',{}) 

def doc_qna(request):
    data=client.list_collections()
    names=[obj.name for obj in data]
    answer=''
    ans_type=''
    section_1=''
    section_2=''
    section_3=''
    if request.method == 'POST':
        my_model_data = params.objects.last()
        if 'param' in request.POST:   
            params.objects.all().delete() 
            selected_collection_try= request.POST.get('selected_collection')
            ans_type=request.POST.get('selected_model')
            ins_type=request.POST.get('exampleRadios1')
            #-----------instruction selection-------------------#
            if ins_type=="Default":
                instructions='''You are a helpful, respectful and honest assistant.
Please provide answer only from the given information.
Do not generate additional content.'''

            elif ins_type=="Custom": 
                instructions=request.POST.get('customField')
            #--------------model selection-----------------#   
            my_model_instance = params(
            collection_name=selected_collection_try,
            ans_type=ans_type,
            inst_type=ins_type,
            inst=instructions
            )
            my_model_instance.save()
        if 'query' in request.POST:    
            selected_collection = my_model_data.collection_name
            query=request.POST.get('query_input')
            if selected_collection:
                instructions=my_model_data.inst
                if my_model_data.ans_type=='meta-llama/llama-2-70b-chat':
                    alice=generateparams('greedy',1000,0.6,'meta-llama/llama-2-70b-chat',creds)
                elif my_model_data.ans_type=='google/flan-ul2':
                    alice=generateparams('sample',100,0.6,'google/flan-ul2',creds)   
                elif my_model_data.ans_type=='google/flan-t5-xxl':
                    alice=generateparams('sample',100,0.6,'google/flan-t5-xxl',creds)     
                collection=client.get_collection(selected_collection)
                result=process_text(query,collection)
                print(result)
                relevant_texts=result["documents"][0]
                section_1=relevant_texts[0]
                if section_1.startswith('my_csv'):
                    section_1 = section_1[6:]
                    csv_file_1 = StringIO(section_1)
                    section_1 = pd.read_csv(csv_file_1)
                section_2=relevant_texts[1]
                if section_2.startswith('my_csv'):
                    section_2 = section_2[6:]
                    csv_file_2 = StringIO(section_2)
                    section_2 = pd.read_csv(csv_file_2)
                section_3=relevant_texts[2]
                if section_3.startswith('my_csv'):
                    section_3 = section_3[6:]
                    csv_file_3 = StringIO(section_3)
                    section_3 = pd.read_csv(csv_file_3)
                print(section_1)    
                example='Answer: '
                answer=generate_answer_update(alice,instructions,relevant_texts,query,example)
            else:
                answer='No data available. Plese make sure you have selected the collection'    
            if answer.strip()=='' or answer==None:
                answer='I dont have answer for the question. Please tune you query further.'     
    my_model_data = params.objects.last()               
    return render(request, 'doc_qna.html',{"col_list":names,'result':answer,'my_model_data': my_model_data,'section_1':section_1,'section_2':section_2,'section_3':section_3})

def update_knowledge(request):
    # client.reset()
    if request.method == 'POST':
        upload_type=request.POST.get('exampleRadios1')
        data_url=request.POST.get('url_input')
        collection_name=request.POST.get('col_name')
        title=request.POST.get('title')
        source=request.POST.get('source')
        print(collection_name)
        print(source)
        print(title)
        if upload_type=='file':
            myfile = request.FILES['myfile']
            chunks=to_text_update(myfile,myfile.name)
        elif upload_type=='website':
            chunks=web_to_text(data_url)
        update_from_doc(collection_name,chunks,source,title)

    data=client.list_collections()
    names=[obj.name for obj in data]
    print(names)
 
        
    return render(request, 'update_knowledge.html',{"col_list":names}) 

def summary(request):  
    sum_answer='' 
    data=client.list_collections()
    names=[obj.name for obj in data]
    if request.method == 'POST':  
        if 'param' in request.POST:   
            summ.objects.all().delete() 
            selected_collection_try= request.POST.get('selected_collection')
            model_name=request.POST.get('selected_model')
            ins_type=request.POST.get('exampleRadios1')
            if model_name=='llama-70b':
                selected_model='meta-llama/llama-2-70b-chat'
            elif model_name=='flan-ul2':
                selected_model='google/flan-ul2'    
            elif model_name=='flan-t5-xxl':
                selected_model='google/flan-t5-xxl'    
            #-----------instruction selection-------------------#
            if ins_type=="Default":
                instructions='''You are a helpful, respectful and honest assistant.
Please provide answer only from the given information.
Do not generate additional content.'''
            else:
                instructions=request.POST.get('customField')    
            #--------------model selection-----------------#   
            my_model_instance = summ(
            collection_name=selected_collection_try,
            model_name=selected_model,
            inst_type=ins_type,
            inst=instructions
            )
            my_model_instance.save()
        if 'summ' in request.POST:
            print("inside summ")
            answers_list=[]   
            answer_list_file=[] 
            text_inputs=[]
            my_model_data = summ.objects.last() 
            collection_id=my_model_data.collection_name
            collection=client.get_collection(collection_id)
            instructions=my_model_data.inst
            input_select=request.POST.get('input_method')
            if input_select=='enter':
                text_inputs = request.POST.getlist('text_input')
            elif input_select=='file':     
                myfile = request.FILES['myfile1']
                df = pd.read_excel(myfile)
                column_name = "Question"
                column_data = df[column_name]
                text_inputs = column_data.tolist()
                print(text_inputs)
            model_id=my_model_data.model_name
            alice=generateparams('sample',1000,0.6,model_id,creds)
            print(text_inputs)
            example='Answer: '
            for text_input in text_inputs:
                result=process_text(text_input,collection)
                relevant_texts=result["documents"][0]
                answer=generate_answer_update(alice,instructions,relevant_texts,text_input,example)
                answers_list.append(f"{text_input}?  {answer}") 
                answer_list_file.append(answer)
            global QA_data
            QA_data={'Question': text_inputs, 'Answer': answer_list_file}  
            df=pd.DataFrame(QA_data)           
            combine_answers = "\n".join(answers_list)
            sum_inst=f"""Read the question and answers given below. provide a detailed summary by combining the question and answers.\n{combine_answers}\nSummary: """
            alice_sum=generateparams('sample',1000,0.6,'meta-llama/llama-2-70b-chat',creds)
            sum_answer=generate_answer(alice_sum,sum_inst)
    my_model_data = summ.objects.last()  
    return render(request, 'summary.html',{"col_list":names,'my_model_data': my_model_data,"answer":sum_answer}) 

def download_excel(request):
            data = QA_data
            df = pd.DataFrame(data)
            response = HttpResponse(content_type='application/xlsx')
            response['Content-Disposition'] = f'attachment; filename="Q_and_A.xlsx"'
            with pd.ExcelWriter(response) as writer:
                df.to_excel(writer, sheet_name='sheet1')
            return response