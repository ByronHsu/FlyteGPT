from langchain.document_loaders import ReadTheDocsLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
import pickle
from langchain.document_loaders import GitLoader, SlackDirectoryLoader
from langchain.text_splitter import CharacterTextSplitter, PythonCodeTextSplitter
import re
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.faiss import FAISS
from typing import Any

def get_documents_from_slack_data(path):
    loader = SlackDirectoryLoader(zip_path=path)
    raw_documents = loader.load()
    text_splitter = CharacterTextSplitter()
    documents = text_splitter.split_documents(raw_documents)
    print(f"Loaded {len(documents)} documents from {path}")
    return documents


def python_path_filter(path: str):
    pattern = r'^(?!.*mock)(?!.*test).*\.(py)$'
    regex = re.compile(pattern)
    match = bool(regex.match(path))
    return match

def get_documents_from_python_data(path):
    loader = GitLoader(repo_path=path, branch="master", file_filter=python_path_filter)
    raw_documents = loader.load()
    text_splitter = PythonCodeTextSplitter()
    documents = text_splitter.split_documents(raw_documents)
    print(f"Loaded {len(documents)} documents from {path}")
    return documents

class GolangTextSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along Golang (*.go) syntax."""

    def __init__(self, **kwargs: Any):
        """Initialize a GolangTextSplitter."""
        separators = [
            # Split along function definitions
            "\nfunc ",
            "\nvar ",
            "\nconst ",
            "\ntype ",
            # Split along control flow statements
            "\nif ",
            "\nfor ",
            "\nswitch ",
            "\ncase ",
            # Split by the normal type of lines
            "\n\n",
            "\n",
            " ",
            "",
        ]
        super().__init__(separators=separators, **kwargs)

def golang_path_filter(path: str):
    pattern = r'^(?!.*mock)(?!.*test).*\.(go)$'
    regex = re.compile(pattern)
    match = bool(regex.match(path))
    return match

def get_documents_from_golang_data(path):
    loader = GitLoader(repo_path=path, branch="master", file_filter=golang_path_filter)
    raw_documents = loader.load()
    text_splitter = GolangTextSplitter()
    documents = text_splitter.split_documents(raw_documents)
    print(f"Loaded {len(documents)} documents from {path}")
    return documents

class RSTTextSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along reStructuredText (*.rst) syntax."""

    def __init__(self, **kwargs: Any):
        """Initialize an RSTTextSplitter."""
        separators = [
            # Split along section titles
            "\n===\n",
            "\n---\n",
            "\n***\n",
            # Split along directive markers
            "\n.. ",
            # Split by the normal type of lines
            "\n\n",
            "\n",
            " ",
            "",
        ]
        super().__init__(separators=separators, **kwargs)

def rst_path_filter(path: str):
    pattern = r'^(?!.*mock)(?!.*test).*\.(rst)$'
    regex = re.compile(pattern)
    match = bool(regex.match(path))
    return match

def get_documents_from_rst_data(path):
    loader = GitLoader(repo_path=path, branch="master", file_filter=rst_path_filter)
    raw_documents = loader.load()
    text_splitter = RSTTextSplitter()
    documents = text_splitter.split_documents(raw_documents)
    print(f"Loaded {len(documents)} documents from {path}")
    return documents

class ProtoTextSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along Protocol Buffer (*.proto) syntax."""

    def __init__(self, **kwargs: Any):
        """Initialize a ProtoTextSplitter."""
        separators = [
            # Split along message definitions
            "\nmessage ",
            # Split along service definitions
            "\nservice ",
            # Split along enum definitions
            "\nenum ",
            # Split along option definitions
            "\noption ",
            # Split along import statements
            "\nimport ",
            # Split along syntax declarations
            "\nsyntax ",
            # Split by the normal type of lines
            "\n\n",
            "\n",
            " ",
            "",
        ]
        super().__init__(separators=separators, **kwargs)

def proto_path_filter(path: str):
    pattern = r'^(?!.*mock)(?!.*test).*\.(proto)$'
    regex = re.compile(pattern)
    match = bool(regex.match(path))
    return match

def get_documents_from_proto_data(path):
    loader = GitLoader(repo_path=path, branch="master", file_filter=proto_path_filter)
    raw_documents = loader.load()
    text_splitter = ProtoTextSplitter()
    documents = text_splitter.split_documents(raw_documents)
    print(f"Loaded {len(documents)} documents from {path}")
    return documents
    

def load_and_split_documents():
    slack_documents = get_documents_from_slack_data("./data/flyte-slack-data.zip")
    python_documents = get_documents_from_python_data("./data/flytekit")
    golang_documents = get_documents_from_golang_data("./data/flyteplugins") + get_documents_from_golang_data("./data/flytepropeller") + get_documents_from_golang_data("./data/flyteadmin")
    rst_documents = get_documents_from_rst_data("./data/flyte")
    proto_documents = get_documents_from_proto_data("./data/flyteidl")
    return slack_documents + python_documents + golang_documents + rst_documents + proto_documents

def embed_and_vectorize_documents(documents):
    embeddings = HuggingFaceEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

if __name__ == "__main__":
    load_and_split_documents()