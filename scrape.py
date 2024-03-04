import requests
from bs4 import BeautifulSoup
import re
import csv
import time

def get_title_content(instance):
    title_div = instance.find('div', class_='list-title mathjax')
    title_string = title_div.get_text()

    # Use re.search to find the pattern in the string
    match = re.search(pattern_title, title_string)
    # Check if a match is found and extract the title content
    if match:
        return match.group(1).strip()
    return None

def get_author_names(instance):
    authors_div = instance.find('div', class_='list-authors')
    return [author.get_text() for author in authors_div.find_all('a')]

def get_subjects(instance):
    subjects_div = instance.find('div', class_='list-subjects')
    subjects_text = subjects_div.get_text()
    match = re.search(pattern_subjects, subjects_text)
    if match:
        subjects_content = match.group(1).strip()
        subjects_list = [subject.strip() for subject in subjects_content.split(';')]
        return subjects_list
    return None

def get_abstraact_link(instance):
    abstract_link=instance.select_one('span.list-identifier a[title="Abstract"]')
    return "https://arxiv.org/"+abstract_link.get('href')

def get_abstract_content(abstract_link, timeout=10):
    try:
        r_abstract = requests.get(abstract_link, timeout=timeout)
        r_abstract.raise_for_status()  # Raise HTTPError for bad requests
        soup_abstract = BeautifulSoup(r_abstract.text, 'html.parser')
        abs_content = soup_abstract.body.find('div', class_="flex-wrap-footer")
        sub_content = abs_content.main.find('div', id="content")
        abs_div = sub_content.find('div', id="abs-outer").find('div', class_='leftcolumn').find('div',
                                                                                                id='content-inner').find(
            'div', id='abs')
        abstract_text = abs_div.find('blockquote').get_text()
        start_index = abstract_text.find('\nAbstract:') + len('\nAbstract:')
        return abstract_text[start_index:].strip()
    except requests.exceptions.Timeout:
        print(f"Timeout occurred for {abstract_link}. Skipping.")
        return ""

# Define a regular expression pattern to capture the title content
pattern_title = r'Title:(.*?)\n'
pattern_subjects = r'Subjects:(.*?)\n'

# Create and open a CSV file for writing
csv_file_path = 'output.csv'
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
    # Create a CSV writer object
    csv_writer = csv.writer(csv_file)

    # Write header row
    csv_writer.writerow(['Title', 'Author Names', 'Subjects', 'Abstract'])

    r = requests.get("https://arxiv.org/list/cs/pastweek?skip=0&show=100")
    # https://arxiv.org/list/cs/pastweek?skip=0&show=100
    soup = BeautifulSoup(r.text, 'html.parser')
    content = soup.find('div', id='content')
    dlpage = content.find('div', id='dlpage')
    dt_contents = dlpage.select('dl dt')  # scrape the abstract
    dd_contents = dlpage.select('dl dd')

    for i in range(len(dd_contents)):
        instance = dd_contents[i]
        abs_content = dt_contents[i]
        title_content = get_title_content(instance)
        author_names = get_author_names(instance)
        subjects = get_subjects(instance)
        
        # Get abstract link
        abs_link = get_abstraact_link(abs_content)
        
        # Get abstract content
        abstract_content = get_abstract_content(abs_link)

        csv_writer.writerow([title_content, ', '.join(author_names), ', '.join(subjects), abstract_content])

print(f'Titles, author names, subjects, and abstracts have been saved to {csv_file_path}')
csv_file.close()
