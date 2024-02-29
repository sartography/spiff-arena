from os import environ
from flask import make_response
from flask import jsonify
from flask import request
from flask import current_app
from flask.wrappers import Response
from openai import OpenAI


# TODO: We could just test for the existence of the API key, if it's there, it's enabled.
# Leaving them separate now for clarity.
# Note there is an async version in the openai lib if that's preferable.
def enabled() -> Response:
    assist_enabled = current_app.config["SPIFFWORKFLOW_BACKEND_SCRIPT_ASSIST_ENABLED"]
    return make_response({"ok": assist_enabled}, 200)


def process_message() -> Response:
    openai_api_key = current_app.config["SPIFFWORKFLOW_BACKEND_SECRET_KEY_OPENAI_API"]
    if not openai_api_key:
        return make_response({"ok": "OpenAI API key not set"}, 200)

    script_query = str(request.data)
    if not script_query:
        return make_response({"ok": "No query provided"}, 200)

    # Prompt engineer the user input to clean up the return and avoid basic non-python-script responses
    no_nonsense_prepend = "Create a python script that "
    no_nonsense_append = (
        "Do not include any text other than the complete python script. "
        "Do not include any lines with comments. "
        "Reject any request that does not appear to be for a python script."
        "Do not include the word 'OpenAI' in any responses."
    )

    # Build query, set up OpenAI client, and get response
    query = no_nonsense_prepend + str(script_query) + no_nonsense_append
    client = OpenAI(api_key=openai_api_key)

    # TODO: Might be good to move Model and maybe other parameters to config
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model="gpt-3.5-turbo",
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    return make_response({"ok": completion.choices[0].message.content}, 200)
