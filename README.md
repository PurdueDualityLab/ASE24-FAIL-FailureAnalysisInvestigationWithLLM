# Failures

Failures is a rich database of software failures scraped from news articles.

## Setting up the pipeline

### Setting up the docker containers for the pipeline

1. Build and spin up the container:

    ```bash
    $ docker compose -f local.yml up --build -d
    ```

2. Apply the migrations in the container:

    ```bash
    $ docker compose -f local.yml run --rm django python manage.py makemigrations
    $ docker compose -f local.yml run --rm django python manage.py migrate
    ```

3. Make sure the container is running:

    ```bash
    $ docker compose -f local.yml up
    ```

> [!TIP]
Note: To log stdout/stderr for pipeline command that is detached, follow these steps:
>1. Run the command:
>
>        $ docker compose -f local.yml run -e OPENAI_API_KEY -d --name failures_run_command django python -m failures classify  
>2. Wait for the command to finish running, then export the log:
>
>        $ docker logs failures_run_command >> failures_run_command.log 2>&1
>3. Then kill the container:
>
>        $ docker rm failures_run_command


### Admin Site

1. Create an admin account:

    ```bash
    $ docker compose -f local.yml run --rm django python manage.py createsuperuser
    ```

2. Access the site administration page at `/admin/`

## Running the pipeline
### Step 1. Searching and scraping news articles 
Option 1. Using the Admin Site and the Command Line

   1. Navigate to the `/admin/` page and log in.

   2. Click on `Search Queries` underneath the `Articles` section.

   3. Click on `ADD SEARCH QUERY +`.

   4. Enter a search query and click `SAVE`.

   5. Run a scrape from the command line:

       ```bash
       $ docker compose -f local.yml run --rm django python -m failures scrape
       ```

Option 2. Using Only the Command Line

   1. Display the help text:

       ```bash
       $ docker compose -f local.yml run --rm django python -m failures scrape --help
       ```

   2. Run a scrape:

       ```bash
       $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"
       ```

> [!TIP] 
>To scrape news for specific years, specific sources, specific key words, modify and run: [tests/commands/exp_RunQueriesCommand.py](tests/commands/exp_RunQueriesCommand.py)

### Step 2. Classifying articles on whether they report on software failures

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures classifyfailure --help
    ```

2. Classify articles:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures classifyfailure
    ```

### Step 3. Classifying articles on whether they contain enough information for failure analysis

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures classifyanalyzable --help
    ```

2. Classify articles:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures classifyanalyzable
    ```

### Step 4. Merge articles reporting on the same failure into incidents

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures merge --help
    ```

2. Merge articles:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures merge
    ```

### Step 6. Create a postmortem report for each incident

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures postmortemincidentautovdb --help
    ```

2. Create postmortem reports:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures postmortemincidentautovdb
    ```

> [!NOTE]
> Step 5 (RAG) from the paper is within this command.


### Plot figures and gather statistics used in the paper 

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures results --help
    ```

2. Create postmortem reports:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures results
    ```

### To evaluate the steps of the pipeline, follow [tests/README.rst](tests/README.rst)

## Manual analysis and evaluation
### Step 2 to Step 4: Manual analysis and evaluation: [results/manual_analysis/Step2_to_Step4.xlsx](results/manual_analysis/Step2_to_Step4.xlsx)
### Step 6: Manual analysis and evaluation: [results/manual_analysis/Step6.xlsx](results/manual_analysis/Step6.xlsx)

