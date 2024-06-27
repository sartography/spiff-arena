# originally from https://mindfulmodeler.substack.com/p/proofreading-an-entire-book-with
# and then modified for our use case.
import sys
import os
import difflib
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
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


def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read()


def split_content(content, chunk_size=13000):
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
    return splitter.split_text(content)


def process_chunk(doc, chat_prompt, retries=3, chunk_index=0):
    for attempt in range(retries):
        result = llm.invoke(chat_prompt.format_prompt(text=doc).to_messages())
        edited_result_content = result.content
        if 0.95 * len(doc) <= len(edited_result_content) <= 1.05 * len(doc):
            return edited_result_content
        print(f"Retry {attempt + 1} for chunk due to size mismatch.")
    raise ValueError("Failed to process chunk after retries.")


def write_to_temp_file(temp_file_path, docs, chat_prompt):
    os.makedirs("/tmp/proof-edits", exist_ok=True)
    with open(temp_file_path, "w") as f:
        for i, doc in enumerate(docs):
            edited_result_content = process_chunk(doc, chat_prompt, chunk_index=i)
            f.write(edited_result_content + "\n")


def analyze_diff(diff_file_path):
    diff_content = read_file(diff_file_path)
    analysis_prompt = f"""
You are an expert technical editor. Please analyze the following diff and ensure it looks like a successful copy edit of a markdown file. Provide feedback if there are any issues or if it looks good, just reply with the single word: good

Diff:
{diff_content}
"""
    result = llm.invoke([HumanMessage(content=analysis_prompt)])
    return result.content


def process_file(input_file):
    content = read_file(input_file)
    docs = split_content(content)
    print(f"Split into {len(docs)} docs")

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_prompt, human_message_prompt]
    )
    os.makedirs("/tmp/proof-edits", exist_ok=True)
    temp_output_file = "/tmp/proof-edits/edited_output.md"

    # Save the original content for diff generation
    original_content = content

    write_to_temp_file(temp_output_file, docs, chat_prompt)

    # Read the edited content
    with open(temp_output_file, "r") as f:
        edited_content = f.read()

    # Generate and save the diff for the whole file
    diff = difflib.unified_diff(
        original_content.splitlines(), edited_content.splitlines(), lineterm=""
    )
    with open("/tmp/proof-edits/diff_file.diff", "w") as diff_file:
        diff_file.write("\n".join(diff))

    # Analyze the diff
    analysis_result = analyze_diff("/tmp/proof-edits/diff_file.diff")

    if analysis_result.lower().strip() == "good":
        os.replace(temp_output_file, input_file)
        print(f"Edited file saved as {input_file}")
    else:
        print(f"The diff looked suspect. Diff analysis result: {analysis_result}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input_file")
    else:
        input_file = sys.argv[1]
        process_file(input_file)
