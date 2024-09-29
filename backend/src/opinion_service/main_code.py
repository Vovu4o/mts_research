import yake
from pymystem3 import Mystem
from tqdm import tqdm
from joblib import Parallel, delayed
from sklearn.cluster import KMeans
import numpy as np
import csv
import json
from navec import Navec



path = 'navec_hudlit_v1_12B_500K_300d_100q.tar'
navec = Navec.load(path)


def read_sentences_from_csv(filename):
  sentences = []
  with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
      sentences.append(row[0])
  return sentences

filename = 'sentences.csv'
newlst = read_sentences_from_csv(filename)

extractor = yake.KeywordExtractor (
    lan = "ru",    
    n = 1,          
    dedupLim = 0.3, 
    top = 1       
)

for i in range(len(newlst)):
  newlst[i] = newlst[i].lower()
ans = []
for i in range(len(newlst)):
  ans.append(extractor.extract_keywords(newlst[i])[0][0])

batch_size = 1000

text_batch = [ans[i: i + batch_size] for i in range(0, len(ans), batch_size)]

def lemmatize(text):
    m = Mystem()
    merged_text = "|".join(text)
    doc = []
    res = []
    for t in m.lemmatize(merged_text):
        if t != '|':
            doc.append(t)
        else:
            res.append(doc)
            doc = []
    return res

processed_texts = Parallel(n_jobs=-1)(delayed(lemmatize)(t) for t in tqdm(text_batch))[0]
ans = [processed_texts[i] for i in range(len(processed_texts))]
lst_for_check_len = [word for sublist in ans for word in sublist]
n_clusters = len(set(lst_for_check_len))
if n_clusters>10:
  n_clusters = 10

def cluster_words_with_vectors(words,n):
    vectors = [navec[word[0]] for word in words if word[0] in navec]
    kmeans = KMeans(n_clusters=n, random_state=0)
    clusters = kmeans.fit_predict(vectors)
    clustered_words = {}
    for i, cluster_id in enumerate(clusters):
        if cluster_id not in clustered_words:
            clustered_words[cluster_id] = []
        clustered_words[cluster_id].append(words[i])
    return clustered_words

clusters = cluster_words_with_vectors(ans,n_clusters)

def cluster_dict_to_compact_dict(cluster_dict):
  compact_dict = {}
  for cluster_id in range(10):
    cluster = cluster_dict[cluster_id]
    all_words = [word for sublist in cluster for word in sublist]
    uniq = []
    sorted_words = sorted(all_words, key=all_words.count, reverse=True)
    for i in range(len(sorted_words)):
      if not(sorted_words[i] in uniq) and len(uniq)<3:
        uniq.append(sorted_words[i])
      if len(uniq)==3:
        break
    key = '/'.join(uniq[:3])
    if len(key.split('/')) < 3:
      key = '/'.join(uniq[:2])
    if len(key.split('/')) < 2:
      key = uniq[0]
    compact_dict[key] = len(all_words)
  return compact_dict

ans = cluster_dict_to_compact_dict(clusters)
with open("QuEZ.json", 'w', encoding='utf-8') as f:
    json.dump(ans, f, ensure_ascii=False, indent=4)
