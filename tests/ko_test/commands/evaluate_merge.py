from sklearn.metrics import homogeneity_score, completeness_score, v_measure_score
import argparse
import logging
import textwrap
import pandas as pd

from failures.articles.models import Article_Ko, SearchQuery


class EvaluateMergeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate merge command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM at merging the articles into clusters of incidents. This will return
            a V-Measure which is a harmonic mean between a homogeneity score and a completeness score. If no arguments are
            provided, all articles that have a corresponding manual classificaiton will be used to score performacne and only
            V-Measure will be logged.
            If --all is provided then more metrics will be output (V-Measure, Homogeneity Score, Completeness Score, etc.)
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Create dictionary to store metrics
        metrics = {
            "Homogeneity": 0,
            "Completeness": 0,
            "V Measure": 0
        }

        # Define the file path
        # input_file_path = "./tests/ko_test/data/Ko_Stories_Consensus.csv"
        # TODO: add input path as interrater agreement csv. Then read the files in using the storyID and the articleID, then compare
        input_file_path = ""
        output_file_path = "tests/ko_test/performance/merge.csv"

        # Define the columns to read
        columns_to_read = ["storyID", "articleID", "DjangoArticleID", "Consensus"]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_csv(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return metrics
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return metrics

        # Filter out rows with missing values in 'DjangoArticleID'
        df = df.dropna(subset=['DjangoArticleID'])

        # Filter rows where 'Consensus' is 'relevant'
        df = df[df['Consensus'] == 'relevant']

        # Get a list of article IDs from the manual database
        article_ids = df['DjangoArticleID'].astype(int).tolist()

        # Query for articles matching manual db IDs
        matching_articles = Article_Ko.objects.filter(id__in=article_ids)

        # Map id to incident for ground truth and predicted
        ground_truth_mapping =  {row['DjangoArticleID']: int(row['storyID']) for _, row in df.iterrows()}
        predicted_mapping = {article.id: article.incident.id for article in matching_articles if article.incident}

        # Get common ids
        common_ids = set(ground_truth_mapping.keys()) & set(predicted_mapping.keys())

        # Create lists for true labels and predicted labels based on common IDS
        true_labels = [ground_truth_mapping[article_id] for article_id in common_ids]
        predicted_labels = [predicted_mapping[article_id] for article_id in common_ids]

        # Calculate homogeneity, completeness, and V-Measure
        if common_ids:
            # Calculate homogeneity score
            homogeneity = homogeneity_score(true_labels, predicted_labels)

            # Calculate completeness score
            completeness = completeness_score(true_labels, predicted_labels)

            # Calculate V-measure
            v_measure = v_measure_score(true_labels, predicted_labels)

            # Log results
            logging.info(f"Homogeneity Score: {homogeneity:.2f}")
            logging.info(f"Completeness Score: {completeness:.2f}")
            logging.info(f"V-Measure Score: {v_measure:.2f}")

            # Store metrics
            metrics["Homogeneity"] = homogeneity
            metrics["Completeness"] = completeness
            metrics["Measure"] = v_measure
        else:
            logging.info("Evaluate Merge Command: No common IDs found between ground truth and predicted data.")

        # Store metrics in a CSV file
        csv_output_path = "./tests/ko_test/eval/merge_output.csv"

        # Convert metrics dictionary to a Pandas DataFrame
        metrics_df = pd.DataFrame(metrics, index=[0])

        # Save the DataFrame to a CSV file
        metrics_df.to_csv(csv_output_path, index=False)
        logging.info(f"Metrics saved to {csv_output_path}")


        return metrics
