FROM 612007926530.dkr.ecr.us-east-1.amazonaws.com/analyzere-python-base:latest
COPY . /analyzere
WORKDIR /analyzere
RUN pyenv local 2.7.15 3.4.9 3.5.6 3.6.6 3.7.0

CMD ["tox", "-c", "tox-jenkins.ini"]
