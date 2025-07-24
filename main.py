# main.py

from langchain_community.document_loaders import ConfluenceLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import os

# Load environment variables from .env file
load_dotenv()

# 1. Set up credentials from environment variables
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")

# 2. Load documents from Confluence
loader = ConfluenceLoader(
    url=CONFLUENCE_BASE_URL,
    username=CONFLUENCE_USERNAME,
    api_key=CONFLUENCE_API_TOKEN,
    space_key="SD",
    limit=25
)

# Load documents
docs = loader.load()

# 3. Create embeddings instance for similarity detection
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 4. Detect similar documents before chunking
print(f">> Analyzing {len(docs)} documents for similarity...")
print(">> Generating embeddings for similarity detection...")

# Generate embeddings for full documents (not chunks yet)
doc_embeddings = []
for doc in docs:
    embedding = embeddings.embed_query(doc.page_content)
    doc_embeddings.append(embedding)

# Calculate similarity matrix and find similar pairs
# Convert to numpy array for easier computation
embedding_matrix = np.array(doc_embeddings)
similarity_matrix = cosine_similarity(embedding_matrix)

# Find similar document pairs above threshold
similarity_threshold = 0.65  # Lowered from 0.75 to catch more pairs
similar_pairs = []
similar_docs_metadata = {}

print(f">> Using similarity threshold: {similarity_threshold}")
print(">> Found similar document pairs:")

for i in range(len(docs)):
    for j in range(i + 1, len(docs)):
        similarity_score = similarity_matrix[i][j]
        if similarity_score >= similarity_threshold:
            title_i = docs[i].metadata.get('title', f'Document {i+1}')
            title_j = docs[j].metadata.get('title', f'Document {j+1}')
            
            similar_pairs.append((i, j, similarity_score))
            print(f"  >> Pair {len(similar_pairs)}: '{title_i}' <-> '{title_j}' (similarity: {similarity_score:.3f})")
            
            # Add metadata to track similar documents
            doc_i_id = f"doc_{i}"
            doc_j_id = f"doc_{j}"
            
            if doc_i_id not in similar_docs_metadata:
                similar_docs_metadata[doc_i_id] = []
            if doc_j_id not in similar_docs_metadata:
                similar_docs_metadata[doc_j_id] = []
            
            similar_docs_metadata[doc_i_id].append(doc_j_id)
            similar_docs_metadata[doc_j_id].append(doc_i_id)

# Add similar document metadata to each document
for i, doc in enumerate(docs):
    doc_id = f"doc_{i}"
    if doc_id in similar_docs_metadata:
        # Convert list to comma-separated string for ChromaDB compatibility
        doc.metadata['similar_docs'] = ','.join(similar_docs_metadata[doc_id])
        doc.metadata['doc_id'] = doc_id
    else:
        doc.metadata['similar_docs'] = ''
        doc.metadata['doc_id'] = doc_id

print(f">> Summary: Found {len(similar_pairs)} similar document pairs")
if len(similar_pairs) != 5:
    print(f">> Expected 5 pairs, got {len(similar_pairs)}. Consider adjusting similarity_threshold (currently {similarity_threshold})")
else:
    print(">> Perfect! Found exactly 5 pairs as expected")

# 5. Split long documents into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
split_docs = splitter.split_documents(docs)

# 6. Store vectors in Chroma
print(f">> Processing {len(docs)} documents from Confluence...")
print(f">> Split into {len(split_docs)} chunks")
print(">> Creating embeddings and storing in vector database...")

db = Chroma.from_documents(split_docs, embeddings, persist_directory="./chroma_store")

print(">> All documents have been embedded and stored in ChromaDB!")
print(f">> Vector database location: ./chroma_store")
print(f">> Total chunks embedded: {len(split_docs)}")

# Print summary of loaded documents
print("\n>> Documents loaded:")
for i, doc in enumerate(docs, 1):
    title = doc.metadata.get('title', 'Unknown')
    content_length = len(doc.page_content)
    print(f"  {i}. {title} ({content_length} characters)")
