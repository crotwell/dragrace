import argparse
import json
import collections

def dict_raise_on_duplicates(ordered_pairs):
    """Reject duplicate keys."""
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           raise ValueError("duplicate key: %r" % (k,))
        else:
           d[k] = v
    return d

def configSanityCheck(configFile):

    sanityPass=True
    data=configFile.read()

# parse file
    try:
        newConfig = json.loads(data,object_pairs_hook=dict_raise_on_duplicates)

    except json.decoder.JSONDecodeError as emsg:
        print("********************************************")
        print("The Config File is NON-COMPLIANT ... check your editing!!")
        print("The Error is: {}".format(emsg))
        print("********************************************")
        exit()
    except ValueError as vmsg:
        print("********************************************")
        print("The Config File is NON-COMPLIANT ... check your editing!!")
        print("Duplicate Key Found: {}".format(vmsg))
        print("********************************************")
        exit()

# If parse works, do sanity tests

    piDict = newConfig["Loc"]
    detailsDict = newConfig["LocInfo"]

#**********
#  Do a series of sanity checks on the filename
#
# Check if two Pis appear to be in the same locations
#
    listOfPositions=[]
    for position in piDict.values():
        if(position != "NO"):
            listOfPositions.append(position)
            if(listOfPositions.count(position) > 1):
                print("{} appears {} times".format(position,listOfPositions.count(position)))
                sanityPass=False
#
# Test for known Pis.  Undocumented Pis are not identified
#
    for pi in ["PI01", "PI02", "PI03", "PI04", "PI05", "PI06", "PI07", "PI08", "PI09","PI10","PI11"]:
        foundIt=piDict.get(pi,"False")
        if(foundIt == "False"):
            print("{} is missing in Location Dictionary".format(pi))
            sanityPass=False
#
# Make sure known Pis are in known locations
#    This will find unknown location codes
#
        if piDict.get(pi) not in ["NO","FL","NL","CT","NR","FR","FL0","FL60","FL330","FL660","FL1K"]:
            print('{}:  Location of {} is not valid'.format(pi,piDict.get(pi)))
            sanityPass=False
    return sanityPass

if __name__ == "__main__":
    print("Running from command line")
    parser = argparse.ArgumentParser()
    parser.add_argument("-f",
                        dest="configFile",
                        type=argparse.FileType('r'),
                        help="your config file to test")
    args=parser.parse_args()
    print(args.configFile)
    goodConfig=configSanityCheck(args.configFile)
    print(" ")
    print(" *** configChecker Output ***")

    if(goodConfig):
      print("Config File is valid, feel free to run deployConfig!")
    else:
      print("Config file {} FAILS, fix and rerun configChecker")

    print (" ")
    print(" *************** ")
