#
# 
#


def handle_variable(var):
    match var:
        case int():
            print(f"Variable is an integer: {var}")
        case float():
            print(f"Variable is a float: {var}")
        case str():
            print(f"Variable is a string: {var}")
        case list():
            print(f"Variable is a list: {var}")
        case dict():
            print(f"Variable is a dictionary: {var}")
        case _:
            print(f"Variable is of an unknown type: {type(var)}")


def main() -> None:
    handle_variable(10)       # Output: Variable is an integer: 10
    handle_variable(10.5)     # Output: Variable is a float: 10.5
    handle_variable("hello")  # Output: Variable is a string: hello
    handle_variable([1, 2, 3])# Output: Variable is a list: [1, 2, 3]
    handle_variable({"key": "value"}) # Output: Variable is a dictionary: {'key': 'value'}
    handle_variable((1, 2))   # Output: Variable is of an unknown type: <class 'tuple'>


if __name__ == '__main__':
    main()
