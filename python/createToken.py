import argparse
import asyncio
from datetime import timedelta
import json
import sys

import simpleDali

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-s",
                        dest="secretFile",
                        default="secret.key",
                        type=argparse.FileType('r'),
                        required=True,
                        help="secret key file, key on first line")
    parser.add_argument("-p",
                        dest="pattern",
                        required=True,
                        help="regular expression match pattern for WRITE, like 'XX_.*/MTRIG'")
    parser.add_argument("-u",
                        dest="username",
                        required=True,
                        help="username")
    parser.add_argument("-e",
                        dest="expire",
                        type=int,
                        default=60,
                        help="expire time in minutes")
    parser.add_argument("--verify",
                        dest="verify",
                        help="verify by sending an authorization requst to the datalink server at the given uri")

    parser.add_argument("-o",
                        dest="outputFile",
                        type=argparse.FileType('w'),
                        help="output token file, encoded token on first line")
    args = parser.parse_args(argv)

    secretKey = args.secretFile.readline().strip()
    token = simpleDali.encodeAuthToken(args.username, timedelta(minutes=args.expire), args.pattern, secretKey)

    if args.outputFile is not None:
        args.outputFile.write(token.decode('utf-8'))
        args.outputFile.close()
    else:
        prettyPayload = json.dumps(simpleDali.decodeAuthToken(token, secretKey), indent=4, sort_keys=True)
        print("token payload as json: \n{}".format(prettyPayload))
        print("token: \n\n{}\n".format(token.decode('utf-8')))
        print("token expires in {}".format(simpleDali.timeUntilExpireToken(token)))

    if args.verify is not None:
        loop = asyncio.get_event_loop()
        #loop.set_debug(True)
        programname="createToken.py"
        username="dragrace"
        processid=0
        architecture="python"
        dali = simpleDali.WebSocketDataLink(args.verify, verbose=True)
        idTask = loop.create_task(dali.id(programname, username, processid, architecture))
        loop.run_until_complete(idTask)
        serverId = idTask.result()
        print("Resp: {}".format(serverId))
        authTask = loop.create_task(dali.auth(token))
        loop.run_until_complete(authTask)
        print("Auth Resp: {}".format(authTask.result()))
        authTask = loop.create_task(dali.close())
        loop.run_until_complete(authTask)
        loop.close()

if __name__ == "__main__":
    main(sys.argv[1:])
