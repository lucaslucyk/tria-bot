#!/bin/bash

# poetry run coverage run -m unittest discover -s ./tria_bot/tests -t ..
poetry run coverage run -m pytest -s ./tria_bot/tests -vv