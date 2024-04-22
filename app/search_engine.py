import spacy
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
# Load English tokenizer, tagger, parser and NER

def prompt_breakdown(doc): # tokenises each word in the prompt and returns a list of noun and verbs
  nlp = spacy.load("en_core_web_sm")
  doc = nlp(doc)
  return [str(token.lemma_) for token in doc if token.pos_ in {"NOUN", "VERB"}]

def get_pdfs():
  uri = "mongodb+srv://bob_the_crim:mTVTirHHRobvHPoe@bio.kzrxpbq.mongodb.net/?retryWrites=true&w=majority&appName=Bio"
  client = MongoClient(uri, server_api=ServerApi('1'))
  try:
    # Ping the server to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")

    # Specify database and collection
    db = client["bio_notes"]
    collection = db["syllabus"]
    pdfs = collection.find_one()
    pdfs.pop('_id')
    return pdfs
  except Exception as e:
    print("An error occurred:", e)

def find_useful_pdfs(prompt):
  pdfs = get_pdfs()
  prompt_tokens = prompt_breakdown(prompt)
  pdf_weight = {}
  for pdf_name, weights in pdfs.items():
    pdf_weight[pdf_name] = 0
    for term in prompt_tokens:
      if term in weights:
        pdf_weight[pdf_name] += weights[term]

  pdf_sorted = dict(sorted(pdf_weight.items(), key=lambda item: item[1], reverse=True))
  useful_pdf = []
  for i in range(5):
    useful_pdf.append(list(pdf_sorted.keys())[i])
  return useful_pdf,prompt_tokens

def search_engine(prompt):
  useful_pdfs,prompt_tokens  = find_useful_pdfs(prompt)
  uri = "mongodb+srv://bob_the_crim:mTVTirHHRobvHPoe@bio.kzrxpbq.mongodb.net/?retryWrites=true&w=majority&appName=Bio"
  client = MongoClient(uri, server_api=ServerApi('1'))
  pdf_weights = {}
  for i in useful_pdfs:
    pdf_weights[i] = {}
    db = client["bio_notes"]
    collection = db[i]
    docs = collection.find_one()
    docs.pop('_id')
    page_weights = {}
    for page_num, tokens in docs.items():
      page_weights[page_num] = 0
      for prompt_token in prompt_tokens:
        if prompt_token in tokens:
          page_weights[page_num] += tokens[prompt_token]
    pdf_page_sorted = dict(sorted(page_weights.items(), key=lambda item: item[1], reverse=True))
    pdf_weights[i] = pdf_page_sorted
  returned_pdf = {}
  for pdf,page_weights in pdf_weights.items():
    returned_pdf[pdf] = [key for key in page_weights.keys()]

  return returned_pdf


if __name__ == "__main__":
  print("This code will only run if testing.py is executed directly.")
