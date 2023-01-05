Failures
========

Failures is a rich database of software failures scraped from news articles.

Running with Docker
-------------------

#. Build and spin up the container::

    $ docker compose -f local.yml up --build -d

#. Apply the migrations in the container::

    $ docker compose -f local.yml run --rm django python manage.py migrate


Admin Site
^^^^^^^^^^

#. Create an admin account::

    $ docker compose -f local.yml run --rm django python manage.py createsuperuser

#. Access the site administration page at ``/admin/``

Main Site: WIP
^^^^^^^^^^^^^^

#. Make sure the container is running::

    $ docker compose -f local.yml up

#. Access the main site at ``/failures/``

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


Summarizing Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures summarize --help

#. Summarize articles::

    $ docker compose -f local.yml run --rm django python -m failures summarize --all



Classifying Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures classify --help

#. Classify articles::

    $ docker compose -f local.yml run --rm django python -m failures classify --all


Create Embedding for Articles Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures embed --help

#. Create embeddings for articles::

    $ docker compose -f local.yml run --rm django python -m failures embed --all


Merge Articles into Failures Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures merge --help

#. Merge articles into failures::

    $ docker compose -f local.yml run --rm django python -m failures merge --all


Admin Parameters
----------------

#. ``FAILURE_NAME_QUESTION``: The question to ask the question and answer model
   when predicting the over-arching failure name. The default is
   ``"What is the name of the software failure?"``.

#. ``FAILURE_INDUSTRY_QUESTION``: The question to ask the question and answer
   model when predicting the industry of the failure. The default is
   ``"What industry does this software failure belong to?"``.

#. ``FAILURE_STARTED_AT_QUESTION``: The question to ask the question and answer
   model when predicting the start date of the failure. The default is
   ``"When did this software failure start?"``.

#. ``FAILURE_ENDED_AT_QUESTION``: The question to ask the question and answer
    model when predicting the end date of the failure. The default is
    ``"When did this software failure end?"``.

#. ``FAILURE_POSITIVE_CLASSIFICATION_CLASS``: The class used as one of the
    labels for the zero-shot classification model when predicting that the article is about a
    software failure. The default is ``"software failure"``.

#. ``FAILURE_NEGATIVE_CLASSIFICATION_CLASS``: The class used as one of the labels for
    the zero-shot classification model when predicting that the article is not about a
    software failure. The default is ``"not a software failure"``.
