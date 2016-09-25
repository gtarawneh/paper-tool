#!/bin/bash

PAPER_DIR=/cygdrive/d/Library/

TEXT_DIR=./text/

rm -rf TEXT_DIR

#find $PAPER_DIR -name '*.pdf' | xargs -I {} ./minePDF.sh "{}"

find $PAPER_DIR -name '*.pdf' | parallel -j 6 ./minePDF.sh 2>/dev/null
