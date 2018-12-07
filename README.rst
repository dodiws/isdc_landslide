=========
landslide
=========

Process and display landslide data.
Optional Module for ISDC

Quick start
-----------

1. Add "landslide" to your DASHBOARD_PAGE_MODULES setting like this::

    DASHBOARD_PAGE_MODULES = [
        ...
        'landslide',
    ]

    If necessary add "landslide" in (check comment for description): 
        QUICKOVERVIEW_MODULES, 
        MAP_APPS_TO_DB_CUSTOM

    For development in virtualenv add LANDSLIDE_PROJECT_DIR path to VENV_NAME/bin/activate:
        export PYTHONPATH=${PYTHONPATH}:\
        ${HOME}/LANDSLIDE_PROJECT_DIR

2. To create the landslide tables:

   python manage.py makemigrations
   python manage.py migrate landslide --database geodb

