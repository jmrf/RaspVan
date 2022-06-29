FROM jmrf/spacy-rpi:3.3.1-cp37


RUN pip install \
        coloredlogs \
        pyyaml \
    && python -m spacy download en_core_web_sm \
    && python -m spacy link en_core_web_sm en_core_web_sm

RUN mkdir -p /app
WORKDIR /app

