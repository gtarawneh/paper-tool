#!/bin/bash

SERVER=nightbird

curl -sv --form input="@$1" $SERVER:8080/processHeaderDocument 2>/dev/null
