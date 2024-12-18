FROM jmrf/spacy-rpi:3.3.1-cp37

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt \
    && python -m spacy download en_core_web_sm \
    && python -m spacy link en_core_web_sm en_core_web_sm



