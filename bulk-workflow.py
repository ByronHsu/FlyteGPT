from flytekit import task, workflow, Resources
from flytekit.types.file import FlyteFile
import torch
import time
from ingest_data import load_and_split_documents, embed_and_vectorize_documents
from query_documents import get_chain
from typing import List

@task(
    requests=Resources(cpu="16", mem="240Gi", gpu="6"),
    limits=Resources(cpu="16", mem="240Gi", gpu="6"),
)
def ingest() -> FlyteFile:
    documents = load_and_split_documents()
    vectorstore = embed_and_vectorize_documents(documents)
    torch.save(vectorstore, "./vectorstore.pt")

    return FlyteFile("./vectorstore.pt")

def query(vectorstore_file: FlyteFile, questions: List[str]):
    vectorstore = torch.load(vectorstore_file)
    qa_chain = get_chain(vectorstore)
    chat_history = []
    for question in questions:
        result = qa_chain({"question": question, "chat_history": chat_history})
        chat_history.append((question, result["answer"]))
        print("AI:")
        print(result["answer"])

@workflow
def workflow():
    vectorstore_file = ingest()
    query(vectorstore_file, ["what is flytekit?", "how to use ray on flyte?"])