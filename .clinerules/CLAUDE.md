### 🚨 MANDATORY TASK COMPLETION WORKFLOW
**BEFORE starting any new task:**
- [ ] Read current task from TASK.md
- [ ] Understand dependencies and requirements
- [ ] Verify all prerequisite tasks are marked complete

**DURING task execution:**
- [ ] Check off individual subtasks in TASK.md as they are completed
- [ ] Add any discovered subtasks to "Discovered During Work" section
- [ ] Update TASK.md immediately after completing each subtask

**AFTER completing ANY subtask:**
- [ ] IMMEDIATELY update TASK.md with completion status
- [ ] Add completion notes if significant work was done
- [ ] Verify all dependencies are met before moving to next task

**BEFORE claiming task completion:**
- [ ] Double-check ALL subtasks are marked complete in TASK.md
- [ ] Add completion timestamp and summary notes
- [ ] Document any deviations or additional work done
- [ ] Mark main task as ✅ COMPLETED with date

### 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, and technology stack.
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Follow the technology stack** specified in the planning document - don't introduce new technologies without discussion.
- **Follow the 7-Step Development Workflow** for all development tasks (automated via MCP server):
  1. Planning Phase (PLANNING.md + TASK.md)
  2. Feature Specification (features/taskX.md)
  3. PRP Generation (PRPs/taskX.md) - *Auto-creates review file*
  4. PRP Review (PRPs/taskX-review.md) - *Quality validation before execution*
  5. PRP Execution - *Auto-creates completion file*
  6. Task Completion (PRPs/taskX-completion.md) - *Structured completion verification*
  7. Documentation Sync - *Update all relevant documentation*
- **Templates are automatically applied** by the MCP server during PRP generation and execution.
- **PRP Review is mandatory** - all PRPs must be reviewed before execution for quality validation.
- **PRP Completion is mandatory** - all executed PRPs must have completion documentation.
- **Maintain interface documentation** in `docs/interfaces/` when implementing new features.

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
- **Mark completed tasks in `TASK.md`** immediately after finishing them using the simplified format below.
- **Add new sub-tasks or TODOs** discovered during development to `TASK.md` under a "Discovered During Work" section.
- **Follow the project phases** as outlined in TASK.md - don't skip ahead without completing dependencies.
- **Use brief completion notes** in TASK.md (2-3 lines max) - detailed technical documentation goes in completion files.

#### Simplified TASK.md Completion Format
```markdown
### Task X: Task Name ✅ COMPLETED (YYYY-MM-DD)
- [x] Subtask 1
- [x] Subtask 2
- [x] Subtask 3

**Completion Notes**: Brief summary of what was accomplished (1-2 sentences max)
**Next**: Dependencies met for Task Y / Ready for next phase
**Discovered During Work**: Any new items found (if applicable)
```

### 🚨 CRITICAL WORKFLOW RULES
- **NEVER proceed to a new task without marking the previous task complete in TASK.md**
- **NEVER claim a task is finished without updating TASK.md first**
- **NEVER use attempt_completion without verifying TASK.md is updated**
- **ALWAYS pause after each subtask completion to update TASK.md**

### ✅ COMPLETION VERIFICATION CHECKLIST
Before using attempt_completion or claiming any task is done:
- [ ] All subtasks marked complete in TASK.md with [x]
- [ ] Any new discoveries added to "Discovered During Work" section
- [ ] Completion timestamp added (YYYY-MM-DD format)
- [ ] Completion notes documenting what was accomplished
- [ ] Next task dependencies verified as met
- [ ] Main task marked as ✅ COMPLETED with date

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
