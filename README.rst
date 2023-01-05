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

Scraping News Articles Using the Admin Site
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Navigate to the ``/admin/`` page and log in.

#. Click on ``Search Queries`` underneath the ``Articles`` section.

#. Click on ``ADD SEARCH QUERY +``.

#. Enter a search query and click ``SAVE``.

#. Run a scrape from the command line::

    $ docker compose -f local.yml run --rm django python -m failures scrape

