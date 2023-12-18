import os.path
from llama_index import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    load_index_from_storage,
    VectorStoreIndex,
    ServiceContext
)
from llama_index.readers import GithubRepositoryReader
from llama_index.llms import OpenAI
import openai

from llama_index import download_loader
download_loader("GithubRepositoryReader")

from llama_hub.github_repo import GithubRepositoryReader, GithubClient

test_folder = "/Users/miguel/Edu/alpha-dash-aws"

llm = OpenAI(temperature=0.1, model="gpt-4")
service_context = ServiceContext.from_defaults(llm=llm)

def generate_index_from_folder(folder, persist=True):
   reader = SimpleDirectoryReader(folder)
   docs = reader.load_data()
   index = VectorStoreIndex.from_documents(docs, service_context=service_context)
   if persist:
        index.storage_context.persist()
   return index

def get_index():
    # check if storage already exists
    if not os.path.exists("./storage"):
        return None
    
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    index = load_index_from_storage(storage_context)
    return index

def generate_index(persist=True):
    # load the documents and create the index
    ## This is currently failing, I believe it's due to Rate Limitting by GitHub
    github_client = GithubClient(os.getenv("GITHUB_TOKEN"))
    loader = GithubRepositoryReader(
        github_client,
        owner =                  "trilogy-group",
        repo =                   "alpha-dash-aws",
        filter_file_extensions = ([".ts", ".md", ".sql", ".py"], GithubRepositoryReader.FilterType.INCLUDE),
        verbose =                True,
        concurrent_requests =    10,
    )

    docs = loader.load_data(branch="main")
    index = VectorStoreIndex.from_documents(docs)

    # store it for later
    if persist:
        index.storage_context.persist()

    return index

def index_response_to_prompt(results):
    THRESHOLD = 0.5
    for node in results.source_nodes:
        if node.score > THRESHOLD:
            final_prompt = final_prompt + "\n\n***CONTEXT***\n" + node.text + f"\n***SOURCE:*** File: {node.metadata['file_name']}, page{node.metadata['page_label']}\n"

if __name__ == "__main__":
    index = get_index()
    if index is None:
        index = generate_index_from_folder(test_folder)

    # query the index
    query_engine = index.as_query_engine()
    results = query_engine.query("What is the process for running unit tests?")
    print("Query Engine Response:")
    print(str(results))