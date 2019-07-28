a = '''
def numb():
    return 1
'''

b = '''
def add_numb():
    result = numb() + 1
    return result

print(add_numb())
'''


if __name__ == '__main__':
    code = '{}{}'.format(a, b)
    print(code)
    exec(code)
