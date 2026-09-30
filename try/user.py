ratediv = 0
ndiv = 0
def get_int(prompt):
    """Take user input and return it as an integer"""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid integer!")
