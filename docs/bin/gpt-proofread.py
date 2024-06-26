# originally from https://mindfulmodeler.substack.com/p/proofreading-an-entire-book-with
# and then modified for our use case.
import sys
import os
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import MarkdownTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage

human_template = """
{text}
"""
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

# system_text = """You are an expert technical editor specializing in business process management documentation written for enterprise software users. You are especially good at cutting clutter.
#
# - Improve grammar and language
# - fix errors
# - cut clutter
# - keep tone and voice
# - don't change markdown syntax, e.g. keep [@reference]
# - never cut jokes
# - output 1 line per sentence (same as input)
# """

# style ideas from 24 aug 2023:
# - short and focused
# - clear over fun
# - brief over verbose

system_text = """You are proofreading and you will receive text that is almost exactly correct, but may contain errors. You should:

- Fix spelling
- Improve grammar that is obviously wrong
- Fix awkward language if it is really bad
- keep everything else exactly the same, including tone and voice
- don't change markdown syntax, e.g. keep [@reference]
- Never remove entire sentences
- never cut jokes
- output 1 line per sentence (same as input)
- Do not put multiple sentences on the same line
- Do not leave any trailing spaces
- Make sure you do not remove the first header in a file that begins with a single #
"""

system_prompt = SystemMessage(content=system_text)

openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key is None:
    keyfile = "oai.key"
    with open(keyfile, "r") as f:
        openai_api_key = f.read().strip()

# model = "gpt-4"
model = "gpt-4o"
# model = "gpt-3.5-turbo"

# If you get timeouts, you might have to increase timeout parameter
llm = ChatOpenAI(openai_api_key=openai_api_key, model=model, request_timeout=240)


def process_file(input_file):

    with open(input_file, "r") as f:
        content = f.read()

    # Markdown splitter didn't work so well
    # splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=0)

    # FIXME: actually split
    # splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
    # docs = splitter.split_text(content)
    docs = [content]

    print("Split into {} docs".format(len(docs)))
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_prompt, human_message_prompt]
    )

    with open(input_file, "w") as f:
        for doc in docs:
            print(f"doc: {doc}")
            result = llm(chat_prompt.format_prompt(text=doc).to_messages())
            print(result.content)
            f.write(result.content + "\n")

    print(f"Edited file saved as {input_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input_file")
    else:
        input_file = sys.argv[1]
        process_file(input_file)
