# NLU

We build a very simple, lightweight intent classifier. Aimed to be comfortably run in
a Raspberry Pi 3b 🍓

> The original pipeline can be found in this
> [Colab Notebook](https://colab.research.google.com/drive/1q6Ei9SRdD8Pdg65Pvp8porRyFlQXD4w6#scrollTo=tqHkCDjuvj3g)


## 📐 Classifier (intent prediction)

### 🧬 Data Encoding

> 💡 We use a `LabelEncoder` which maps classes to integer indices

> 💡 We use `Spacy` to embed sentences into continuous vector space


## 📤 CRF (entity extraction)

We use [sklearn-crfsuite](https://github.com/TeamHG-Memex/sklearn-crfsuite) to extract entities.

> 💡 To know more check its [documentation](https://sklearn-crfsuite.readthedocs.io/en/latest/)!


## How To

While the rest of the components use `numpy~=1.16` the NLU components requires
a newer version in order to work with `scikit`.

Building the numpy wheel in the RPI can be a painfully slow process so to avoid
the pain a possible solution is to cross-compile using docker `buildx`.

1. Install buildx

  https://github.com/jmrf/pyvosk-rpi/blob/main/scripts/init_multi-build.sh

2. Run docker build (**in a work-station, not in the RPI!**):

  ```bash
  docker buildx build --push \
    --platform linux/arm/v7 \
    -t jmrf/numpy-rpi:1.21.6-cp37 \
    -f numpy_build.Dockerfile .
  ```

3. Run the container (**in the RPI**)

    ```bash
    docker run -it --entrypoint /bin/bash jmrf/numpy-rpi:py37-np1.21.6
    ```

    In another terminal:

    ```bash
    docker container ls  # copy the container ID
    docker cp <your-container-ID>:/numpy/dist/numpy-1.21.6-cp37-cp37m-linux_armv7l.whl .
    pip install numpy-1.21.6-cp37-cp37m-linux_armv7l.whl
    ```
