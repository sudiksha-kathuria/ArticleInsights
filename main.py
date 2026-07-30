from fastapi import FastAPI, Query
import requests
import json
import csv
from collections import defaultdict

def load_data():
    for i in range(2000):
        source=requests.get(url[i])
        a=source.json()
        data=json.loads(a)
        return data

def load_needed_data():
    data= load_data()
    selected_data=[]
    for i in data:
        selected={'Title': i['title'], 'Text': i['text'], 'Synopsis': i['synopsis'], 'Insert Date': i['insertdate'], 'Author': i['authors'], 'Keywords': i['keywords']}
        selected_data.append(selected)
    return selected_data
    #with open('file.csv','w') as f:
    #    writer=csv.DictWriter(f,fieldnames=['Title', 'Text', 'Synopsis', 'Insert Date','Author','Keywords'])
    #    writer.writeheader()
    #    for i in selected_data:
    #        writer.writerows(selected_data)

app=FastAPI()

@app.get('/')
def home():
    return{'message':'Home Page'}

@app.get('/view')
def view():
    data=load_data()
    return data

@app.get('/articles-by-each-author')
def articles():
    count= defaultdict(int)
