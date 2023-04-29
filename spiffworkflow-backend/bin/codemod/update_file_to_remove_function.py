from bowler import Query
from bowler.types import Leaf

# This came about because vulture (actually dead, from the list of Similar programs at https://pypi.org/project/vulture/)
# actually found unused stuff, and I wanted to remove it.
# See also https://github.com/craigds/decrapify

def remove_function(filename: str, function_name: str) -> None:

    def remove_statement(node, capture, filename):
        node.remove()

    bowler_query = (Query(filename)
        .select_function(function_name)
        .modify(remove_statement)
        .execute(write=True))

    if len(bowler_query.exceptions) > 0:
        print(f"Failed to remove function {function_name} from {filename}.")
        raise Exception(bowler_query.exceptions[0])

    print(f"Function {function_name} successfully removed from {filename}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Remove a function from a Python file while preserving comments.")
    parser.add_argument("filename", help="the file to modify")
    parser.add_argument("function_name", help="the name of the function to remove")
    args = parser.parse_args()

    remove_function(args.filename, args.function_name)
