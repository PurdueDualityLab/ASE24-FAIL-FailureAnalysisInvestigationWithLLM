Failures
========

Failures is a rich database of software failures scraped from news articles.

Running with Docker
-------------------

#. Build and spin up the container::

    $ docker compose -f local.yml up --build -d

#. Apply the migrations in the container::

    $ docker compose -f local.yml run --rm django python manage.py makemigrations
    $ docker compose -f local.yml run --rm django python manage.py migrate

#. Make sure the container is running::

    $ docker compose -f local.yml up
    
#. To log a command, follow these steps:

    #. Run the command::

        $ docker compose -f local.yml run -e OPENAI_API_KEY -d --name failures_run_command django python -m failures classify
    
    #. Wait for the command to finish running, then export the log::

        $ docker logs failures_run_command >> failures_run_command.log 2>&1

    #. Then kill the container::

        $ docker rm failures_run_command


Admin Site
^^^^^^^^^^

#. Create an admin account::

    $ docker compose -f local.yml run --rm django python manage.py createsuperuser

#. Access the site administration page at ``/admin/``


Scraping News Articles Using the Admin Site and the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Navigate to the ``/admin/`` page and log in.

#. Click on ``Search Queries`` underneath the ``Articles`` section.

#. Click on ``ADD SEARCH QUERY +``.

#. Enter a search query and click ``SAVE``.

#. Run a scrape from the command line::

    $ docker compose -f local.yml run --rm django python -m failures scrape


Scraping News Articles Using Only the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures scrape --help

#. Run a scrape::

    $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"

#. To scrape news for automated experiments use: experiment.sh


Classifying Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures classify --help

#. Classify articles::

    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures classify --all


Create Postmortems for Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures postmortem --help

#. Create postmortems::

    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures postmortem --all

Evaluate LLM Classification of Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluateclassification --help

#. Evaluate LLM's Classification::

    $ docker compose -f local.yml run --rm django python -m tests evaluateclassification --all --list

Evaluate LLM Analysis of Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluateidentification --help

#. Evaluate LLM's Analysis::

    $ docker compose -f local.yml run --rm django python -m tests evaluateidentification --all --list

Evaluate LLM Merge of Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluatemerge --help

#. Evaluate LLM's Merge::

    $ docker compose -f local.yml run --rm django python -m tests evaluatemerge --all

Evaluate LLM Taxonomization of Articles Using the Command Line ##TODO##
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluatemerge --help

#. Evaluate LLM's Merge::

    $ docker compose -f local.yml run --rm django python -m tests evaluatemerge --all

Evaluate LLM Postmortem Creation Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m tests evaluatepostmortem --help

#. Evaluate LLM's Merge::

    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m tests evaluatepostmortem

Evaluate LLM's performance given set of temperature values Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m tests evaluatetemperature --help
    
#. Evaluate LLM's Merge::

    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m tests evaluatetemperature --all
    
Create Embedding for Articles Using the Command Line (OUTDATED): REMOVE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures embed --help

#. Create embeddings for articles::

    $ docker compose -f local.yml run --rm django python -m failures embed --all


Setting Admin Parameters (OUTDATED): REMOVE
^^^^^^^^^^^^^^^^^^^^^^^^

#. Navigate to the ``/admin/`` page and log in.

#. Click on ``Parameters`` underneath the ``Parameters`` section.

#. Click on ``ADD PARAMETER +``.

#. Enter a name, value, and value type and click ``SAVE``.

#. Repeat for each parameter.

Working with Parameters Programmatically (OUTDATED): REMOVE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Import the ``Parameter`` model::

    >>> from failures.parameters.models import Parameter

#. Get the value of a parameter::

        >>> Parameter.get("FAILURE_NAME_QUESTION", "What is the name of the software failure?")
        'What is the name of the software failure?'

If the parameter does not exist, it will be created with the default value. This is similar to
``dict.get``; however, parameters set in the admin site are persisted in the database.

Using failures.networks Programmatically (OUTDATED): Update (w/ open source models + OpenAI models)
---------------------------------------

There are four main classes in the ``failures.networks.models`` module:

#. ``ZeroShotClassifier``::

        >>> from failures.networks.models import ZeroShotClassifier
        >>> classifier = ZeroShotClassifier(["software failure", "not a software failure"])
        >>> classifier.run("This is a software failure.")
        ('software failure', 0.9999998807907104)


#. ``Summarizer``::

        >>> from failures.networks.models import Summarizer
        >>> summarizer = Summarizer()
        >>> summarizer.run("This is an article about a software failure...")
        'This is a summary of the article.'

#. ``QuestionAnswerer``::

        >>> from failures.networks.models import QuestionAnswerer
        >>> question_answerer = QuestionAnswerer()
        >>> question_answerer.run("When did this software failure start?", "This software failure started in 2020.")
        '2020'


#. ``Embedder``::

        >>> from failures.networks.models import Embedder
        >>> embedder = Embedder()
        >>> embedder.run("This is an article about a software failure...")
        array([ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00, ...,
                0.00000000e+00,  0.00000000e+00, -1.19209290e-07], dtype=float32)

