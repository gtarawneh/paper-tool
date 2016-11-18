#!/bin/bash

FILE="apache-opennlp-1.6.0-bin.tar.gz"

curl -Os http://mirror.catn.com/pub/apache/opennlp/$FILE

tar -xzf ./$FILE

JAR=`find -name 'opennlp-tools-1.6.0.jar'`

mv -u $JAR .

rm $FILE

