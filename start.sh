#!/bin/bash

sudo apt update

sudo apt install -y ffmpeg

pip install -r rq.txt

cd core/

python manage.py runserver