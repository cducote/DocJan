"""
AI operations for document merging, similarity detection, and other ML tasks.
"""
import os
import sys
from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Add config directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.environment import get_openai_api_key
    OPENAI_API_KEY = get_openai_api_key()
except ImportError:
    # Fallback to direct environment variable
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize embedding model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)


def merge_documents_with_ai(main_doc, similar_doc, merged_title=None):
    """
    Merge two similar documents using AI to create a combined document
    that preserves the most important information from both.
    
    Args:
        main_doc: Primary document (object with page_content/metadata OR string)
        similar_doc: Similar document to merge (object with page_content/metadata OR string)
        merged_title: Optional title for the merged document
        
    Returns:
        str: The merged document content
    """
    try:
        # Handle both document objects and simple strings
        if hasattr(main_doc, 'page_content'):
            # Document object
            title_a = main_doc.metadata.get("title", "Untitled")
            url_a = main_doc.metadata.get("source", "No URL")
            content_a = main_doc.page_content
        else:
            # Simple string
            title_a = merged_title or "Document A"
            url_a = "No URL"
            content_a = str(main_doc)
        
        if hasattr(similar_doc, 'page_content'):
            # Document object
            title_b = similar_doc.metadata.get("title", "Untitled")
            url_b = similar_doc.metadata.get("source", "No URL")
            content_b = similar_doc.page_content
        else:
            # Simple string
            title_b = merged_title or "Document B"
            url_b = "No URL"
            content_b = str(similar_doc)
        
        # Read the prompt template
        with open("prompts/merge_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Replace placeholders
        prompt = prompt_template.replace("{{title_a}}", title_a)
        prompt = prompt.replace("{{title_b}}", title_b)
        prompt = prompt.replace("{{url_a}}", url_a)
        prompt = prompt.replace("{{url_b}}", url_b)
        prompt = prompt.replace("{{content_a}}", content_a)
        prompt = prompt.replace("{{content_b}}", content_b)
        
        # Call OpenAI
        llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        result = llm.invoke(prompt)
        
        return result.content
    except Exception as e:
        return f"Error during merge: {str(e)}"


def calculate_document_similarity(doc1_embedding, doc2_embedding):
    """
    Calculate cosine similarity between two document embeddings
    
    Args:
        doc1_embedding: Embedding vector for document 1
        doc2_embedding: Embedding vector for document 2
        
    Returns:
        float: Similarity score between 0 and 1
    """
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Reshape embeddings for sklearn
    embedding1 = np.array(doc1_embedding).reshape(1, -1)
    embedding2 = np.array(doc2_embedding).reshape(1, -1)
    
    # Calculate cosine similarity
    similarity = cosine_similarity(embedding1, embedding2)[0][0]
    
    return similarity
