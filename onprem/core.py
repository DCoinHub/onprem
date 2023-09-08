# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['DEFAULT_MODEL_URL', 'DEFAULT_LARGER_URL', 'DEFAULT_EMBEDDING_MODEL', 'LLM']

# %% ../nbs/00_core.ipynb 3
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import GPT4All, LlamaCpp
import chromadb
import os
import warnings
from typing import Any, Dict, Generator, List, Optional, Tuple, Union


# %% ../nbs/00_core.ipynb 4
from . import utils as U
DEFAULT_MODEL_URL = 'https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGML/resolve/main/Wizard-Vicuna-7B-Uncensored.ggmlv3.q4_0.bin'
DEFAULT_LARGER_URL = ' https://huggingface.co/TheBloke/WizardLM-13B-V1.2-GGML/resolve/main/wizardlm-13b-v1.2.ggmlv3.q4_0.bin'
DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

class LLM:
    def __init__(self, 
                 model_url=DEFAULT_MODEL_URL,
                 n_gpu_layers:Optional[int]=None, 
                 model_download_path:Optional[str]=None,
                 max_tokens:int=512, 
                 n_ctx:int=2048, 
                 n_batch:int=1024,
                 mute_stream=False,
                 embedding_model_name:str ='sentence-transformers/all-MiniLM-L6-v2',
                 embedding_model_kwargs:dict ={'device': 'cpu'},
                 use_larger=False,
                 confirm=True,
                 verbose=False):
        """
        LLM Constructor
        
        **Args:**

        - *model_url*: URL to `.bin` model (currently must be GGML model).
        - *n_gpu_layers*: Number of layers to be loaded into gpu memory. Default is `None`.
        - *model_download_path*: Path to download model. Default is `onprem_data` in user's home directory.
        - *max_tokens*: The maximum number of tokens to generate.
        - *n_ctx*: Token context window.
        - *n_batch*: Number of tokens to process in parallel.
        - *mute_stream*: Mute ChatGPT-like token stream output during generation
        - *embedding_model*: name of sentence-transformers model. Used for `LLM.ingest` and `LLM.ask`.
        - *embedding_model_kwargs*: arguments to embedding model (e.g., `{device':'cpu'}`).
        - *use_larger**: If True, a larger model than the default `model_url` will be used.
        - *confirm*: whether or not to confirm with user before downloading a model
        - *verbose*: Verbosity
        """
        self.model_url = DEFAULT_LARGER_URL if use_larger else model_url
        if verbose:
            print(f'Since use_larger=True, we are using: {os.path.basename(DEFAULT_LARGER_URL)}')
        self.model_name = os.path.basename(self.model_url)
        self.model_download_path = model_download_path
        if not os.path.isfile(os.path.join(U.get_datadir(), self.model_name)):
            self.download_model(self.model_url, model_download_path=self.model_download_path, confirm=confirm)
        self.llm = None
        self.ingester = None
        self.n_gpu_layers = n_gpu_layers
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.callbacks = [] if mute_stream else [StreamingStdOutCallbackHandler()]
        self.embedding_model_name = embedding_model_name
        self.embedding_model_kwargs = embedding_model_kwargs
        self.verbose = verbose
 
    @classmethod
    def download_model(cls, model_url=DEFAULT_MODEL_URL, model_download_path:Optional[str]=None, confirm=True, ssl_verify=True):
        """
        Download an LLM in GGML format supported by [lLama.cpp](https://github.com/ggerganov/llama.cpp).
        
        **Args:**
        
        - *model_url*: URL of model
        - *model_download_path*: Path to download model. Default is `onprem_data` in user's home directory.
        - *confirm*: whether or not to confirm with user before downloading
        - *ssl_verify*: If True, SSL certificates are verified. 
                        You can set to False if corporate firewall gives you problems.
        """
        datadir = model_download_path or U.get_datadir()
        model_name = os.path.basename(model_url)
        filename = os.path.join(datadir, model_name)
        confirm_msg = f"You are about to download the LLM {model_name} to the {datadir} folder. Are you sure?"
        if os.path.isfile(filename):
            confirm_msg = f'There is already a file {model_name} in {datadir}.\n Do you want to still download it?'
            
        shall = True
        if confirm:
            shall = input("%s (Y/n) " % confirm_msg) == "Y"
        if shall:
            U.download(model_url, filename, verify=ssl_verify)
        else:
            warnings.warn(f'{model_name} was not downloaded because "Y" was not selected.')
        return

    def load_ingester(self):
        """Get Ingester instance"""
        if not self.ingester:
            from onprem.ingest import Ingester
            self.ingester = Ingester(embedding_model_name=self.embedding_model_name,
                                     embedding_model_kwargs=self.embedding_model_kwargs)
        return self.ingester
        
        
    def ingest(self, 
               source_directory:str,
              ):
        """
        Ingests all documents in `source_folder` into vector database.
        Previously-ingested documents are ignored.

        **Args:**
        
        - *source_directory*: path to folder containing document store

        
        **Returns:** `None`
        """
        ingester = self.load_ingester()
        ingester.ingest(source_directory)
        return

 
        
    def check_model(self):
        datadir = self.model_download_path or U.get_datadir()
        model_path = os.path.join(datadir, self.model_name)
        if not os.path.isfile(model_path):
            raise ValueError(f'The LLM model {self.model_name} does not appear to have been downloaded. '+\
                             f'Execute the download_model() method to download it.')
        return model_path
        
 
    def load_llm(self):
        model_path = self.check_model()
        
        if not self.llm:
            self.llm =  llm = LlamaCpp(model_path=model_path, 
                                       max_tokens=self.max_tokens, 
                                       n_batch=self.n_batch, 
                                       callbacks=self.callbacks, 
                                       verbose=self.verbose, 
                                       n_gpu_layers=self.n_gpu_layers, 
                                       n_ctx=self.n_ctx)    

        return self.llm
        
        
    def prompt(self, prompt, prompt_template=None):
        """
        Send prompt to LLM to generate a response
        """
        llm = self.load_llm()
        if prompt_template:
            prompt = prompt_template.format(**{'prompt': prompt})
        return llm(prompt)  
    
    def ask(self, question, num_source_docs=4):
        """
        Answer a question based on source documents fed to the `ingest` method.
        
        **Args:**
        
        - question: a question you want to ask
        - num_source_docs: the number of ingested source documents use to generate answer
        """
        ingester = self.load_ingester()
        db = ingester.get_db()
        if not db:
            raise ValueError('A vector database has not yet been created. Please call the LLM.ingest method.')
        retriever = db.as_retriever(search_kwargs={"k": num_source_docs})
        llm = self.load_llm()
        qa = RetrievalQA.from_chain_type(llm=llm, 
                                         chain_type="stuff", 
                                         retriever=retriever, 
                                         return_source_documents= True)
        res = qa(question)
        return res['result'], res['source_documents']
