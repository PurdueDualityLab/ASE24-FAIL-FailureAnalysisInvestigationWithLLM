import os
import re
from collections import Counter
import matplotlib.pyplot as plt

def extract_sources_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        content = file.read().split('----------------------------------------------------------------------')[0]

    # Use the provided regex to extract articles from the content
    sources = re.findall(r'\(([^()]+)\)', content)
    filtered_sources = []
    for s in sources:
        s = s.lower()
        # filter the sources that are not relevant
        if s == 'comp.risks' or any(char.isdigit() for char in s):
            continue
        for char in s:
            # format the source properly
            if char == '\n':
                s = s.replace(char, '')

        filtered_sources.append(s)
    
    return filtered_sources

def count_sources(directory_path):
    sources_counter = Counter()

    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            sources = extract_sources_from_file(file_path)
            sources_counter.update(sources)

    return sources_counter


def plot_results(sources_counter):
    sources = list(sources_counter.keys())
    counts = list(sources_counter.values())

    # Plot the bar chart
    plt.figure()
    plt.bar(sources, counts, color='skyblue')
    plt.xlabel('Source')
    plt.ylabel('Occurences')
    plt.title('Occurences of Sources in RISKS Digest Articles')
    plt.xticks(rotation=90)
    # plt.tight_layout()
    plt.show()

directory_path = '../../risk_articles'
sources_counter = count_sources(directory_path)
plot_results(sources_counter)

# Write the sorted results to a file
with open('risks_sources.txt', 'w', encoding='utf-8') as output_file:
    for article, count in sorted(sources_counter.items(), key=lambda x: x[1], reverse=True):
        output_file.write(f'{count} occurrences - {article}\n')

