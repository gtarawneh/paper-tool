#!/bin/bash

PAPER_DIR=/cygdrive/d/Library/

TEXT_DIR=./text/

#rm ./source.txt

find $PAPER_DIR -name '*.pdf' -print0 |

	while IFS= read -r -d $'\0' pdfFile; do

		textFile=${pdfFile/.pdf/.txt}

		textFile=${textFile/$PAPER_DIR/$TEXT_DIR\/}

		textDIR="$(dirname -- "$textFile")"

		echo "Processing $pdfFile -> $textFile ..."

		[ -d "$textDIR" ] || mkdir -p -- "$textDIR"

		pdftotext -q "$pdfFile" - | ./getSentences.sh | ./getFiltered.sh > "$textFile"

	done
