import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
import json

def get_filing_metadata(cik):
    headers = {'User-Agent': "your-email@example.com"}
    response = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching metadata for CIK {cik}: {response.status_code}")
        return None

def get_10k_urls(filing_metadata):
    urls = []
    try:
        recent_filings = filing_metadata['filings']['recent']
        for idx in range(len(recent_filings['form'])):
            if recent_filings['form'][idx] == '10-K':
                filing_date = recent_filings['filingDate'][idx]
                filing_year = int(filing_date[:4])
                if 2001 <= filing_year <= 2023:
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{filing_metadata['cik']}/{recent_filings['accessionNumber'][idx].replace('-', '')}/{recent_filings['primaryDocument'][idx]}"
                    urls.append((filing_url, filing_year))
    except KeyError as e:
        print(f"KeyError: {e}")
    return urls

def download_10k_document(filing_url):
    headers = {'User-Agent': "your-email@example.com"}
    response = requests.get(filing_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    else:
        print(f"Error downloading document {filing_url}: {response.status_code}")
        return ""

def search_words_in_10k(document_text, search_words):
    occurrences = {}
    for word in search_words:
        matches = re.findall(word, document_text, re.IGNORECASE)
        occurrences[word] = len(matches)
    return occurrences
st.title("SEC 10-K Filings Word Count")

cik = st.text_input("Enter Company CIK")
search_words = st.text_area("Enter search words (comma-separated)").split(',')

if st.button("Search"):
    if not cik or not search_words:
        st.error("CIK and search words are required")
    else:
        st.write("Fetching data... This may take a few moments.")
        filing_metadata = get_filing_metadata(cik)
        if not filing_metadata:
            st.error("Error fetching filing metadata")
        else:
            filing_urls = get_10k_urls(filing_metadata)
            results = []
            for filing_url, year in filing_urls:
                document_text = download_10k_document(filing_url)
                if not document_text:
                    continue
                word_occurrences = search_words_in_10k(document_text, search_words)
                result = {
                    "cik": cik,
                    "year": year,
                    "word_counts": word_occurrences
                }
                results.append(result)
            
            st.write("Results:")
            st.json(results)
            with open('10k_word_occurrences.json', 'w') as f:
                json.dump(results, f)
            st.success("Results saved to 10k_word_occurrences.json")
