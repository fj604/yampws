import ubinascii


def decode(string):
    p = 0
    ret = ""
    while p < len(string):
        if string[p] == "%":
                if p < len(string) - 1 and string[p+1] == "%":
                    ret += "%"
                    p += 2
                elif p < len(string) - 2:
                    ret += ubinascii.unhexlify(string[p+1:p+3]).decode()
                    p += 3
                else:
                    p += 1
        else:
            ret += string[p]
            p += 1
    return ret.replace("+"," ")
