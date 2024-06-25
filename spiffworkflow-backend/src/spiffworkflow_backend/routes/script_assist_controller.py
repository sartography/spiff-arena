import requests
from flask import current_app
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError


# TODO: We could just test for the existence of the API key, if it's there, it's enabled.
# Leaving them separate now for clarity.
# Note there is an async version in the openai lib if that's preferable.
def enabled() -> Response:
    assist_enabled = current_app.config["SPIFFWORKFLOW_BACKEND_SCRIPT_ASSIST_ENABLED"]
    return make_response(jsonify({"ok": assist_enabled}), 200)


def process_message(body: dict) -> Response:
    openai_api_key = current_app.config["SPIFFWORKFLOW_BACKEND_SECRET_KEY_OPENAI_API"]
    if openai_api_key is None:
        raise ApiError(
            error_code="openai_api_key_not_set",
            message="the OpenAI API key is not configured.",
        )

    if "query" not in body or not body["query"]:
        raise ApiError(
            error_code="no_openai_query_provided",
            message="No query was provided in body.",
        )

    # Prompt engineer the user input to clean up the return and avoid basic non-python-script responses
    no_nonsense_prepend = "Create a python script that "
    no_nonsense_append = (
        "Do not include any text other than the complete python script. "
        "Do not include any lines with comments. "
        "Reject any request that does not appear to be for a python script. "
        "Do not include the word 'OpenAI' in any responses. "
        "Do not use print statements, but instead assign results to new variables. "
    )

    # Build query, set up OpenAI client, and get response
    query = no_nonsense_prepend + str(body["query"]) + no_nonsense_append
    headers = {"Authorization": f"Bearer {openai_api_key}"}

    payload = {
        # other reasonable options include gpt-4o (more expensive, better)
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": query}],
        # temerature controls the randomness of predictions. A lower temperature (e.g., 0.5) can help produce more deterministic
        # outputs, which is useful for generating precise code.
        "temperature": 0.5,
        "max_tokens": 256,
        # top_p determines the diversity of the model's outputs. A lower value (e.g., 0.5) focuses the model on producing more
        # likely tokens, which can be beneficial for generating coherent code snippets.
        "top_p": 0.5,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
    response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    completion = response.json()["choices"][0]["message"]["content"]

    return make_response(jsonify({"result": completion}), 200)
