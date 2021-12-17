FROM python:3.9
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install pipenv
WORKDIR /alwaysontime
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --dev
COPY alwaysontime .