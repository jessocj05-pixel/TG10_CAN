ratediv = 0
ndiv = 0
freq = 0
tperiod = 0.0
char = 'a'
def get_int(text):
    """Take user input and return it as an integer"""
    while True:
        try:
            return int(input(text))
        except ValueError:
            print("Please enter a valid integer!")

def get_float(text):
    """Take user input and return it as an integer"""
    while True:
        try:
            return float(input(text))
        except ValueError:
            print("Please enter a valid float!")

def get_char(text):
    while True:
        value = input(text)
        if len(value) == 1 and value.isalpha():
            return value
        print("Please enter a single letter!")