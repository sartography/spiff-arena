import itertools
import os
from collections.abc import ItemsView
from collections.abc import Iterable


def normalized_environment(key_values: os._Environ) -> dict:
    results = _parse_environment(key_values)
    if isinstance(results, dict):
        return results
    raise Exception(f"results from parsing environment variables was not a dict. This is troubling. Results were: {results}")


# source originally from: https://charemza.name/blog/posts/software-engineering/devops/structured-data-in-environment-variables/
def _parse_environment(key_values: os._Environ | dict) -> list | dict:
    """Converts denormalised dict of (string -> string) pairs, where the first string
    is treated as a path into a nested list/dictionary structure

    {
        "FOO__1__BAR": "setting-1",
        "FOO__1__BAZ": "setting-2",
        "FOO__2__FOO": "setting-3",
        "FOO__2__BAR": "setting-4",
        "FIZZ": "setting-5",
    }

    to the nested structure that this represents

    {
        "FOO": [{
            "BAR": "setting-1",
            "BAZ": "setting-2",
        }, {
            "FOO": "setting-3",
            "BAR": "setting-4",
        }],
        "FIZZ": "setting-5",
    }

    If all the keys for that level parse as integers, then it's treated as a list
    with the actual keys only used for sorting

    This function is recursive, but it would be extremely difficult to hit a stack
    limit, and this function would typically by called once at the start of a
    program, so efficiency isn't too much of a concern.

    Copyright (c) 2018 Department for International Trade. All rights reserved.

    This work (this function) is licensed under the terms of the MIT license.
    For a copy, see https://opensource.org/licenses/MIT.
    """

    # Separator is chosen to
    # - show the structure of variables fairly easily;
    # - avoid problems, since underscores are usual in environment variables
    separator = "__"

    def get_first_component(key: str) -> str:
        return key.split(separator)[0]

    def get_later_components(key: str) -> str:
        return separator.join(key.split(separator)[1:])

    without_more_components = {key: value for key, value in key_values.items() if not get_later_components(key)}

    with_more_components = {key: value for key, value in key_values.items() if get_later_components(key)}

    def grouped_by_first_component(items: ItemsView[str, str]) -> Iterable:
        def by_first_component(item: tuple) -> str:
            return get_first_component(item[0])

        # groupby requires the items to be sorted by the grouping key
        return itertools.groupby(
            sorted(items, key=by_first_component),
            by_first_component,
        )

    def items_with_first_component(items: Iterable, first_component: str) -> dict:
        return {get_later_components(key): value for key, value in items if get_first_component(key) == first_component}

    nested_structured_dict = {
        **without_more_components,
        **{
            first_component: _parse_environment(items_with_first_component(items, first_component))
            for first_component, items in grouped_by_first_component(with_more_components.items())
        },
    }

    def all_keys_are_ints() -> bool:
        def is_int(string: str) -> bool:
            try:
                int(string)
                return True
            except ValueError:
                return False

        return all(is_int(key) for key, value in nested_structured_dict.items())

    def list_sorted_by_int_key() -> list:
        return [value for key, value in sorted(nested_structured_dict.items(), key=lambda key_value: int(key_value[0]))]

    return list_sorted_by_int_key() if all_keys_are_ints() else nested_structured_dict
