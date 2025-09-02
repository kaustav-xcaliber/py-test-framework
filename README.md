# API Test Framework (Python)

A comprehensive HTTP API testing framework built with Python, featuring test management, execution, and detailed reporting capabilities. This is a complete Python conversion of the original Go framework.

## 🚀 Features

- **Service Management**: Add, edit, and manage microservices for testing
- **Test Case Management**: Create and manage HTTP test cases with JSON specifications
- **Test Execution**: Execute tests using httpx with comprehensive assertions
- **Result Tracking**: Track test runs and individual test results with detailed metrics
- **REST API**: Complete REST API for frontend integration
- **Redis Integration**: Job queue and caching support
- **PostgreSQL**: Persistent storage for all test data
- **Detailed Reporting**: Comprehensive test execution reports and analytics
- **Curl Import**: Create tests directly from curl commands
- **Authentication Support**: Multiple authentication methods (Bearer, API Key, Basic, OAuth2)

## 🔐 Authentication Support

The framework supports four authentication types for testing secured APIs:

### Bearer Token Authentication

- **Type**: `bearer`
- **Required Fields**: `token`
- **Usage**: Automatically adds `Authorization: Bearer <token>` header

### API Key Authentication

- **Type**: `api_key`
- **Required Fields**: `key_name`, `key_value`
- **Usage**: Adds the key as a header or query parameter based on the key name

### Basic Authentication

- **Type**: `basic`
- **Required Fields**: `username`, `password`
- **Usage**: Automatically encodes credentials and adds `Authorization: Basic <encoded>` header

### OAuth2 Authentication

- **Type**: `oauth2`
- **Required Fields**: `client_id`, `client_secret`, `token_url`
- **Usage**: Automatically acquires access tokens using client credentials flow

### Example Usage

```python
# Create authentication configuration
auth_config = {
    "type": "bearer",
    "token": "your-jwt-token-here"
}

# Create service with authentication
service = {
    "name": "Secured API",
    "base_url": "https://api.example.com",
    "auth_config": auth_config
}

# Test execution automatically applies authentication
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                API Test Framework (Python)                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Service   │  │    Test     │  │   Test      │        │
│  │ Management  │  │ Management  │  │ Execution   │        │
│  │  Service    │  │  Service    │  │  Service    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                              │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │ PostgreSQL  │  │    Redis    │                         │
│  │  Database   │  │   Cache     │                         │
│  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.104.1
- **Python Version**: 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis
- **HTTP Testing**: httpx + pytest
- **Validation**: Pydantic
- **Documentation**: Automatic OpenAPI/Swagger generation

## 📊 Reporting & Analytics

### Test Execution Reports

The framework provides comprehensive reporting capabilities for test execution:

#### 1. Test Run Summary

- **Execution Status**: Running, Completed, Failed, Cancelled
- **Test Counts**: Total, Passed, Failed
- **Performance Metrics**: Execution time, Response times
- **Timestamps**: Start time, completion time, duration

#### 2. Individual Test Results

- **Test Case Details**: Name, description, service
- **Execution Status**: Passed, Failed
- **Performance Data**: Response time, request/response size
- **Error Details**: Error messages, stack traces
- **Response Data**: Full response payload for analysis

#### 3. Historical Analytics

- **Trend Analysis**: Test success rates over time
- **Performance Trends**: Response time patterns
- **Failure Analysis**: Common failure patterns
- **Service Health**: Service reliability metrics

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd py-framework
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/api_test_framework
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=api_test_framework
DATABASE_USER=postgres
DATABASE_PASSWORD=password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

This will start:

- PostgreSQL database on port 5432
- Redis on port 6379
- PgAdmin on port 5050 (admin/admin)
- API server on port 8000

### 5. Run Locally (Alternative)

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Run migrations (if using Alembic)
alembic upgrade head

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **PgAdmin**: http://localhost:5050

## 📚 API Usage

### 1. Create a Service

```bash
curl -X POST "http://localhost:8000/api/v1/services/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "User Service",
    "description": "User management microservice",
    "base_url": "https://api.users.com",
    "is_active": true
  }'
```

### 2. Create a Test Case from Curl

```bash
curl -X POST "http://localhost:8000/api/v1/tests/from-curl" \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "your-service-id",
    "name": "Get User Test",
    "description": "Test user retrieval endpoint",
    "curl_command": "curl -X GET https://api.users.com/users/123 -H 'Authorization: Bearer token'"
  }'
```

### 3. Execute Test Run

```bash
curl -X POST "http://localhost:8000/api/v1/test-runs/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "test_case_ids": ["test-case-id-1", "test-case-id-2"],
    "test_run_name": "User Service Test Run"
  }'
```

### 4. Get Test Results

```bash
curl "http://localhost:8000/api/v1/test-runs/{test_run_id}/results"
```

## 🔧 Configuration

### Environment Variables

| Variable       | Description                  | Default                                                            |
| -------------- | ---------------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://username:password@localhost:5432/api_test_framework` |
| `REDIS_URL`    | Redis connection string      | `redis://localhost:6379/0`                                         |
| `DEBUG`        | Enable debug mode            | `true`                                                             |
| `LOG_LEVEL`    | Logging level                | `INFO`                                                             |
| `SECRET_KEY`   | Application secret key       | `your-secret-key-here`                                             |
| `HOST`         | Server host                  | `0.0.0.0`                                                          |
| `PORT`         | Server port                  | `8000`                                                             |
| `WORKERS`      | Number of worker processes   | `4`                                                                |

### Test Execution Settings

| Variable                  | Description                        | Default |
| ------------------------- | ---------------------------------- | ------- |
| `MAX_CONCURRENT_TESTS`    | Maximum concurrent test executions | `10`    |
| `TEST_TIMEOUT_SECONDS`    | Test execution timeout             | `300`   |
| `DEFAULT_REQUEST_TIMEOUT` | HTTP request timeout               | `30`    |

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run with specific markers
pytest -m "unit"
pytest -m "integration"
```

### Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_services.py     # Service management tests
├── test_tests.py        # Test case management tests
├── test_test_runs.py    # Test execution tests
└── test_utils.py        # Utility function tests
```

## 🔌 Extending the Framework

### Adding New Assertion Types

The framework supports extensible assertion types. You can add new assertion types by extending the `TestExecutor` class:

```python
# In app/testrunner/executor.py

def _assert_custom(self, assertion: Dict[str, Any], response: httpx.Response) -> Dict[str, Any]:
    """Custom assertion implementation."""
    # Your custom assertion logic here
    pass

def _run_single_assertion(self, assertion: Dict[str, Any], response: httpx.Response) -> Dict[str, Any]:
    assertion_type = assertion.get("type", "unknown")

    if assertion_type == "custom":
        return self._assert_custom(assertion, response)
    # ... existing assertion types
```

### Adding New Authentication Methods

Authentication methods can be extended by adding new types to the `AuthConfig` model and implementing the corresponding logic in the test executor.

### Custom Test Reporters

You can implement custom test reporters by extending the test execution pipeline and adding new output formats.

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:

   ```bash
   export DEBUG=false
   export LOG_LEVEL=WARNING
   export SECRET_KEY=your-production-secret-key
   ```

2. **Database Migration**:

   ```bash
   alembic upgrade head
   ```

3. **Run with Gunicorn**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Docker Production

```bash
# Build production image
docker build -t api-test-framework:latest .

# Run production container
docker run -d \
  -p 8000:8000 \
  -e DEBUG=false \
  -e DATABASE_URL=your-production-db-url \
  -e REDIS_URL=your-production-redis-url \
  api-test-framework:latest
```

## 📈 Monitoring and Health Checks

### Health Endpoints

- `GET /health` - Basic application health
- `GET /health/db` - Database connection health
- `GET /health/redis` - Redis connection health

### Metrics

The framework provides various metrics for monitoring:

- Test execution success rates
- Response time distributions
- Service availability
- Database connection status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black app/ tests/

# Run linting
flake8 app/ tests/

# Run type checking
mypy app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **Original Go Framework**: The Go-based version this framework was converted from
- **Frontend**: React-based web interface (coming soon)
- **CLI Tool**: Command-line interface for test execution (coming soon)

## 📞 Support

- **Documentation**: [API Documentation](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

## 🚧 Roadmap

### Phase 1 (Current)

- ✅ Core framework structure
- ✅ Service management
- ✅ Test case management
- ✅ Basic test execution
- ✅ Health checks

### Phase 2 (Next)

- 🔄 Authentication system
- 🔄 Advanced assertions
- 🔄 Test scheduling
- 🔄 Email notifications

### Phase 3 (Future)

- 📋 Test templates
- 📋 Performance testing
- 📋 Load testing
- 📋 CI/CD integration

---

