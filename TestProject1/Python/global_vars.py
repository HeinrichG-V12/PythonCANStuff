#!/usr/bin/env python3


def create_global_variable():
    global global_variable # must declare it to be a global first
    # modifications are thus reflected on the module's global scope
    global_variable = 'Foo'

def use_global_variable():
    print(global_variable + '!!!')

def change_global_variable():
    global global_variable
    global_variable = 'Bar'


def main():
    create_global_variable()
    use_global_variable()
    change_global_variable()
    use_global_variable()

if __name__ == '__main__':
    main()