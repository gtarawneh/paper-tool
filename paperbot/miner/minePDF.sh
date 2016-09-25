#!/bin/bash

PAPER_DIR=/cygdrive/d/Library/

TEXT_DIR=./text/

pdfFile=$1

textFile=${pdfFile/.pdf/.txt}

textFile=${textFile/$PAPER_DIR/$TEXT_DIR\/}

textDIR="$(dirname -- "$textFile")"

echo "Processing $pdfFile -> $textFile ..."

[ -d "$textDIR" ] || mkdir -p -- "$textDIR"

pdftotext -q "$pdfFile" - | ./getSentences.sh | ./getFiltered.sh > "$textFile"