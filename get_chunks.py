from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.utils import set_global_tokenizer
from transformers import AutoTokenizer

# def generate_chunks_context(text_content):
#     # Initialize tokenizer and splitter
#     set_global_tokenizer(AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer"))
#     splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=25)

#     # Create Document objects and split into chunks
#     documents = [Document(text=text) for text in text_content]
#     nodes = splitter.get_nodes_from_documents(documents)
#     chunks = [n.text for n in nodes]
    
#     return chunks[:30]

# Initialize tokenizer and splitter once globally
# or pass them as arguments to the function.
try:
    set_global_tokenizer(AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer"))
except OSError:
    print("Warning: Could not load tokenizer. Using default tokenizer.")
    # Fallback to a default tokenizer if the specified one fails.
    pass

splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=25)

def generate_chunks_context(text_content):

    # Create Document objects
    documents = [Document(text=text) for text in text_content]
    
    # Split documents into nodes (chunks)
    nodes = splitter.get_nodes_from_documents(documents)
    
    # Extract the text from the nodes
    chunks = [n.text for n in nodes]
    
    return chunks[:30]