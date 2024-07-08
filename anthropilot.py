import os
import urllib.parse
from dotenv import load_dotenv
from typing import Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.document_loaders import PyPDFLoader
# from gpt4all import Embed4All
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

load_dotenv()

class CustomStreamingCallbackHandler(BaseCallbackHandler):
    """Callback Handler that Stream LLM response."""
    def __init__(self, queue):
      self.queue = queue

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
      """Run on new LLM token. Only available when streaming is enabled."""
      await self.queue.put(urllib.parse.quote_plus(token))

    def on_llm_start(self, serialized, prompts, **kwargs):
      print(f"LLM Start triggered with prompt")

    async def on_llm_end(self, *args, **kwargs: Any) -> None:
      print("LLM End triggered")
      await self.queue.put("END")

class Anthropilot:
  def __init__(self, open_ai_key, anthropic_key, model_name="claude-3-sonnet-20240229"):
    os.environ["OPENAI_API_KEY"] = open_ai_key
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    self.llm_anthropic = ChatAnthropic(
      streaming=True,
      # model_name="claude-3-opus-20240229",
      model_name=model_name,
      temperature=0,
      timeout=None,
      max_tokens_to_sample=4000,
      api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    self.embedding = GPT4AllEmbeddings(
      model_name = "nomic-embed-text-v1.f16.gguf"
    )

  def create_vector_db_from_text(self, raw_text, vector_db_path):
    text_splitter = RecursiveCharacterTextSplitter(
          separators=['.', '!', '?', '\n'],
          chunk_size=1000,
          chunk_overlap=100
      )
    all_splits = text_splitter.split_text(raw_text)

    embedding = GPT4AllEmbeddings(
      model_name = "nomic-embed-text-v1.f16.gguf"
    )

    vector_store = FAISS.from_texts(texts=all_splits, embedding=embedding)

    vector_store.save_local(vector_db_path)
    return vector_store

  def create_vector_db_from_file(self, file_path, vector_db_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
      separators=['.', '!', '?', '\n'],
      chunk_size=1000,
      chunk_overlap=100
    )

    chunks = text_splitter.split_documents(documents)
    vector_store = FAISS.from_documents(documents=chunks, embedding=self.embedding)
    vector_store.save_local(vector_db_path)
    return vector_store

  def read_vectors_db(self, vector_db_path):
    db = FAISS.load_local(
      vector_db_path,
      self.embedding,
      allow_dangerous_deserialization=True
    )
    return db

  def create_prompt(self, template):
    prompt = PromptTemplate(
      template=template,
      input_variables=["context", "question"]
    )
    return prompt

  def chat(self, question, prompt, db):
    search_kwargs = {
      'k': 1000000,
      'fetch_k':1000000,
      'maximal_marginal_relevance': True,
      'distance_metric': 'cos',
    }

    qa_chain = RetrievalQA.from_chain_type(
      llm = self.llm_anthropic,
      chain_type="stuff",
      retriever=db.as_retriever(search_kwargs=search_kwargs),
      chain_type_kwargs={"prompt": prompt}
    )
    result = qa_chain.invoke({"query": question })

    return result["result"]

  def stream_data(self, question, prompt, db, queue):
    search_kwargs = {
      'k': 30,
      'fetch_k':100,
      'maximal_marginal_relevance': True,
      'distance_metric': 'cos',
    }
    self.llm_anthropic.callbacks = [CustomStreamingCallbackHandler(queue)]
    qa_chain = RetrievalQA.from_chain_type(
      llm = self.llm_anthropic,
      retriever=db.as_retriever(search_kwargs=search_kwargs),
      chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain.stream({"query": question })

