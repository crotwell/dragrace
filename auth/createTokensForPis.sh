#!/bin/bash

DAYS=60

for i in {1..9}
do
   python3 ../python/createToken.py -p XX_PI0${i}/IP -s ./secret.key -u dragrace -o pi0${i}_token.jwt --ed ${DAYS}
done

python3 ../dragrace/python/createToken.py -p 'XX(.|_).*/((IP)|(MAXACC)|(MSEED))' -s ./secret.key -u dragrace -o mseed_token.jwt --ed ${DAYS}


