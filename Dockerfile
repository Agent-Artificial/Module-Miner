FROM python:3.10-slim

WORKDIR /miner

RUN apt update && apt upgrade -y 
RUN apt install sudo build-essential git libsndfile1-dev libgmp10-dev -y

COPY requirements.txt /miner/
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . /miner/

RUN python -m module_manager --no-interaction --install

CMD ["python", "-m", "module_manager"]