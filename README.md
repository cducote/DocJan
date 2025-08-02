# DocJaninor 🔍

A Streamlit application for semantic search and AI-powered merging of Confluence documents. This tool helps identify similar documentation pages and intelligently merge them to reduce redundancy and improve content quality.

## Features

### 🔍 Semantic Search
- Search across Confluence documents using natural language queries
- Powered by OpenAI embeddings for accurate semantic matching
- Groups similar documents together automatically
- Shows document previews and metadata

### 🤖 AI-Powered Document Merging
- Identifies similar documents using cosine similarity
- Merges duplicate content using GPT-4o
- Side-by-side document comparison
- Manual editing capabilities for merged content

### 🔄 Confluence Integration
- Automatically updates Confluence pages with merged content
- Deletes duplicate pages to maintain clean documentation
- Preserves page relationships and metadata
- User-friendly interface for selecting which page to keep

## Architecture

### Core Components
- **Vector Database**: ChromaDB for storing document embeddings
- **Embeddings**: OpenAI text-embedding-3-small model
- **AI Model**: GPT-4o for document merging
- **UI Framework**: Streamlit for web interface
- **Confluence API**: Direct integration with Confluence REST API

### Module Structure
```
Concatly/
├── ai/              # AI operations (merging, embeddings)
├── config/          # Application configuration and settings
├── confluence/      # Confluence API integration
├── database/        # Database operations and document management  
├── models/          # Data models and database structures
├── prompts/         # Prompt templates for AI operations
├── ui/              # Streamlit UI components and pages
│   └── pages/       # Individual page renderers
└── utils/           # Utility functions and helpers
```

### Workflow
1. **Document Loading**: Confluence documents are loaded and processed
2. **Similarity Detection**: Documents are analyzed for semantic similarity
3. **Embedding Storage**: Document chunks are embedded and stored in ChromaDB
4. **Search Interface**: Users can search and browse similar document groups
5. **Merge Process**: AI merges similar documents with user oversight
6. **Confluence Update**: Merged content is applied back to Confluence

## Installation

### Prerequisites
- Python 3.8+
- Confluence access with API permissions
- OpenAI API key

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd DocJan
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Configure your `.env` file with:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Confluence Configuration
CONFLUENCE_USERNAME=your_confluence_username
CONFLUENCE_API_TOKEN=your_confluence_api_token
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki

# Database Configuration
CHROMA_DB_DIR=./chroma_store
```

## Usage

### Initial Setup
1. Run the document loader to populate the vector database:
```bash
python main.py
```

2. Start the Streamlit application:
```bash
streamlit run app.py
```

### Using the Application

1. **Search Documents**: Enter search queries to find relevant documents
2. **Review Groups**: Examine grouped similar documents
3. **Merge Documents**: Click "Merge Documents" to compare and merge similar pages
4. **Edit Content**: Use AI merge or manual editing to create final content
5. **Apply Changes**: Choose which Confluence page to keep and apply the merge

## Configuration

### Similarity Detection
- **Threshold**: Adjustable similarity threshold (default: 0.75)
- **Embedding Model**: OpenAI text-embedding-3-small
- **Chunk Size**: 1000 characters with 100 character overlap

### AI Merging
- **Model**: GPT-4o with temperature 0.3
- **Prompt Template**: Customizable in `prompts/merge_prompt.txt`
- **Output Format**: Markdown with Confluence storage conversion

## File Structure

```
DocJan/
├── app.py                 # Main Streamlit application
├── main.py               # Document loader and similarity detection
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── prompts/
    └── merge_prompt.txt # AI merge prompt template
```

## API Integration

### Confluence REST API
- **Authentication**: Basic auth with username/API token
- **Operations**: Read, update, and delete pages
- **Format Conversion**: Markdown to Confluence storage format

### OpenAI API
- **Embeddings**: text-embedding-3-small for semantic search
- **Completion**: GPT-4o for document merging
- **Rate Limiting**: Built-in retry logic

## Security Considerations

- Environment variables for all sensitive credentials
- Private repository recommended for deployment
- API tokens should have minimal required permissions
- Regular credential rotation recommended

## Troubleshooting

### Common Issues

1. **Page ID Extraction Errors**
   - Check Confluence URL formats in debug panel
   - Verify API permissions for content access

2. **Embedding Failures**
   - Verify OpenAI API key and quota
   - Check network connectivity

3. **Confluence API Errors**
   - Confirm API token permissions
   - Verify Confluence base URL format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is private and proprietary. All rights reserved.

## Support

For questions or issues, please contact the development team or create an issue in the repository.

---

**DocJaninor** - Streamlining documentation through intelligent merging 🚀
