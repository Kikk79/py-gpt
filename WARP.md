# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PyGPT is a comprehensive desktop AI assistant written in Python that provides direct interaction with multiple language models including GPT-4, Claude, Gemini, and local models via Ollama. The application features a Qt-based GUI, extensive plugin system, multiple operation modes (chat, agents, assistants, etc.), and supports both local and cloud-based AI models.

**Key Technologies**: Python 3.10+, PySide6/Qt, LlamaIndex, OpenAI SDK, Anthropic SDK, Google GenAI SDK

## Quick Start Commands

### Development Setup
```bash
# Clone and setup (if not already done)
git clone https://github.com/szczyglis-dev/py-gpt.git
cd py-gpt

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Alternative: Poetry setup
pip install poetry
poetry env use python3.10
poetry shell
poetry install
```

### Running the Application
```bash
# Standard run
python3 run.py

# Development with debug logging
python3 run.py --debug=1     # INFO level
python3 run.py --debug=2     # DEBUG level

# Force legacy mode (for WebEngine issues)
python3 run.py --legacy=1

# Disable GPU acceleration
python3 run.py --disable-gpu=1

# Custom work directory
python3 run.py --workdir=/path/to/custom/workdir
```

### Testing
```bash
# Run all tests
pytest tests

# Run tests with verbose output
pytest -vv

# Run specific test file
pytest tests/core/test_config.py

# Using the test runner script (Linux/Mac)
./run-tests.sh
```

### Build and Distribution
```bash
# Build using PyInstaller (Linux)
./bin/build.sh

# Build Windows installer
./bin/build_installer.bat

# Clean build artifacts
./bin/clean.sh

# Build documentation
cd docs
make html         # Linux/Mac
make.bat html     # Windows
```

### Resource Management
```bash
# Compile Qt resources
./bin/resources.sh    # Linux/Mac
./bin/resources.bat   # Windows

# Minify JavaScript
./bin/minify.sh
```

## Architecture Overview

### High-Level Structure
PyGPT follows a modular MVC-like architecture:

- **UI Layer** (`src/pygpt_net/ui/`): Qt-based interface components
- **Controller Layer** (`src/pygpt_net/controller/`): Business logic and event handling
- **Core Layer** (`src/pygpt_net/core/`): Core business logic and data management
- **Provider Layer** (`src/pygpt_net/provider/`): External service integrations (LLMs, vector stores, etc.)
- **Plugin System** (`src/pygpt_net/plugin/`): Extensible functionality modules

### Key Components

#### Application Entry Points
- **`run.py`**: Main entry point, imports from `src/pygpt_net/app.py`
- **`src/pygpt_net/app.py`**: Application setup and plugin/provider registration
- **`src/pygpt_net/launcher.py`**: Application launcher with argument parsing and Qt setup

#### Core Systems
- **Context Management**: Conversation history and memory (`src/pygpt_net/core/ctx/`)
- **Model Management**: LLM provider abstraction (`src/pygpt_net/core/models/`)
- **Plugin System**: Extensible architecture for adding features
- **Agent Framework**: Multiple agent implementations (LlamaIndex, OpenAI Agents)
- **Vector Store Integration**: LlamaIndex-based document indexing and retrieval

#### Data Flow
1. UI events trigger controller methods
2. Controllers interact with core business logic
3. Core logic may call providers (LLMs, vector stores, etc.)
4. Plugins can intercept and modify the flow
5. Results flow back through the stack to update the UI

## Directory Structure

### Core Directories
- **`src/pygpt_net/`**: Main application source code
  - **`controller/`**: MVC controllers for different features (chat, agents, etc.)
  - **`core/`**: Core business logic, data models, and services
  - **`ui/`**: Qt-based user interface components
  - **`plugin/`**: Built-in plugins for extending functionality
  - **`provider/`**: Service providers (LLMs, vector stores, audio, etc.)
  - **`tools/`**: Standalone tools (indexer, code interpreter, etc.)
  - **`item/`**: Data models and entities
  - **`data/`**: Static data files and configurations

### Configuration & Resources
- **`bin/`**: Build scripts and utilities
- **`docs/`**: Documentation source files (Sphinx-based)
- **`tests/`**: Test suite (pytest-based)
- **`examples/`**: Example plugins and extensions

### Important Files
- **`pyproject.toml`**: Poetry configuration and project metadata
- **`setup.py`**: Python package setup configuration
- **`requirements.txt`**: Python dependencies for pip
- **`linux.spec`**: PyInstaller specification for Linux builds

## Plugin Development

### Plugin Architecture
Plugins extend PyGPT's functionality through a well-defined interface:

```python
from pygpt_net.plugin.base.plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super(MyPlugin, self).__init__()
        self.id = "my_plugin"
        self.name = "My Plugin"
        
    def handle(self, event, *args, **kwargs):
        # Handle plugin events
        pass
```

### Key Plugin Types
- **Command Plugins**: Add new chat commands (e.g., file operations, web search)
- **Audio Plugins**: Speech input/output processing
- **Integration Plugins**: External service integrations (GitHub, Google, etc.)
- **Agent Plugins**: Autonomous behavior and task execution
- **Vision Plugins**: Image processing and analysis

### Adding Custom Plugins
1. Create plugin class extending `BasePlugin`
2. Implement required methods (`handle`, `setup_events`, etc.)
3. Register in `src/pygpt_net/app.py` or via custom launcher
4. Use `examples/custom_launcher.py` as a template

## Development Patterns

### Provider Pattern
External services are abstracted through providers:
- **LLM Providers**: OpenAI, Anthropic, Google, Ollama, etc.
- **Vector Store Providers**: ChromaDB, Pinecone, Elasticsearch, etc.
- **Audio Providers**: Whisper, Azure TTS, Google TTS, etc.

### Event System
The application uses an event-driven architecture for communication between components.

### Configuration Management
- **Global Config**: `src/pygpt_net/core/config/`
- **User Workdir**: Runtime configuration and data storage
- **Profile System**: Multiple user profiles with separate configurations

## Testing Strategy

### Test Structure
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Mock Objects**: `tests/mocks.py` provides test doubles
- **Fixtures**: `tests/conftest.py` sets up test environment

### Running Tests
```bash
# All tests
pytest

# Specific test patterns
pytest tests/core/
pytest -k "test_config"

# Coverage reporting
pytest --cov=src/pygpt_net tests/
```

## Common Development Tasks

### Adding a New LLM Provider
1. Create provider class in `src/pygpt_net/provider/llms/`
2. Extend `BaseLLM` class
3. Implement required methods (`chat`, `completion`, etc.)
4. Register in `app.py`

### Adding a New Plugin
1. Create plugin in `src/pygpt_net/plugin/`
2. Extend `BasePlugin` class
3. Implement event handlers
4. Add to plugin registration in `app.py`

### Debugging and Logging
- Use `--debug=1` or `--debug=2` command line flags
- Logs are written to `app.log` in the user's workdir
- Debug classes available in `src/pygpt_net/core/debug/`

### Database and Migrations
- SQLite database for context storage (`db.sqlite` in workdir)
- Migration system in `src/pygpt_net/migrations/`
- Context and attachment data persistence

## Security Considerations

### API Key Management
- API keys stored in user workdir, not in source code
- Support for environment variables
- Per-provider key configuration

### Sandbox Execution
- Code interpreter supports Docker sandbox mode
- IPython kernel isolation for code execution
- File system access controls through plugins

## Performance Notes

### Memory Management
- Context chunking for large conversations
- Vector store optimization for large document sets
- Qt resource management and pixmap caching

### Scalability
- Async/await patterns for API calls
- Streaming support for real-time responses
- Efficient token usage calculation

## Troubleshooting

### Common Issues
- **Qt/WebEngine problems**: Use `--legacy=1` flag
- **GPU issues**: Use `--disable-gpu=1` flag  
- **Audio problems on Linux**: Install `portaudio19-dev`, `libasound2`
- **Snap permissions**: Connect required interfaces (`pygpt:camera`, `pygpt:audio-record`)

### Debug Configuration
- Enable debug logging with `--debug=2`
- Check `app.log` in workdir for detailed logs
- Use Qt debugging environment variables for WebEngine issues

## External Dependencies

### Core Dependencies
- **PySide6**: Qt-based GUI framework
- **LlamaIndex**: Document indexing and retrieval
- **OpenAI SDK**: GPT model integration
- **Anthropic SDK**: Claude model integration
- **Google GenAI SDK**: Gemini model integration

### Optional Dependencies
- **Docker**: For sandboxed code execution
- **FFmpeg**: Audio/video processing
- **Various API SDKs**: For plugin integrations (GitHub, Google services, etc.)

This architecture enables a highly extensible desktop AI assistant with plugin-based functionality, multi-modal capabilities, and support for numerous AI providers and services.