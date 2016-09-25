#!/bin/bash

PAPER_DIR=/cygdrive/d/Library/

META_DIR=./meta/

rm -rf META_DIR

find $PAPER_DIR -name '*.pdf' -printf '"%p"\n' | xargs -I {} ./getMeta.sh {}
