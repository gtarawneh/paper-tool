#!/bin/bash

OUTFILE=/tmp/title.txt

cat $1 | jq ".[].title" | tr -d "\"" | fzf --reverse -e > $OUTFILE
