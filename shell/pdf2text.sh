#!/bin/bash

pdfFile=$1
textFile=$2

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NLP_JAR="shell/opennlp-tools-1.6.0.jar"

MODEL="shell/en-sent.bin"

_dir=`dirname -- "$2"`

mkdir -p -- "$_dir"

pdftotext -q "$pdfFile" - \
| tr -cd '[:alpha:][:blank:].,\-\n\r' | tr '\n\r' ' ' \
| java -jar $NLP_JAR SentenceDetector $MODEL 2>/dev/null \
| sed -r "/^[a-zA-Z ,\-]+\..+$/d" \
| sed -r "/^([^\r\n\t\f ]+[ ]+){5,}.+$/!d" \
| sed -r "/[^a-zA-Z]{2}/d" \
| sed -r "/^[a-z]/d" \
> "$textFile"
