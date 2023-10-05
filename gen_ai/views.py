from django.http import HttpResponse
from django.template import loader
from genai.credentials import Credentials
from genai.model import Model
from genai.schemas import GenerateParams
from django.shortcuts import render
import pdfplumber
import pandas as pd
import docx2txt
import os
import chromadb
import uuid
from .models import params

current_directory = os.getcwd()
client = chromadb.PersistentClient(path=f"{current_directory}/collection")
# def create_new_collection(collection_name):
#     collection = client.create_collection(name=collection_name)
#     return collection
def generate_unique_id():
    return str(uuid.uuid4())    

def update_from_doc(collection_name,data,input_source,input_title):
    client = chromadb.PersistentClient(path=f"{current_directory}/collection")
    collection = client.create_collection(name=collection_name)
    for i in data:
        print(i)
        collection.add(
        ids=generate_unique_id(),
        documents=[i],
        metadatas=[{"source":input_source,"title":input_title}],)   

creds = Credentials("pak-4D7V0iz9n86tsi2BH48ezpshf0mmxTnnPnvHl2dJatw", api_endpoint="https://bam-api.res.ibm.com/v1")

binary_params = GenerateParams(decoding_method="greedy", max_new_tokens=3, temperature=0.1)
binary = Model("google/flan-ul2", params=binary_params, credentials=creds)

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


    for sheet_name in excel_file.sheet_names:

        df = excel_file.parse(sheet_name)

        rows_per_split = 15
        num_splits = len(df) // rows_per_split
        split_dataframes = []

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
    rows_per_split = 15
    num_splits = len(df) // rows_per_split
    split_dataframes = []

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

    for sheet_name in excel_file.sheet_names:

        df = excel_file.parse(sheet_name)


        rows_per_split = 15
        num_splits = len(df) // rows_per_split
        split_dataframes = []

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
         print()
    return text_list


def extract_text_from_docx_update(file_path):
    text=''
    text = docx2txt.process(file_path)
    chunks=get_overlapped_chunks(text, 1000, 300)
    return chunks

def extract_text_from_csv_update(file_path):
    text = pd.read_csv(file_path)
    df = pd.DataFrame(text)
    rows_per_split = 15
    num_splits = len(df) // rows_per_split
    split_dataframes = []

    for i in range(num_splits):
        start_row = i * rows_per_split
        end_row = (i + 1) * rows_per_split
        split_df = df.iloc[start_row:end_row, :]
        split_dataframes.append(split_df)

# If there are any remaining rows, add them to the last split
    if len(df) % rows_per_split != 0:
        remaining_rows = df.iloc[end_row:, :]
        split_dataframes[-1] = pd.concat([split_dataframes[-1], remaining_rows], axis=0)

# Access the split DataFrames
    text_list=[]
    for idx, split_df in enumerate(split_dataframes):
#         print(f"Split DataFrame {idx + 1}:")
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

def process_text(query,collection):
    if query.strip():
        results = collection.query(
        query_texts=[query],
        n_results=3
)
    return results

def make_prompt(instruction, context, question_text):
   return (f"""{instruction}\n"""
          + f"Information :\n{context}\n"
          + f"{question_text}?\n")

def generate_answer_update(alice,instruction,relevant,text):
    print('entered')
    context = '\n'.join(relevant)
    prompt_text = make_prompt(instruction,context, text)
    lines=prompt_text
    print(lines)
    alice_response = alice.generate([lines])   
    alice_gen = alice_response[0].generated_text
    print(f"Watson : \n{alice_gen}")
    return alice_gen


 #--------------------Views start here--------------------------#           

def home(request):
    if request.method == 'POST':
        query = request.POST.get('query_input')      
        creds = Credentials("pak-4D7V0iz9n86tsi2BH48ezpshf0mmxTnnPnvHl2dJatw", api_endpoint="https://bam-api.res.ibm.com/v1")
        alice=generateparams('sample',1000,0.6,'meta-llama/llama-2-70b-chat',creds)
        answer=generate_answer(alice,f"{query}?")
    else:
        query = ''
        answer = ''   
    return render(request,'home.html',{"query":query,"answer":answer})

def classification(request):

    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        selected_option=request.POST.get('exampleRadios')
        file_path_custom=request.POST.get('customField')
        custompercent=request.POST.get('custompercent')
        search_params=request.POST.get('custom_path')
        chunks=to_text(myfile,myfile.name)
        percentage=int(count_occurence(chunks,search_params))
        print(percentage)
        context={
            'file_name': myfile.name,
            'file_size':myfile.size,
            'percent':percentage,
                 }
        return render(request, 'classification.html', context)

    return render(request, 'classification.html',{}) 

def doc_qna(request):
    my_model_data = params.objects.first()
    data=client.list_collections()
    names=[obj.name for obj in data]
    answer=''
    ans_type=''
    if request.method == 'POST':
        if 'param' in request.POST:   
            params.objects.all().delete() 
            selected_collection_try= request.POST.get('selected_collection')
            ans_type=request.POST.get('exampleRadios')
            ins_type=request.POST.get('exampleRadios1')
            instruction=request.POST.get('customField')
            my_model_instance = params(
            collection_name=selected_collection_try,
            ans_type=ans_type,
            inst_type=ins_type,
            inst=instruction
            )
            my_model_instance.save()
        if 'query' in request.POST:    
            selected_collection = request.POST.get('selected_collection')
            print(f"this is {selected_collection}")
            query=request.POST.get('query_input')
            creds = Credentials("pak-4D7V0iz9n86tsi2BH48ezpshf0mmxTnnPnvHl2dJatw", api_endpoint="https://bam-api.res.ibm.com/v1")
            alice=generateparams('sample',1000,0.6,'meta-llama/llama-2-70b-chat',creds)
            instructions='''You are a helpful, respectful and honest assistant. Please provide correct answer only from the information provided. Do not make  up any answers.'''
            if selected_collection:
                collection=client.get_collection(selected_collection)
                result=process_text(query,collection)
                relevant_texts=result["documents"][0]
                answer=generate_answer_update(alice,instructions,relevant_texts,query)
            else:
                answer='No data available. Plese make sure you have selected the collection'    
    return render(request, 'doc_qna.html',{"col_list":names,'result':answer,'my_model_data': my_model_data})

def update_knowledge(request):
    if request.method == 'POST':
        myfile = request.FILES['myfile']
        collection_name=request.POST.get('col_name')
        title=request.POST.get('title')
        source=request.POST.get('source')
        print(myfile.name)
        print(collection_name)
        print(source)
        print(title)
        chunks=to_text_update(myfile,myfile.name)
        update_from_doc(collection_name,chunks,source,title)

    data=client.list_collections()
    names=[obj.name for obj in data]
    print(names)
 
        
    return render(request, 'update_knowledge.html',{"col_list":names}) 