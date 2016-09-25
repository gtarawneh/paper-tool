#!/bin/bash

# stage 1 : remove lines containing multiple dots
# stage 2 : remove lines not containing at least 5 sequences of [WORD SPACE]
# stage 3 : remove lines with space followed by non-alpha char
# stage 4 : remove lines starting with smaller letters

sed -r "/^[a-zA-Z ,\-]+\..+$/d" | \
sed -r "/^([^\r\n\t\f ]+[ ]+){5,}.+$/!d" | \
sed -r "/[^a-zA-Z]{2}/d" | \
sed -r "/^[a-z]/d"
#sed -r "/ [^a-zA-Z]/d"
