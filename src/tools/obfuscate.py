def obfuscate(byt):
    # Use same function in both directions.  Input and output are bytes
    # objects.
    mask = b'keyword'
    lmask = len(mask)
    return bytes(c ^ mask[i % lmask] for i, c in enumerate(byt))

def decode(data):
    return obfuscate(data).decode()

def test(s):
    data = obfuscate(s.encode())
    print(len(s), len(data), data)
    newdata = obfuscate(data).decode()
    print('obfuscated data', data)
    print('decoded data', newdata)
    print(newdata == s)


if __name__ == "__main__":
    s='https://gist.github.com/krishnakuruvadi/e7271043e29b4d9083094fb3aefe9e63/raw/be8c55d71c50941c45b05271c3b5890d88db26e5/ms.csv'
    test(s)

