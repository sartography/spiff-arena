# originally from https://mindfulmodeler.substack.com/p/proofreading-an-entire-book-with
# and then modified for our use case.
import sys
import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
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
# - Do not leave any trailing spaces (handled by another script, though)
# - Never remove entire sentences (didn't seem necessary, since we said keep everything else exactly the same)

system_text = """You are proofreading and you will receive text that is almost exactly correct, but may contain errors. You should:

- Fix spelling
- Improve grammar that is obviously wrong
- Fix awkward language if it is really bad
- Keep everything else exactly the same, including tone and voice
- not change the case of words unless they are obviously wrong
- Avoid changing markdown syntax, e.g. keep [@reference]
- Output one line per sentence (same as input)
- Avoid putting multiple sentences on the same line
- Make sure you do not remove any headers at the beginning of the text (markdown headers begin with one or more # characters)
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
    splitter = CharacterTextSplitter(chunk_size=13000, chunk_overlap=0)
    docs = splitter.split_text(content)

    print("Split into {} docs".format(len(docs)))
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_prompt, human_message_prompt]
    )

    os.makedirs("/tmp/proof-edits", exist_ok=True)

    temp_output_file = "/tmp/proof-edits/edited_output.md"
    with open(temp_output_file, "w") as f:
        print(f"working on: {input_file}")
        for i, doc in enumerate(docs):
            result = llm.invoke(chat_prompt.format_prompt(text=doc).to_messages())
            edited_result_content = result.content

            # compare edited_result_content with doc and see if the size is off by more than 5%
            # if it is, try again, up to 3 times
            if len(edited_result_content) > 1.05 * len(doc) or len(
                edited_result_content
            ) < 0.95 * len(doc):
                print(f"{input_file}: Chunk {i} size after edit is off by more than 5%")
                # get basename of input_file and save before and after to tmp for debugging
                basename_of_input_file = os.path.basename(input_file)
                before_filename = (
                    f"/tmp/proof-edits/before_{basename_of_input_file}_{i}.txt"
                )
                after_filename = (
                    f"/tmp/proof-edits/after_{basename_of_input_file}_{i}.txt"
                )
                # save files
                with open(before_filename, "w") as before_f:
                    before_f.write(doc)
                with open(after_filename, "w") as after_f:
                    after_f.write(edited_result_content)
                print(
                    f"Before and after files written to {before_filename} and {after_filename} for comparison."
                )

                for j in range(3):
                    print(f"Trying again {j+1}")
                    result = llm.invoke(
                        chat_prompt.format_prompt(text=doc).to_messages()
                    )
                    edited_result_content = result.content
                    if len(edited_result_content) < 1.05 * len(doc) and len(
                        edited_result_content
                    ) > 0.95 * len(doc):
                        break
                else:
                    raise ValueError(
                        f"Failed to process chunk {i} of {input_file} after 3 retries."
                    )

            if os.environ.get("DEBUG") == "true":
                chunk_file = f"/tmp/proof-edits/chunk_{i}.txt"
                with open(chunk_file, "w") as chunk_f:
                    chunk_f.write(doc)
                print(f"Chunk {i} written to {chunk_file}")
                edited_chunk_file = f"/tmp/proof-edits/edited_chunk_{i}.txt"
                with open(edited_chunk_file, "w") as edited_chunk_f:
                    edited_chunk_f.write(edited_result_content)
                print(f"Edited chunk {i} written to {edited_chunk_file}")
            f.write(edited_result_content + "\n")

    os.replace(temp_output_file, input_file)
    print(f"Edited file saved as {input_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input_file")
    else:
        input_file = sys.argv[1]
        process_file(input_file)
