# 🦅🔗 Building FlyteGPT on Flyte with LangChain

Flyte is the best example of [deep modules](https://www.mattduck.com/2021-04-a-philosophy-of-software-design.html). The user interface is amazingly simple, but the implementation is deeply complicated. As a active contributor of Flyte, I usually help answering questions in our slack channel. The answer of common questions can mostly be found in the slack history, but for the new questions, I usually have to deep dive into the source code to figure out. 

As time has gone by, I feel like I'm becoming a Flyte GPT myself, constantly looking up information and providing answers. I've come up with a wild idea: why not build a Flyte GPT on Flyte itself?


## Demo

Before we start, let's look at some impressing Q&A result.


> Human: Compare flyte and airflow. For machine learning use cases, which one is better? 

AI:
Flyte and Airflow are both workflow automation platforms for machine learning and data processes at scale. However, there are some differences between the two. Airflow is older and more monolithic, with great integrations, while Flyte is more scalable, k8s native, and API first. Flyte also has features like data flow, multiple languages, versioning, backend plugins, a type system, and multi-schedules, which Airflow lacks. Ultimately, the choice between Flyte and Airflow depends on your specific use case and requirements. It's worth noting that Flyte works well for batch inference and event-driven architectures with latency requirements of 1-10 minutes, but for anything faster, inference tools like BentoML may be more suitable.

> Human: how is fast registration implemented?

AI:
Fast registration in Flyte allows users to update workflow code without having to rebuild the entire docker image. This is achieved by zipping up the code, uploading it to the configured blob store using a signed URL, and then prepending a command to the task's normal command. At runtime, the command downloads the archive from the blob store and unzips it to the root of the container's image. The `pyflyte package` command with the `--fast` flag can be used to enable fast registration. It is important to note that registration is a two-step process involving compilation and registration, and separate commands are available for each step. More information can be found in the Flyte documentation.

I am extremely amazed by how deep FlyteGPT understands Flyte. The answers are not only accurate, but also offer abundant context for users to easily understand. 


## How FlyteGPT works

LangChain provides a great abstraction and makes building FlyteGPT easy. There are mainly two steps: Ingestion and Query.

### 1. Ingest documents into a queriable format
- Load documents (document loader): The bot loads documents using a document loader, which can handle various data types.
- Split documents (text splitter): The loaded documents are split into smaller text chunks to facilitate indexing and querying.

```python
def get_documents_from_slack_data(path):
    loader = SlackDirectoryLoader(zip_path=path)
    raw_documents = loader.load()
    text_splitter = CharacterTextSplitter()
    documents = text_splitter.split_documents(raw_documents)
    print(f"Loaded {len(documents)} documents from {path}")
    return documents
```

- Create embeddings for documents (text embedding model): Text embeddings are generated for the documents using a text embedding model. These embeddings capture the semantic meaning of the text.
- Store the embeddings in a vector store: The generated embeddings are stored in a vector store, such as FAISS, to enable efficient querying.

```python
def embed_and_vectorize_documents(documents):
    embeddings = HuggingFaceEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore
```

### 2. Query relevant documents by the question and send the context to the chat model

- Get user question: The bot receives a user question as input.
- Look up documents in the index relevant to the question: The bot looks up documents in the index that are relevant to the user's question.
- Construct the prompt from the question + relevant document: The bot constructs a prompt by combining the user's question with the relevant document retrieved from the index.
- Pass the prompt to a model: The constructed prompt is passed to a chat model, such as OpenAI's GPT, to generate a response.
- Get the result: The bot retrieves the response from the chat model and presents it as the answer to the user's question.

```python
def get_chain(vectorstore):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm,
        vectorstore.as_retriever(search_kwargs={"k": 20}),
        condense_question_prompt=CONDENSE_QUESTION_PROMPT,
        combine_docs_chain_kwargs={'prompt': QA_PROMPT},
    )
    return qa_chain

def start_conversation(vectorstore):
    qa_chain = get_chain(vectorstore)
    chat_history = []
    print("Chat with your docs!")
    while True:
        print("Human:")
        question = input()
        print(question)
        result = qa_chain({"question": question, "chat_history": chat_history})
        chat_history.append((question, result["answer"]))
        print("AI:")
        print(result["answer"])
```
## Running on Flyte

Flyte provides an simple pythonic interface to run tasks on kubernetes cluster. I can easily configure the resource, image, and cachablity in pure python.

### Development

Check out [dev-workflow](./dev-workflow.py)

In the development stage, I wanted to utilize the GPU nodes in the cluster. To achieve this, I launched a pod that was built with both VSCode and Jupyter Notebook. I then connected to the pod using a browser-based interface.

1. Build a docker image equipped with developer tools (code-server, jupyterlab, vim, etc). Refer to [MaastrichtU-IDS/jupyterlab](https://github.com/MaastrichtU-IDS/jupyterlab/blob/8bc639a46ec2213cb909025d98bae4103019d1cd/Dockerfile#L1)

2. Run a sleeping task with gpu resources (gpu makes embedding much faster)

```python
from flytekit import task, workflow, Resources
import time

@task(
    requests=Resources(cpu="16", mem="240Gi", gpu="6"),
    limits=Resources(cpu="16", mem="240Gi", gpu="6"),
)
def sleep():
    time.sleep(60 * 60 * 24 * 2) # 2 days

@workflow
def workflow():
    sleep()
```

3. Port-forward and connect to the code-server in the pod
4. You can follow [main.ipynb](./main.ipynb) to debug and play with the GPT interactively.

### Bulk Inference

Check out [bulk-workflow](./bulk-workflow.py)

Once we ensure there are no more syntax, dependencies, cuda issues in the development stage, we can move on to bulk inference! To fully leverage Flyte, we can break it down to two tasks: Ingestion and Query. The major benefit of using Flyte is that the task result can be cached. To be more specific, the ingestion phase usually takes a long time, and the task can be **skipped** because of the cache if it was already run before.

```python
@task(
    requests=Resources(cpu="16", mem="240Gi", gpu="6"),
    limits=Resources(cpu="16", mem="240Gi", gpu="6"),
    cache=True,
    cache_version="0.0.0"
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
```

## References

1. https://docs.langchain.com/docs/use-cases/qa-docs
2. https://github.com/hwchase17/chat-langchain-readthedocs
