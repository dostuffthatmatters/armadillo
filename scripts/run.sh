#!/bin/bash

docker run -d -p 8080:8080 \
    -e ENVIRONMENT='development' \
    -e MONGO_DB_CONNECTION_STRING='mongodb+srv://fastapi-backend:Hso7zAPzMQY3sCAb@armadillocluster.vambn.gcp.mongodb.net' \
    -e IBM_API_KEY='8bkPmfd8GRRq_enIkKVeA-g0ZDvrNpW4H1DWu9YzJgOh' \
    armadillo
