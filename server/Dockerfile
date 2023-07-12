FROM python:3.9-bullseye

WORKDIR /sdk_server

COPY Pipfile .

RUN python -m pip install -U pipenv \ 
    && pipenv lock \
    && pipenv install --system

COPY . . 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]