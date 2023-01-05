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

    $ python manage.py createsuperuser

#. Access the site administration page at ``/admin/``
