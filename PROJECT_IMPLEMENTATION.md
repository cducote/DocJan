# DocJan Project Implementation Guide

*Last Updated: August 14, 2025*

## 🏗️ Project Overview

DocJan is a document management and duplicate detection system that ingests content from Confluence and SharePoint, processes it through AI embeddings, and provides intelligent duplicate detection capabilities. The system uses a modern full-stack architecture with FastAPI backend, Next.js frontend, and ChromaDB for vector storage.

## 📋 Current Architecture

### Backend Stack
- **FastAPI**: Python web framework with async support
- **ChromaDB**: Vector database for document embeddings and metadata storage
- **OpenAI**: Embedding generation and AI processing
- **JSON Files**: Simple file-based storage for merge operations tracking
- **Docker**: Containerization

### Frontend Stack
- **Next.js 14+**: React framework with App Router
- **Clerk**: Authentication and organization management
- **Tailwind CSS**: Styling framework
- **TypeScript**: Type safety

### Infrastructure
- **AWS EKS**: Kubernetes orchestration
- **AWS ECR**: Container registry
- **AWS LoadBalancer**: Service exposure
- **Terraform**: Infrastructure as code

## 🔄 Current Implementation Status

### ✅ Completed Features

#### Authentication & Authorization
- Clerk integration for user authentication
- Organization-based multi-tenancy
- JWT token handling between frontend and backend
- Protected routes and API endpoints

#### Data Ingestion
- Confluence API integration
- SharePoint API integration (partial)
- Background processing with async workers
- Document chunking and preprocessing

#### Vector Processing
- OpenAI embedding generation
- ChromaDB storage and retrieval
- Semantic similarity search
- Duplicate detection algorithms

#### User Interface
- Dashboard with ingestion controls
- Document count and status display
- Organization selection workflow
- Theme support (dark/light)

#### DevOps & Deployment
- Docker containerization with AMD64 support
- Kubernetes deployment manifests
- ECR image registry
- Enhanced deployment script with smart rebuild detection

### 🚧 Partially Implemented Features

#### Enhanced Logging
- **Status**: Implemented but needs production validation
- **Location**: Enhanced in `services/main.py`
- **Features**: Startup environment validation, detailed connection status, verbose background processing
- **Next**: Test logging output in production environment

#### SharePoint Integration
- **Status**: Basic structure exists, needs completion
- **Location**: `sharepoint/api.py`
- **Missing**: Full authentication flow, document parsing
- **Next**: Complete integration following Confluence pattern

#### Database Schema
- **Status**: PostgreSQL models defined but not actively used
- **Location**: `models/database.py`, `models/pg_versioning.py`
- **Current Reality**: Using ChromaDB for all data storage and JSON files for merge tracking
- **Missing**: Decision on whether to implement PostgreSQL or remove the unused code
- **Next**: Either implement PostgreSQL integration or clean up unused PostgreSQL code

### ❌ Known Issues & Technical Debt

#### Data Isolation Problem
- **Issue**: ChromaDB doesn't isolate data between organizations
- **Impact**: Cross-organization data contamination
- **Current Workaround**: Manual database cleanup between tests
- **Solution Needed**: Implement collection-based isolation per organization

#### Deployment Complexity
- **Issue**: Manual image tag management, disk space constraints
- **Impact**: Deployment failures, operational overhead
- **Current Status**: Smart deployment script implemented
- **Solution Needed**: Automated tagging, resource monitoring

#### Local Development Flow
- **Issue**: Complex setup, environment inconsistencies
- **Impact**: Developer onboarding friction
- **Solution Needed**: Docker Compose setup, unified environment

## 🛠️ Development Workflow

### Current Local Testing Process

1. **Environment Setup**
```bash
# Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database setup
# Start ChromaDB (embedded mode)
# Configure environment variables
```

2. **Backend Testing**
```bash
# Start FastAPI server
uvicorn services.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/connection-status
```

3. **Frontend Testing**
```bash
cd nextjs
npm install
npm run dev
# Access http://localhost:3000
```

4. **Integration Testing**
- Test document ingestion through UI
- Verify duplicate detection
- Check organization isolation

### Current Production Deployment

1. **Build Process**
```bash
# Smart deployment (recommended)
./scripts/deploy.sh --deploy-only <existing-tag>

# Force rebuild
./scripts/deploy.sh --force-build <new-tag>

# Regular deployment
./scripts/deploy.sh <tag>
```

2. **Deployment Verification**
```bash
kubectl get pods -l app=concatly-api
kubectl logs -f deployment/concatly-api
```

## 🎯 Priority Issues to Resolve

### 1. Data Isolation (HIGH PRIORITY)
**Problem**: Organizations see each other's documents
**Solution**: Implement ChromaDB collection-based isolation
```python
# Target implementation
collection_name = f"org_{organization_id}"
collection = chroma_client.create_collection(collection_name)
```

### 2. Local Development Environment (HIGH PRIORITY)
**Problem**: Complex local setup process
**Solution**: Create Docker Compose configuration
```yaml
# docker-compose.yml target
services:
  backend:
    build: .
    ports: ["8000:8000"]
  frontend:
    build: ./nextjs
    ports: ["3000:3000"]
  chromadb:
    image: chromadb/chroma
    ports: ["8001:8000"]
```

### 3. Production Logging & Monitoring (MEDIUM PRIORITY)
**Problem**: Limited visibility into production issues
**Status**: Enhanced logging implemented, needs validation
**Solution**: Deploy enhanced logging version and establish monitoring

### 4. Automated Testing (MEDIUM PRIORITY)
**Problem**: No automated test suite
**Solution**: Implement unit tests, integration tests, E2E tests
```bash
# Target test structure
tests/
  unit/
    test_ai_merging.py
    test_confluence_api.py
  integration/
    test_ingestion_flow.py
  e2e/
    test_user_workflows.py
```

### 5. CI/CD Pipeline (LOW PRIORITY)
**Problem**: Manual deployment process
**Solution**: GitHub Actions workflow
```yaml
# .github/workflows/deploy.yml target
- Build and test
- Deploy to staging
- Run E2E tests
- Deploy to production
```

## 📚 Code Organization

### Backend Structure
```
services/
├── main.py              # FastAPI app, enhanced logging
├── confluence_service.py # Confluence integration
├── vector_store.py      # ChromaDB operations
└── config.py           # Configuration management

ai/
├── merging.py          # Duplicate detection logic

models/
├── database.py         # SQLAlchemy models
└── pg_versioning.py    # Migration system

config/
├── settings.py         # Application settings
└── user_profiles.py    # User configuration
```

### Frontend Structure
```
nextjs/
├── app/
│   ├── page.tsx        # Main dashboard
│   ├── api/           # API routes
│   └── [org-routes]/  # Organization-specific pages
├── components/
│   ├── dashboard-content.tsx  # Main dashboard logic
│   ├── sidebar.tsx           # Navigation
│   └── theme-provider.tsx    # Theme management
└── lib/
    ├── api.ts         # Backend communication
    └── database/      # Database utilities
```

## 🚀 Future Implementation Plan

### Phase 1: Stabilization (Current Branch → Main)
- [ ] Fix data isolation issue
- [ ] Validate enhanced logging in production
- [ ] Complete SharePoint integration
- [ ] Create comprehensive testing suite
- [x] Merge `feature/cloud-terraform-clerk` to `main`

### Phase 2: Developer Experience
- [ ] Docker Compose local environment
- [ ] Automated database migrations
- [ ] Development documentation
- [ ] IDE configuration guides

### Phase 3: Production Readiness
- [ ] CI/CD pipeline implementation
- [ ] Automated deployment to staging
- [ ] Production monitoring setup
- [ ] Error tracking integration
- [ ] Performance optimization

### Phase 4: Feature Enhancement
- [ ] Advanced duplicate detection algorithms
- [ ] Bulk document operations
- [ ] Enhanced search capabilities
- [ ] Export functionality
- [ ] Advanced organization management

## 🔧 Key Configuration Files

### Environment Variables
```bash
# Required for local development
OPENAI_API_KEY=sk-...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# AWS/Production
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
ECR_REPOSITORY=039612881134.dkr.ecr.us-east-1.amazonaws.com/concatly-cluster-api

# Note: PostgreSQL variables exist in requirements.txt but are not actively used
# DATABASE_URL=postgresql://... (not currently implemented)
```

### Deployment Configuration
```bash
# Current working image in production
IMAGE_TAG=amd64

# Kubernetes namespace
NAMESPACE=default

# Cluster configuration
CLUSTER_NAME=concatly-cluster
AWS_REGION=us-east-1
```

## 📝 Development Best Practices

### Git Workflow
1. Create feature branches from `main`
2. Test locally before pushing
3. Use semantic commit messages
4. Squash commits before merging

### Code Quality
1. Run tests before committing
2. Use type hints in Python code
3. Follow ESLint rules in TypeScript
4. Update documentation for API changes

### Deployment Safety
1. Always test in local environment first
2. Use `--deploy-only` for existing images
3. Monitor pod status after deployment
4. Keep rollback plan ready

## 🎯 Success Metrics

### Development Velocity
- [ ] Local setup time < 10 minutes
- [ ] Deployment time < 5 minutes
- [ ] Zero-downtime deployments

### System Reliability
- [ ] 99.9% uptime
- [ ] Error rate < 0.1%
- [ ] Response time < 500ms

### Code Quality
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] Automated code quality checks

---

## 📞 Quick Reference Commands

### Local Development
```bash
# Start backend
uvicorn services.main:app --reload

# Start frontend
cd nextjs && npm run dev

# Run tests
pytest tests/

# Check logs
tail -f logs/app.log
```

### Production Operations
```bash
# Deploy existing image
./scripts/deploy.sh --deploy-only amd64

# Check pod status
kubectl get pods -l app=concatly-api

# View logs
kubectl logs -f deployment/concatly-api

# Emergency rollback
kubectl rollout undo deployment/concatly-api
```

### Debugging
```bash
# Check connection status
curl http://api-url/connection-status

# Test ingestion endpoint
curl -X POST http://api-url/start-sync

# Verify ChromaDB
curl http://localhost:8001/api/v1/collections
```

---

*This document should be updated as the project evolves. Consider it a living guide for the project's implementation and future development.*
