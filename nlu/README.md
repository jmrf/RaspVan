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

### Install


Installing `Spacy` can be challenging in an Raspberry Pi.
The advice is either to cross-compile or to use pre-built wheels.

`Blis` and `Spacy` wheels can be found [here](https://github.com/hoefling/so-59927844)

Alternatively you can cross-compile / build your own:

<details>
  <summary>Click to expand!</summary>


Building the `blis`, `spacy` or `numpy` wheels in the RPI can be a painfully
slow process so to avoid the suffering a possible solution is to cross-compile
using docker `buildx`.

The steps are as follows:

1. Install buildx

  You can use [this script](https://github.com/jmrf/pyvosk-rpi/blob/main/scripts/init_multi-build.sh)

2. Run docker build (**in a work-station, not in the RPI!**):

  ```bash
  docker buildx build --push \
    --platform linux/arm/v7 \
    -t jmrf/simple-nlu-rpi:cp37 \
    -f Dockerfile .
  ```

3. Run the container (**in the RPI**)

    ```bash
    docker run -it --entrypoint /bin/bash jmrf/numpy-rpi:py37-np1.21.6
    ```

    In another terminal:

    ```bash
    docker container ls  # copy the container ID

    # Copy the wheels back to the target system
    docker cp <your-container-ID>:/numpy/dist/numpy-1.21.6-cp37-cp37m-linux_armv7l.whl .
    pip install numpy-1.21.6-cp37-cp37m-linux_armv7l.whl
    ```

</details>
