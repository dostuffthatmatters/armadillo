#!/bin/bash

pytest --cov=app --cov-report=term-missing --cov-report=xml ./tests
