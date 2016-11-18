#!/bin/bash

pdfFile=$1
textFile=$2

_dir=`dirname -- "$2"`

mkdir -p -- "$_dir"

pdftotext -q "$pdfFile" - \
| tr -cd '[:alpha:][:blank:].,\-\n\r' | tr '\n\r' ' ' \
| java -jar opennlp-tools-1.6.0.jar SentenceDetector en-sent.bin 2>/dev/null \
| sed -r "/^[a-zA-Z ,\-]+\..+$/d" \
| sed -r "/^([^\r\n\t\f ]+[ ]+){5,}.+$/!d" \
| sed -r "/[^a-zA-Z]{2}/d" \
| sed -r "/^[a-z]/d" \
> $textFile
