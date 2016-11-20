#!/bin/bash

TMPFILE=/tmp/paper.txt
OUTFILE=/tmp/title.txt

if [ "$#" -gt 0 ] && [ -e "$1" ]; then
	pdftotext $1 $TMPFILE && \
	cat $TMPFILE | fzf --prompt="Paper title: "  -m --reverse --print-query > $OUTFILE
else
	echo "ERROR" > $OUTFILE
fi
