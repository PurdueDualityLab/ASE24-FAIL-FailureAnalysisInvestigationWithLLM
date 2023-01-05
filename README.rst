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

