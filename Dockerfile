FROM 753029624111.dkr.ecr.us-east-2.amazonaws.com/graphene/python_base:2023-06-12-1686593973

COPY . /analyzere
WORKDIR /analyzere

RUN poetry install --no-interaction --no-ansi --no-root;

CMD ["python", "-m", "pytest", "--junitxml=/results/testresults.xml"]
