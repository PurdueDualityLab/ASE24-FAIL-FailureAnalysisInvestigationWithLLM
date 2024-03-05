Failures Evaluation
========

This folder contains commands necessary to monitor, test, and evaluate the performance and quality of the Failures pipeline and database.


Evaluate Pipeline's Classification Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Introduction
------------

This command is designed for evaluating the pipeline's classification command. The classification command is responsible for determing whether and article does or does not describe a software failure.

Metrics Evaluated
-----------------

- Accuracy (Percentage): Measures the overall correctness of the classification in percentage.
- Accuracy (Fraction): Indicates the accuracy of the classification in fraction format.
- False Positive (Percentage): Percentage of false positives in the classification.
- False Positive (Fraction): Fraction of false positives in the classification.
- False Negative (Percentage): Percentage of false negatives in the classification.
- False Negative (Fraction): Fraction of false negatives in the classification.
- Wrong (Percentage): Percentage of incorrect classifications.
- Wrong (Fraction): Fraction of incorrect classifications.
- Total Evaluated: Total number of articles evaluated.

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures scrape --help

#. Run a scrape::

    $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"


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
