FROM python:3.7

WORKDIR /code
RUN mkdir src/
# Be sure to run with run.sh, which mounts the code to src/

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y libxkbcommon-x11-0 libdbus-1-3 libgssapi-krb5-2 libgl1 "^libxcb-*"

ENTRYPOINT [ "python", "src/app.py" ]
