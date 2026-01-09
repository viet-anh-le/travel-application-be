import random
def generate_code(length):
    code = ""
    characters = "0123456789"
    characters_length = len(characters)
    for i in range(length):
        code += characters[int(random.random() * characters_length)]
    return code