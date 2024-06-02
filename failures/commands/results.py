import argparse
import logging
import textwrap

import csv
import pandas as pd
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from collections import Counter
import itertools
from urllib.parse import urlparse

from failures.articles.models import Article, Incident

from failures.commands.PROMPTS import TAXONOMY_QUESTIONS, CPS_KEYS


class ResultsCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Report results for paper from the database.
            """
        
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nReporting Results.")

        start_year = 2010
        end_year = 2022

        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)

        incidents = Incident.objects.filter(published__range=(start_date, end_date))
        num_incidents = len(incidents)

        '''

        # Get the list of distinct years
        years = list(range(start_year,end_year+1)) #list(Article.objects.values_list('published__year', flat=True).distinct())

        stats = {}
        for year in years:
            count_all = Article.objects.filter(published__year=year).count()
            count_scrape_successful = Article.objects.filter(scrape_successful=True, published__year=year).count()
            count_describes_failure = Article.objects.filter(describes_failure=True, published__year=year).count()
            count_analyzable_failure = Article.objects.filter(analyzable_failure=True, published__year=year).count()
            count_incidents = Incident.objects.filter(published__year=year).count()

            stats[year] = {
                'All': count_all,
                'Scrape Successful': count_scrape_successful,
                'Describes Failure': count_describes_failure,
                'Analyzable Failure': count_analyzable_failure,
                'Incidents': count_incidents
            }

        # Prepare data for the Sankey diagram
        labels = []
        source = []
        target = []
        value = []

        label_to_index = {}
        index = 0

        # Create labels for years and stats categories
        for year in years:
            labels.append(f"Year {year}")
            label_to_index[f"Year {year}"] = index
            index += 1

        for category in ['All', 'Scrape Successful', 'Describes Failure', 'Analyzable Failure', 'Incidents']:
            labels.append(category)
            label_to_index[category] = index
            index += 1

        # Create source, target, and value lists for Sankey
        for year in years:
            if year in stats:
                for category, count in stats[year].items():
                    source.append(label_to_index[f"Year {year}"])
                    target.append(label_to_index[category])
                    value.append(count)

        # Create the Sankey plot
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            ))])

        # Update layout and save the figure
        fig.write_image("results/IncidentsOverYears.png")
        '''

        '''
        # Convert the stats dictionary to a DataFrame
        df = pd.DataFrame.from_dict(stats, orient='index').sort_index()

        logging.info(df)

        # Plotting the stacked bar chart
        ax = df.plot(kind='bar', stacked=True, figsize=(14, 8))

        # Adding labels and title
        ax.set_xlabel('Year')
        ax.set_ylabel('Count')
        ax.set_title('Incident Statistics Over the Years')
        ax.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Save the plot as a PNG file
        plt.tight_layout()
        plt.savefig('results/IncidentsOverYears.png')
        plt.close()

        '''


        '''
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)

        incidents = Incident.objects.filter(published__range=(start_date, end_date))

        fields = list(TAXONOMY_QUESTIONS.keys())

        # Create a defaultdict to hold the counts for each field
        field_counts = {field: defaultdict(int) for field in fields}

        # Process each incident
        for incident in incidents:
            for field in fields:
                field_value = getattr(incident, f"{field}_option", "")
                if field_value:  # Check if the field value is not empty or None
                    values = [v.strip() for v in field_value.split(",") if v.strip()]  # Split and strip whitespace
                    for value in values:
                        field_counts[field][value] += 1

        # Convert the dictionary to a DataFrame
        data = {field: dict(counts) for field, counts in field_counts.items()}
        df = pd.DataFrame(data).fillna(0).astype(int)

        # Transpose the DataFrame for easier plotting
        df = df.T
        df.index.name = 'Fields'

        # Plotting the stacked bar chart
        ax = df.plot(kind='barh', stacked=True, figsize=(14, 8))

        # Adding labels and title
        ax.set_xlabel('Count')
        ax.set_ylabel('Fields')
        ax.set_title('Distribution of Keys for Each Field in Incidents')
        ax.legend(title='Options', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.savefig('results/TaxonomyDistributionOverYears.png')
        '''

        '''
        incidents = Incident.objects.filter(published__range=(start_date, end_date))
        num_incidents = len(incidents)
        logging.info("Number of incidents between 2010 to 2022: " + str(num_incidents))


        incidents = Incident.objects.filter(published__range=(start_date, end_date), rag=True)
        num_incidents = len(incidents)
        logging.info("Number of incidents between 2010 to 2022 with RAG: " + str(num_incidents))

        incidents = Incident.objects.filter(published__range=(start_date, end_date), rag=False)
        num_incidents = len(incidents)
        logging.info("Number of incidents between 2010 to 2022 without RAG: " + str(num_incidents))
        '''

        '''
        incidents = Incident.objects.filter(published__range=(start_date, end_date))
        num_incidents = len(incidents)
        
        count = 0
        for incident in incidents:
            if "one_organization" in incident.recurring_option or "multiple_organization" in incident.recurring_option:
                count += 1
        
        logging.info("Number of recurring incidents, one_organization or multiple_organization: "+ str(count) +", "+str(int(count/num_incidents*100)) + "%")
        

        incidents = Incident.objects.filter(published__range=(start_date, end_date))
        num_incidents = len(incidents)
        
        count = 0
        for incident in incidents:
            if "one_organization" in incident.recurring_option or "multiple_organization" in incident.recurring_option:
                count += 1
        
        logging.info("Number of recurring incidents, one_organization or multiple_organization: "+ str(count) +", "+str(int(count/num_incidents*100)) + "%")
        '''

        ### For plotting the taxonomy
        '''
        characterize = "impacts" #impacts
        causes = ["recurring", "phase", "boundary", "nature", "dimension", "objective", "intent", "capability", "cps", "perception", "communication", "application"]
        impacts = ["duration", "behaviour", "domain", "consequence"]

        data  = {}
        for taxonomy_key in TAXONOMY_QUESTIONS.keys():
            data[taxonomy_key] = []


        for incident in incidents:
            for field in data.keys():
                values = getattr(incident, field+"_option")
                if values:
                    true_values = [val.strip() for val in values.split(",")]
                    if "unknown" in true_values and len(true_values) > 1: #If LLM says unknown and other options, then remove unknown.
                        true_values.remove("unknown")
                    data[field].extend(true_values)

        df = pd.DataFrame({key: pd.Series(value) for key, value in data.items()})

        # Determine the maximum count for scaling
        max_count = max(df.apply(lambda x: x.value_counts().max(), axis=0))

        #long_labels = ["multiple_organization","network_communication","embedded_software","accidental_decisions","natural_resources","connectivity_level","development_incompetence","theoretical_consequence"]

        fields = list(data.keys())
        if characterize == "causes":
            fields = [key for key in fields if key in causes]
        elif characterize == "impacts":
            fields = [key for key in fields if key in impacts]
        
        fig, axes = plt.subplots(nrows=int(len(fields)/4), ncols=4, figsize=(20, int((len(fields)/4)*5)))

        for i, ax in enumerate(axes.flatten()):
            if i < len(fields):
                num_incidents_ratio = num_incidents
                field = fields[i]
                value_counts = df[field].value_counts()

                if field == "consequence":
                    #value_counts = value_counts.drop(index="no_consequence")
                    value_counts = value_counts.drop(index="non-human")
                    value_counts = value_counts.drop(index="theoretical_consequence")

                bars = value_counts.plot(kind='barh', ax=ax)
                ax.set_title(field)
                ax.set_xlabel('Number of incidents')
                #ax.set_ylabel('Keys')

                if field in CPS_KEYS:
                    ax.set_xlim(0, df["cps"].value_counts()["TRUE"])  # Set the CPS Max for all subplots
                    num_incidents_ratio = df["cps"].value_counts()["TRUE"]
                else:
                    ax.set_xlim(0, num_incidents)  # Set the same x-axis limit for all subplots

                labels = [label.replace('_', '\n') for label in value_counts.index]
                ax.set_yticklabels(labels) # Replace underscores with spaces and set y-tick labels

                 # Display value of each bar inside the bar
                for bar in bars.patches:
                    width = bar.get_width()
                    placement = 'inside' if width > (max_count * 0.7) else 'outside'
                    text_color = 'black'
                    offset = -5 if placement == 'inside' else 5
                    ha = 'right' if placement == 'inside' else 'left'
                    ax.text(width + offset, bar.get_y() + bar.get_height() / 2, str(width)+", "+str(int(width/num_incidents_ratio*100))+"%", ha=ha, va='center', color=text_color, fontsize=12)
            
        plt.tight_layout()
        plt.savefig(f'results/TaxonomyDistributionSubplots{characterize}.png',dpi=300)
        
        '''


        ### To plot pie chart of keywords and sources 
        '''
        # Step 2: Get the associated articles for the queried incidents
        articles = Article.objects.filter(incident__in=incidents)

        # Step 3: Count the articles by keywords and sources
        keyword_counter = Counter()
        source_counter = Counter()


        for article in articles:
            unique_keywords = set(article.search_queries.values_list('keyword', flat=True))
            for keyword in unique_keywords:
                keyword_counter[keyword] += 1
            
            # Extract the domain name from the source URL
            if "dailymail" in article.source:
                domain = urlparse(article.source).netloc.split('.')[-3]
            else:
                domain = urlparse(article.source).netloc.split('.')[-2]
            
            source_counter[domain] += 1

        # Remove "software " from keyword labels
        keyword_counter = {k.replace("software ", ""): v for k, v in keyword_counter.items() if k.startswith("software ")}
        
        # Group small counts for keywords and sources
        keyword_counter = group_small_counts(keyword_counter)
        source_counter = group_small_counts(source_counter)

        # Sort the counters by count (smallest to largest)
        keyword_counter = dict(sorted(keyword_counter.items(), key=lambda item: item[1]))
        source_counter = dict(sorted(source_counter.items(), key=lambda item: item[1]))


        # Define a larger color palette
        colors = plt.cm.tab20.colors  # Tab20 has 20 distinct colors
        color_cycle = itertools.cycle(colors) # Create a color cycle iterator to handle more colors

        # Step 4: Plot the figures with two subplots
        fig, axs = plt.subplots(1, 2, figsize=(10, 5))

        # First subplot: Pie chart of articles by keywords
        wedges, texts, autotexts = axs[0].pie(keyword_counter.values(), labels=keyword_counter.keys(), autopct='%1.0f%%', startangle=140, colors=[next(color_cycle) for _ in keyword_counter], radius=1, pctdistance=0.85)
        axs[0].set_xlabel('(a)', weight='bold')

        # Increase text size and percentage size for the subplot
        for text in texts + autotexts:
            text.set_fontsize(12)
            text.set_color('black')
            text.set_fontweight('bold')  # Make labels bold


        # Second subplot: Pie chart of articles by sources
        wedges, texts, autotexts = axs[1].pie(source_counter.values(), labels=source_counter.keys(), autopct='%1.0f%%', startangle=140, colors=[next(color_cycle) for _ in source_counter], radius=1, pctdistance=0.85)
        axs[1].set_xlabel('(b)', weight='bold')

        # Increase text size and percentage size for the subplot
        for text in texts + autotexts:
            text.set_fontsize(12)
            text.set_color('black')
            text.set_fontweight('bold')  # Make labels bold


        #plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3)
        plt.tight_layout()

        plt.savefig(f'results/SourcesKeywordsPieChart.png',dpi=300)


# Step 4: Group keywords that are less than 2% into the "Other" category
def group_small_counts(counter, threshold=0.02):
    total_count = sum(counter.values())
    other_count = 0
    grouped_counter = Counter()
    for key, count in counter.items():
        if count / total_count < threshold:
            other_count += count
        else:
            grouped_counter[key] += count
    if other_count > 0:
        grouped_counter["other"] = other_count
    return grouped_counter
    '''