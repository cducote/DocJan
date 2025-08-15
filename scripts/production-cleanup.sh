#!/bin/bash

# Production cleanup script for ChromaDB
# Usage: ./production-cleanup.sh [list|delete-collection|delete-all] [collection-name]

set -e

NAMESPACE=${NAMESPACE:-default}
APP_LABEL="app=concatly-api"

# Function to get the first available pod
get_pod_name() {
    kubectl get pods -l $APP_LABEL -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

# Function to check if pod exists
check_pod_exists() {
    local pod_count=$(kubectl get pods -l $APP_LABEL --no-headers 2>/dev/null | wc -l)
    if [ "$pod_count" -eq 0 ]; then
        echo "❌ No pods found with label $APP_LABEL"
        echo "💡 Make sure your deployment is running"
        exit 1
    fi
}

# Function to list collections
list_collections() {
    echo "📋 Listing all ChromaDB collections..."
    local pod_name=$(get_pod_name)
    kubectl exec $pod_name -- python -c "
import chromadb
from config.environment import get_chroma_persist_directory

client = chromadb.PersistentClient(path=get_chroma_persist_directory())
collections = client.list_collections()
print(f'Found {len(collections)} collections:')
for i, collection in enumerate(collections, 1):
    doc_count = collection.count()
    print(f'  {i}. {collection.name} ({doc_count} documents)')
"
}

# Function to delete a specific collection
delete_collection() {
    local collection_name="$1"
    if [ -z "$collection_name" ]; then
        echo "❌ Collection name is required"
        echo "Usage: $0 delete-collection <collection-name>"
        exit 1
    fi
    
    echo "🗑️  Deleting collection: $collection_name"
    local pod_name=$(get_pod_name)
    kubectl exec $pod_name -- python -c "
import chromadb
from config.environment import get_chroma_persist_directory

client = chromadb.PersistentClient(path=get_chroma_persist_directory())
try:
    client.delete_collection('$collection_name')
    print('✅ Successfully deleted collection: $collection_name')
except Exception as e:
    print(f'❌ Error deleting collection: {e}')
    exit(1)
"
}

# Function to run interactive cleanup
interactive_cleanup() {
    echo "🔧 Starting interactive cleanup..."
    local pod_name=$(get_pod_name)
    echo "📱 Connecting to pod: $pod_name"
    kubectl exec -it $pod_name -- python cleanup_db.py
}

# Main script logic
check_pod_exists

case "${1:-interactive}" in
    "list")
        list_collections
        ;;
    "delete-collection")
        delete_collection "$2"
        ;;
    "interactive")
        interactive_cleanup
        ;;
    "--help"|"-h")
        echo "Production ChromaDB Cleanup Script"
        echo ""
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  interactive          Start interactive cleanup (default)"
        echo "  list                 List all collections"
        echo "  delete-collection    Delete a specific collection"
        echo ""
        echo "Examples:"
        echo "  $0                                    # Interactive mode"
        echo "  $0 list                               # List collections"
        echo "  $0 delete-collection org_old_data     # Delete specific collection"
        echo ""
        echo "Environment Variables:"
        echo "  NAMESPACE    Kubernetes namespace (default: default)"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 --help' for usage information"
        exit 1
        ;;
esac
