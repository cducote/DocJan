"""
AI operations for document merging, similarity detection, and other ML tasks.
"""
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from config.settings import OPENAI_API_KEY

# Initialize embedding model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


def merge_documents_with_ai(main_doc, similar_doc):
    """
    Merge two similar documents using AI to create a combined document
    that preserves the most important information from both.
    
    Args:
        main_doc: Primary document object with page_content and metadata
        similar_doc: Similar document to merge with the main document
        
    Returns:
        str: The merged document content
    """
    try:
        # Read the prompt template
        with open("prompts/merge_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Replace placeholders
        prompt = prompt_template.replace("{{title_a}}", main_doc.metadata.get("title", "Untitled"))
        prompt = prompt.replace("{{title_b}}", similar_doc.metadata.get("title", "Untitled"))
        prompt = prompt.replace("{{url_a}}", main_doc.metadata.get("source", "No URL"))
        prompt = prompt.replace("{{url_b}}", similar_doc.metadata.get("source", "No URL"))
        prompt = prompt.replace("{{content_a}}", main_doc.page_content)
        prompt = prompt.replace("{{content_b}}", similar_doc.page_content)
        
        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
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
