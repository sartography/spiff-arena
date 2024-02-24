from flask import make_response
from flask.wrappers import Response
from flask import current_app as app
from openai import OpenAI

# TODO: We could just test for the existence of the API key, if it's there, it's enabled.
# Leaving them separate now for clarity.
# Note there is an async version in the openai lib if that's preferable.
def enabled() -> Response:
    response = app.config["SCRIPT_ASSIST_ENABLED"]
    return make_response({"ok": response}, 200)

def process_message() -> Response:
    openai_api_key = app.config["SPIFFWORKFLOW_BACKEND_OPENAI_API_KEY"]

    no_nonsense = "Do not include any text other than the complete python script. Do not include any comments. Reject any request that does not appear to be for a python script."

    client = OpenAI(api_key=openai_api_key)

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "create a python script that says hello world {}".format(no_nonsense),
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

