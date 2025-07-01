# BlameGPT 🔍

> Why is my shiny new feature not on production yet?

Oh... we have deploy blockers!! 

BlameGPT is an AI-powered tool that finds the pull requests begging to be reverted so you can go back to shipping. (Blame the PR, not your coworker. Probably.)

## 🚀 What does BlameGPT do?

BlameGPT uses AI to analyze GitHub issues (particularly deploy blockers) and identifies which pull requests are likely causing the problems. It leverages:

- **LLM embeddings** to understand issue descriptions and PR content
- **GitHub API integration** for seamless repository analysis  
- **Semantic similarity matching** to find relevant PRs
- **Automated blame pipeline** that processes issues and suggests culprit PRs

## 🖼️ Demo

<img src="https://github.com/user-attachments/assets/c049bc22-b194-45ef-b2c7-1e58bd6a999b" height=500>

*Finding the PR causing a deploy blocker*

## 🏗️ Architecture

BlameGPT consists of:

- **Backend**: FastAPI application with RESTful APIs
- **Frontend**: React + TypeScript web interface  
- **Database**: SQLite for storing issues, PRs, and embeddings
- **AI/ML**: OpenAI GPT models for analysis and LangChain for orchestration
- **Integrations**: GitHub webhooks and API for real-time updates

## 📋 Prerequisites

- **Python 3.12+**
- **Node.js 20+** and npm
- **GitHub Personal Access Token** with repo permissions
- **OpenAI API Key** for LLM functionality

## ⚙️ Installation & Setup

### Quick Start (Recommended)

We provide a development helper script to streamline setup:

```bash
# Full setup (install dependencies, format code, build frontend)
./dev.sh setup

# Start development server
./dev.sh dev
```

### Manual Setup

### 1. Clone the repository

```bash
git clone https://github.com/rushatgabhane/blame-gpt.git
cd blame-gpt
```

### 2. Backend Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

Install Node.js dependencies:

```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and configuration:

```env
GITHUB_TOKEN=your_github_personal_access_token
OPENAI_API_KEY=your_openai_api_key
GITHUB_WEBHOOK_SECRET=your_webhook_secret
USER_API_AUTH_TOKEN=your_user_api_token
INTERNAL_API_AUTH_TOKEN=your_internal_api_token
```

## 🚀 Running the Application

### Start the Backend Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Start the Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Production Build

For production deployment:

```bash
# Build frontend
cd frontend
npm run build

# Start backend in production mode
cd ..
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📖 API Documentation

Once the backend is running, you can access:

- **Interactive API docs**: `http://localhost:8000/docs`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

### Key Endpoints

- `POST /api/webhook` - GitHub webhook endpoint for automated processing
- `POST /api/blame/manual/{issue_id}` - Manually trigger blame analysis
- `GET /api/issues` - List processed issues
- `GET /api/deploy-blockers` - Access deploy blocker analysis

## 🔧 Configuration

### GitHub Integration

1. **Personal Access Token**: Create a token with `repo` permissions
2. **Webhook Setup**: Configure webhook URL pointing to `/api/webhook`
3. **Repository Access**: Ensure the token has access to target repositories

> **Note**: Currently, BlameGPT is configured to work with the Expensify/App repository by default. To use it with different repositories, you'll need to modify the constants in `libs/constants.py`.

### OpenAI Configuration

- Set your OpenAI API key in the environment variables
- The application uses GPT models for content analysis and similarity matching
- Costs depend on usage volume and model selection

## 🛠️ Development

### Development Helper Script

We provide a helper script to streamline common development tasks:

```bash
# Full setup
./dev.sh setup

# Start development server  
./dev.sh dev

# Format code
./dev.sh format

# Build frontend
./dev.sh build

# Run linting
./dev.sh lint

# Show help
./dev.sh help
```

### Code Formatting

The project uses Black for Python code formatting:

```bash
black . --line-length=120
```

### Project Structure

```
blame-gpt/
├── controllers/          # FastAPI route handlers
├── frontend/            # React TypeScript frontend
├── libs/                # Shared libraries and utilities
├── middlewares/         # FastAPI middleware
├── models/              # Pydantic data models
├── services/            # Business logic and external integrations
├── main.py              # FastAPI application entry point
├── dev.sh               # Development helper script
└── requirements.txt     # Python dependencies
```

### Database

BlameGPT uses SQLite databases:
- **Core database**: Issues, PRs, embeddings, and relationships
- **Docs database**: Documentation content and embeddings

Databases are automatically initialized on first run.

## 🔧 Troubleshooting

### Common Issues

**GitHub API Connection Error**
```
github.GithubException.GithubException: <exception str() failed>
```
- Ensure `GITHUB_TOKEN` is set in your `.env` file
- Verify the token has proper permissions for the target repository
- Check if the repository configuration in `libs/constants.py` is correct

**OpenAI API Errors**
- Verify `OPENAI_API_KEY` is set correctly
- Check your OpenAI account has sufficient credits
- Ensure you're using a supported model

**Frontend Build Issues**
- Delete `node_modules` and run `npm install` again
- Ensure you're using Node.js 20+
- Check for any TypeScript compilation errors

**Database Connection Issues**
- Ensure the `data/` directory exists and is writable
- Check file permissions for SQLite database files
- Verify no other processes are using the database files

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up your development environment
- Code style and standards
- Testing procedures
- Submitting pull requests

## 📄 License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## 🆘 Support

For support and demos, reach out at [rushatgabhane@gmail.com](mailto:rushatgabhane@gmail.com)

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - Frontend user interface
- [LangChain](https://langchain.com/) - LLM application framework  
- [OpenAI](https://openai.com/) - AI models for analysis
- [GitHub API](https://docs.github.com/en/rest) - Repository integration
