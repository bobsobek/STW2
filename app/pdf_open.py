from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LAParams
import os
import search_engine
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
# prompt_breakdown
# get_weightage
from pymongo import MongoClient
from pymongo.server_api import ServerApi

nlp = spacy.load("en_core_web_sm")

def extract_pdf(): # gets all the text from pdf files
  pdf_and_text = {}

  folder_path = 'data/bio' # the bio part can be changed to any other folder

  files = os.listdir(folder_path)
  for file_name in files:
    print(file_name)
    # Check if the item is a file (not a subdirectory)
    pdf_file = os.path.join(folder_path, file_name)
    if os.path.isfile(pdf_file):
        # Open and read each file      
      with open(pdf_file, 'rb') as file:
        text = extract_text(file)
    pdf_and_text[file_name] = text
  return pdf_and_text

def extract_pdf_with_pages(): # returns dictionary {pdf_name:{page_no:text}}
  pdf_with_pages = {}
  folder_path = 'data/bio' # the bio part can be changed to any other folder

  files = os.listdir(folder_path)
  for file_name in files:
    # Check if the item is a file (not a subdirectory)
    pdf_file = os.path.join(folder_path, file_name)
    if os.path.isfile(pdf_file):
        # Open and read each file      
      with open(pdf_file, 'rb') as file:
        pdf_page = {} # {page_number: text}
        text = extract_text(file)
        pages = text.split('\x0c')
        for page_num, page_text in enumerate(pages, start=1):
          pdf_page[str(page_num)] = page_text

    pdf_with_pages[file_name] = pdf_page
  return pdf_with_pages

def get_TF_IDF(documents): # documents is a dictionary(pdf_file: text)
  # Create TF-IDF vectorizer
  vectorizer = TfidfVectorizer()
  texts = list(documents.values())
  file_names = list(documents.keys())
  # gets the nouns and verbs from each document, and puts it back into a string
  tokenized_documents = [search_engine.prompt_breakdown(nlp(text)) for text in texts]
  # Convert tokenized documents back to string format
  preprocessed_documents = [' '.join(tokens) for tokens in tokenized_documents]
  # Compute TF-IDF scores
  tfidf_matrix = vectorizer.fit_transform(preprocessed_documents)

  doc_dict = {}  # dictionary (pdf_name:TFIDF)
  terms = vectorizer.get_feature_names_out()
  for i, doc in enumerate(documents):
    print("Document:", file_names[i])
    tfidf = {}
    for j, term in enumerate(terms):
        tfidf_score = tfidf_matrix[i, j]
        if tfidf_score > 0:  # Print only non-zero TF-IDF scores
            print("  {}: {:.4f}".format(term, tfidf_score))
            tfidf[term] = tfidf_score
    doc_dict[file_names[i]] = tfidf
  return doc_dict

def syllabus_load_into_mongodb():
  uri = "mongodb+srv://bob_the_crim:mTVTirHHRobvHPoe@bio.kzrxpbq.mongodb.net/?retryWrites=true&w=majority&appName=Bio"
  client = MongoClient(uri, server_api=ServerApi('1'))
  try:
    # Ping the server to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")

    # Specify database and collection
    db = client["bio_notes"]
    collection = db["syllabus"]

    # Extract PDFs and compute TF-IDF
    pdf_and_text = extract_pdf()
    doc_dict = get_TF_IDF(pdf_and_text)

    # Insert documents into MongoDB collection
    collection.insert_one(doc_dict)

    print("Documents inserted into MongoDB successfully!")
  except Exception as e:
    print("An error occurred:", e)

def indiv_load_into_mongodb():
  uri = "mongodb+srv://bob_the_crim:mTVTirHHRobvHPoe@bio.kzrxpbq.mongodb.net/?retryWrites=true&w=majority&appName=Bio"
  client = MongoClient(uri, server_api=ServerApi('1'))
  try:
    # Ping the server to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")

    # Specify database and collection
    db = client["bio_notes"]
    # Extract PDFs and compute TF-IDF
    pdf_and_text = extract_pdf_with_pages()
    for file_name, pdf_pages in pdf_and_text.items():
      doc_dict = get_TF_IDF(pdf_pages)
      collection = db[file_name]
      print(doc_dict)
      collection.insert_one(doc_dict)


    print("Documents inserted into MongoDB successfully!")
  except Exception as e:
    print("An error occurred:", e)
