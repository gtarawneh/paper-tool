#!/bin/bash

PAPER_DIR=/cygdrive/d/Library/

META_DIR=./meta/

pdfFile=$1

textFile=${pdfFile/.pdf/.txt}

textFile=${textFile/$PAPER_DIR/$META_DIR\/}

if [ ! -f "$textFile" ]; then

	textDIR="$(dirname -- "$textFile")"

	echo "Processing $pdfFile -> $textFile ..."

	[ -d "$textDIR" ] || mkdir -p -- "$textDIR"

	./runGrobid.sh "$pdfFile" > "$textFile"

fi