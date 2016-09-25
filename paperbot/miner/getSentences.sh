 #!/bin/bash

tr -cd '[:alpha:][:blank:].,\-\n\r' | tr '\n\r' ' ' | java -jar opennlp-tools-1.6.0.jar SentenceDetector en-sent.bin 2>/dev/null
