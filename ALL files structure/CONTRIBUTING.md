# Contributing to Quickfix

First off, thank you for considering contributing to Quickfix! It's people like you that make Quickfix such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [riteshkumar90359@gmail.com](mailto:riteshkumar90359@gmail.com).

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

**Bug Report Template:**
```markdown
**Description**
A clear and concise description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Node Version: [e.g., 18.17.0]
- Python Version: [e.g., 3.10.0]

**Additional Context**
Any other context about the problem.
```

### 💡 Suggesting Features

Feature suggestions are welcome! Please provide:

**Feature Request Template:**
```markdown
**Problem Statement**
Describe the problem this feature would solve.

**Proposed Solution**
Describe your proposed solution.

**Alternatives Considered**
Describe alternative solutions you've considered.

**Additional Context**
Any other context, mockups, or examples.
```

### 🔧 Code Contributions

1. **Fork the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/customer-complaint-agent_new.git
   cd customer-complaint-agent_new
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make Your Changes**
   - Write clean, readable code
   - Follow coding standards
   - Add tests if applicable
   - Update documentation

4. **Test Your Changes**
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd frontend
   npm test
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "✨ Add amazing feature"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

---

## Development Setup

### Prerequisites

- Node.js 16+
- Python 3.10+
- PostgreSQL 15+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python init_db.py

# Run tests
pytest

# Run with auto-reload
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies (if not in package.json)
npm install --save-dev @testing-library/react @testing-library/jest-dom

# Create .env file
cp .env.example .env

# Run development server
npm run dev

# Run tests
npm test

# Run linter
npm run lint

# Build for production
npm run build
```

---

## Coding Standards

### Python (Backend)

**Style Guide:** Follow [PEP 8](https://pep8.org/)

```python
# Good
def process_complaint(complaint_text: str) -> dict:
    """
    Process a customer complaint using AI agents.
    
    Args:
        complaint_text: The complaint text to process
        
    Returns:
        Dictionary containing AI analysis results
    """
    result = orchestrator.process(complaint_text)
    return result


# Bad
def processComplaint(text):
    result=orchestrator.process(text)
    return result
```

**Key Points:**
- Use type hints
- Write docstrings for functions and classes
- Use meaningful variable names
- Keep functions small and focused
- Maximum line length: 88 characters (Black formatter)

**Tools:**
```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

### JavaScript/React (Frontend)

**Style Guide:** Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

```javascript
// Good
const ComplaintForm = ({ onSubmit, loading }) => {
  const [complaint, setComplaint] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await onSubmit(complaint);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form content */}
    </form>
  );
};

// Bad
function ComplaintForm(props) {
  var complaint = '';
  
  function submit(e) {
    e.preventDefault()
    props.onSubmit(complaint)
  }
  
  return <form onSubmit={submit}></form>
}
```

**Key Points:**
- Use functional components with hooks
- Use const/let, never var
- Use arrow functions
- Use meaningful component and variable names
- Keep components small and focused
- Use PropTypes or TypeScript

**Tools:**
```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint -- --fix

# Format code (if Prettier is configured)
npm run format
```

### CSS

```css
/* Good */
.complaint-card {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  border-radius: 0.5rem;
  background: var(--card-background);
}

.complaint-card__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* Bad */
.cc {
  display: flex;
  padding: 20px;
}

.cc h2 {
  font-size: 20px;
}
```

**Key Points:**
- Use BEM naming convention
- Use CSS variables for colors and spacing
- Mobile-first responsive design
- Avoid !important unless absolutely necessary

---

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **✨ feat**: New feature
- **🐛 fix**: Bug fix
- **📝 docs**: Documentation changes
- **💄 style**: Code style changes (formatting, etc.)
- **♻️ refactor**: Code refactoring
- **⚡ perf**: Performance improvements
- **✅ test**: Adding or updating tests
- **🔧 chore**: Build process or auxiliary tool changes
- **🔥 remove**: Removing code or files
- **🚀 deploy**: Deployment related changes

### Examples

```bash
# Good commits
git commit -m "✨ feat(auth): add Google OAuth integration"
git commit -m "🐛 fix(api): resolve CORS issue in production"
git commit -m "📝 docs: update installation instructions"
git commit -m "♻️ refactor(agents): simplify orchestrator logic"
git commit -m "⚡ perf(cache): implement Redis caching layer"

# Bad commits
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "changes"
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No console errors or warnings
- [ ] Tested on multiple browsers (if frontend)

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes.

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] Added tests
- [ ] All tests passing
- [ ] No new warnings
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainer reviews code
3. **Feedback**: Address any requested changes
4. **Approval**: PR approved by maintainer
5. **Merge**: PR merged into main branch

---

## Project Structure

```
customer-complaint-agent_new/
├── frontend/           # React frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── styles/     # CSS files
│   │   └── api.js      # API client
│   └── package.json
│
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── agents/     # AI agents
│   │   ├── routes/     # API routes
│   │   ├── db/         # Database models
│   │   └── services/   # Business logic
│   └── requirements.txt
│
└── docs/               # Documentation
```

---

## Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_classifier
```

### Frontend Testing

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- ComplaintForm.test.jsx
```

---

## Documentation

### Code Documentation

**Python:**
```python
def classify_complaint(text: str) -> str:
    """
    Classify a complaint into a category.
    
    Args:
        text: The complaint text to classify
        
    Returns:
        The classified category (e.g., "Billing", "Technical")
        
    Raises:
        ValueError: If text is empty
        APIError: If Gemini API fails
        
    Example:
        >>> classify_complaint("My bill is wrong")
        'Billing'
    """
    pass
```

**JavaScript:**
```javascript
/**
 * Submit a complaint to the backend API
 * 
 * @param {string} complaint - The complaint text
 * @param {number} userId - The user ID
 * @returns {Promise<Object>} The API response with AI analysis
 * @throws {Error} If API request fails
 * 
 * @example
 * const result = await submitComplaint("Issue with order", 123);
 */
const submitComplaint = async (complaint, userId) => {
  // Implementation
};
```

### README Updates

When adding new features, update:
- Feature list
- API documentation
- Configuration section
- Examples

---

## Getting Help

- 📧 **Email**: [riteshkumar90359@gmail.com](mailto:riteshkumar90359@gmail.com)
- 💬 **GitHub Discussions**: [Start a discussion](https://github.com/RiteshKumar2e/customer-complaint-agent_new/discussions)
- 🐛 **Issues**: [Report an issue](https://github.com/RiteshKumar2e/customer-complaint-agent_new/issues)

---

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project documentation

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Quickfix! 🎉**
