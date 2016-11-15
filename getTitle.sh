#!/bin/bash

TMPFILE=/tmp/paper.txt

if [ "$#" -gt 0 ]; then
	pdftotext $1 $TMPFILE && \
	cat $TMPFILE | fzf --prompt="Paper title: "  -m --reverse --print-query
else
	echo "ERROR"
fi
