import hashlib

def hash_password(password):
    hashed_password = hashlib.sha224(password.encode('utf-8')).hexdigest()
    return hashed_password


def is_match(password, hash):
    hash_new = hash_password(password)
    # print(hash_new, hash)
    return hash_new == hash
