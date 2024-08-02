import random
import sys

def shika(s):
    if s == "し":
        r = random.randint(0, 1)

        if r == 0:
            return "か"

        else:
            return "た"

    elif s == "か":
        return "の"

    elif s == "の":
        return "こ"

    elif s == "こ":
        r = random.randint(0, 3)

        if r == 0:
            return "こ"

        elif r == 1:
            return "し"

        else:
            return "の"

    elif s == "た":
        return "ん"

    else:
        r = random.randint(0, 1)

        if r == 0:
            return "た"

        else:
            return "END"