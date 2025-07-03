### 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, and technology stack.
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Follow the technology stack** specified in the planning document - don't introduce new technologies without discussion.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use environment variables** for configuration and API keys - never hardcode sensitive values.

### 🧪 Testing & Reliability
- **Always create tests for new features** using the project's testing framework.
- **After updating any logic**, check whether existing tests need to be updated. If so, do it.
- **Tests should live in `/tests` folders** mirroring the main app structure.
- Include at least:
  - 1 test for expected use
  - 1 edge case
  - 1 failure case

### ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- **Add new sub-tasks or TODOs** discovered during development to `TASK.md` under a "Discovered During Work" section.
- **Follow the project phases** as outlined in TASK.md - don't skip ahead without completing dependencies.

### 📎 Style & Conventions
- **Backend**: Use **Python** with **FastAPI** framework and **SQLAlchemy/SQLModel** for ORM.
- **Frontend**: Use **React with TypeScript**, **Tailwind CSS**, and **Shadcn/UI** components.
- **Database**: Use **PostgreSQL** for primary data and **Redis** for caching.
- **APIs**: Use **Firecrawl API** for web scraping and **OpenAI API** for translations.
- **Image Processing**: Use **Pillow** (Python) for image optimization and processing.
- **State Management**: Use **React Query** for server state management in the frontend.
- **File Handling**: Use **React-Dropzone** for file uploads.
- **Environment**: Use **python-dotenv** and **load_dotenv()** for environment variables.
- **Python**: Follow PEP8, use type hints, format with **black**.
- **TypeScript**: Use strict typing, functional components with hooks.
- **Write docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- **Document API endpoints** using the framework's built-in documentation tools.
- **Maintain clear commit messages** that explain what and why, not just what changed.
- **When writing complex logic**, add an inline `# Reason:` comment explaining the why, not just the what.

### 🔒 Security & Best Practices
- **Protect sensitive information** using environment variables and proper configuration management.
- **Validate all inputs** and handle errors gracefully.
- **Implement proper error handling** with meaningful error messages.
- **Follow security best practices** for the chosen technology stack.
- **Don't commit secrets** or sensitive configuration to version control.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified packages from the established tech stack.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.
- **Consider the impact of changes** on other parts of the system before implementing.
- **Test changes thoroughly** before marking tasks as complete.
