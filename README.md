# ELWIS SBF Binnen Questions Parser

This script parses the ELWIS Page and generates a JSON File with the current
Questions and Answers.

Images are downloaded into a _assets_ Folder.

As status 10.2018, the correct answer at ELWIS is always answer **a**

# Running the parser

    docker-compose run python /usr/local/bin/python /app/parser.py
