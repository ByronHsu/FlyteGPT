# 🦅🔗 Building Flyte LangChain Bot on Flyte
The Flyte LangChain Bot is designed to ingest documents into a queriable format, query relevant documents based on user questions, and utilize a chat model to generate responses. In this guide, we'll walk through the steps to build the bot on Flyte

## Interesting Results

> Human: what is podtemplate in flytekit?

AI: 

The `PodTemplate` in Flytekit is a configuration used as a base for all Kubernetes Pods to be built on. It can be specified in three ways: (1) through default `PodTemplate` applied on a per-namespace basis, (2) by using the `pod_template` or `pod_template_name` arguments in the `@task` decorator, or (3) by specifying an entire `PodTemplate` as an argument using the `pod_template` argument in the task decorator. The default `PodTemplate` (in Flytepropeller settings) is applied to the task by Flytepropeller as the base configuration. If a `pod_template_name` is specified in the task decorator, this will apply the specified Kubernetes `PodTemplate` resource instead of the default `PodTemplate` from Flytepropeller settings. However, if the `pod_template` argument in the task decorator is used to define an entire `PodTemplate`, it will be applied in addition to the default `PodTemplate`. The fields available in the `PodTemplate` resource, including container-level configuration, are supported in Flyte configuration. The `PodTemplate` can be created at a system-wide configuration level or applied from the same namespace that the Pod will be created in. For more information, refer to this [page](https://docs.flyte.org/en/latest/deployment/configuration/general.html#using-default-k8s-podtemplates).

> Human: Compare flyte and airflow. For machine learning use cases, which one is better? 

AI:
Flyte and Airflow are both workflow automation platforms for machine learning and data processes at scale. However, there are some differences between the two. Airflow is older and more monolithic, with great integrations, while Flyte is more scalable, k8s native, and API first. Flyte also has features like data flow, multiple languages, versioning, backend plugins, a type system, and multi-schedules, which Airflow lacks. Ultimately, the choice between Flyte and Airflow depends on your specific use case and requirements. It's worth noting that Flyte works well for batch inference and event-driven architectures with latency requirements of 1-10 minutes, but for anything faster, inference tools like BentoML may be more suitable.

> Human: My company has configured Flyter Admin server to store flyte data in another S3 bucket/folder. How can we change the flyte config to replace s3://my-s3-bucket/data with the the other bucket/folder that has the necessary permissions?

AI:
To change the Flyte config to replace s3://my-s3-bucket/data with another bucket/folder that has the necessary permissions, you can update the default-env-vars in the values.yaml file or create a config.yaml file in ~/.flyte/sandbox/ with the desired configuration. If you want to use S3 directly instead of the local filesystem when running Flyte tasks locally, this is not currently supported. For more information, you can refer to the Flyte documentation or ask for help in the Flyte community.

> Human: I’m seeing this line in error message of a workflow in the UI [4/4] currentAttempt done. Last Error: USER::[1/1] currentAttempt done. Last Error: USER::Traceback  Where are these two currentAttempt set?

AI:
Unfortunately, we don't have documentation on where the two currentAttempt variables are set in Flyte. However, there is an open issue on GitHub that may provide some insight: https://github.com/flyteorg/flyte/issues/2616.

> Human: how is fast registration implemented?

AI:
Fast registration in Flyte allows users to update workflow code without having to rebuild the entire docker image. This is achieved by zipping up the code, uploading it to the configured blob store using a signed URL, and then prepending a command to the task's normal command. At runtime, the command downloads the archive from the blob store and unzips it to the root of the container's image. The `pyflyte package` command with the `--fast` flag can be used to enable fast registration. It is important to note that registration is a two-step process involving compilation and registration, and separate commands are available for each step. More information can be found in the Flyte documentation.

> Human: provide me step-by-step instruction to run ray on flyte

AI:
To run Ray on Flyte, first install the Flyte backend plugin and then follow the instructions in this guide: <https://blog.flyte.org/ray-and-flyte>. Note that the sandbox environment does not come with Ray installed, so you will need to install it separately. The <https://github.com/flyteorg/flyteplugins/tree/master/go/tasks/plugins/k8s/ray> repository contains all the code for the Flyte plugin for Ray. The `ray_start_params` and `runtime_env` parameters in the `RayJobConfig` both take in dictionaries, which can be populated according to the documentation in the Ray CLI documentation: <https://docs.ray.io/en/latest/cluster/cli.html#ray-start-doc|ray start>. The `address` argument in the `RayJobConfig` is used when you want to submit the Ray job to your own Ray cluster. If the value is None, Flyte will create a Ray cluster in the k8s. For more information on running distributed hyperparameter tuning like Ray Tune, see this guide: <https://docs.flyte.org/en/latest/tutorials/first_example.html>. Additional documentation for the Flytekit Ray plugin can be found here: <https://docs.flyte.org/projects/flytekit/en/latest/plugins/ray.html>. The `ray_start_params` and `runtime_env` dictionaries are not specifically documented in the Flytekit Ray plugin documentation, but they can be populated according to the Ray CLI documentation.

> Human: how to use okta with flyte?

AI:
To use Okta with Flyte, follow the steps outlined in the Okta sample configs section of the Flyte documentation. These steps include creating an authorization server, adding access policies and scopes, and creating integrations for Flytectl and Flytepropeller. After completing these steps, you can direct FlyteAdmin to use the external authorization server by editing the config map. For more information, refer to the Flyte documentation on auth setup and auth migration.


## How Flyte LangChain Bot Works
Before we dive into the building process, let's briefly understand how Flyte LangChain Bot functions:

### A. Ingest documents into a queriable format
- Load documents (document loader): The bot loads documents using a document loader, which can handle various data types.
- Split documents (text splitter): The loaded documents are split into smaller text chunks to facilitate indexing and querying.
- Create embeddings for documents (text embedding model): Text embeddings are generated for the documents using a text embedding model. These embeddings capture the semantic meaning of the text.
- Store the embeddings in a vector store: The generated embeddings are stored in a vector store, such as FAISS, to enable efficient querying.
### B. Query relevant documents by the question and send the context to the chat model
- Get user question: The bot receives a user question as input.
- Look up documents in the index relevant to the question: The bot looks up documents in the index that are relevant to the user's question.
- Construct the prompt from the question + relevant document: The bot constructs a prompt by combining the user's question with the relevant document retrieved from the index.
- Pass the prompt to a model: The constructed prompt is passed to a chat model, such as OpenAI's GPT, to generate a response.
- Get the result: The bot retrieves the response from the chat model and presents it as the answer to the user's question.

## Running on Flyte

Flyte ease the process to run a kubernetes pod on machines. 

1. Build a docker image equipped with developer tools (code-server, jupyterlab, vim, etc)
https://github.com/MaastrichtU-IDS/jupyterlab/blob/8bc639a46ec2213cb909025d98bae4103019d1cd/Dockerfile#L1

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


## Building the Flyte LangChain Bot

To build the Flyte LangChain Bot, follow these steps:

### A. Download the datasets

1. Clone the Flyte repositories from GitHub using the following command:

```bash
./flyte-code-clone.sh
```

2. Download the public data from the Flyte Slack Channel. 

You can reach out to the Flyte community for assistance with accessing this data.


### B. Ingest data
The `ingest_data.py` file contains two crucial functions:

- `load_and_split_documents`: This function loads the datasets using various loaders and splitters based on the data types.
- `embed_and_vectorize_documents`: This function uses the HuggingFaceEmbedding model to embed the loaded documents and vectorizes them using FAISS.

### C. Query data

The `query_documents.py` file utilizes the `start_conversation` function to retrieve the vector representing the user's question and interacts with the OpenAI chat model.

### D. Combine everything in a notebook

The main.ipynb notebook serves as the entry point to call the above Python modules and build the Flyte LangChain Bot.


## References

1. https://docs.langchain.com/docs/use-cases/qa-docs
2. https://github.com/hwchase17/chat-langchain-readthedocs
