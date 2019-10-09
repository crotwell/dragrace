#!/bin/bash

/usr/bin/python3 /home/geo/Auth/dragrace/python/createToken.py -p '/MTRIG' -s /home/geo/Auth/auth/secret.key -u dragrace -o /home/geo/Auth/www/dutytoken.jwt --em 70 >> /home/geo/Auth/regenToken.log 2>&1
