# Contributing to Azure Advisor Reports Platform

Thank you for your interest in contributing to the Azure Advisor Reports Platform! We welcome contributions from the community and are pleased to have you join us.

## 🤝 Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** installed
- **Docker & Docker Compose** installed
- **Git** installed and configured

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork locally:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/azure-advisor-reports.git
   cd azure-advisor-reports
   ```
3. **Set up the development environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your development settings
   docker-compose up -d
   ```

## 🛠️ Development Workflow

### Branch Naming Convention

Use descriptive branch names with the following prefixes:

- `feature/` - New features (e.g., `feature/add-cost-report`)
- `fix/` - Bug fixes (e.g., `fix/csv-parsing-error`)
- `docs/` - Documentation updates (e.g., `docs/update-readme`)
- `refactor/` - Code refactoring (e.g., `refactor/report-generator`)
- `test/` - Adding tests (e.g., `test/add-integration-tests`)

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Write or update tests** for your changes

4. **Run the test suite:**
   ```bash
   # Backend tests
   cd azure_advisor_reports
   pytest --cov=apps

   # Frontend tests
   cd frontend
   npm test
   ```

5. **Ensure code quality:**
   ```bash
   # Python formatting and linting
   black .
   isort .
   flake8 .

   # JavaScript/TypeScript linting
   cd frontend
   npm run lint
   ```

## 📝 Coding Standards

### Python/Django Backend

- **Follow PEP 8** style guide
- **Use Black** for code formatting: `black .`
- **Use isort** for import sorting: `isort .`
- **Use flake8** for linting: `flake8 .`
- **Maximum line length:** 100 characters
- **Write docstrings** for all functions, classes, and modules

#### Code Style Example

```python
from typing import Dict, List, Optional
from django.db import models
from apps.core.models import BaseModel


class Report(BaseModel):
    """
    Represents an Azure Advisor report generated from CSV data.

    Attributes:
        client: The client this report belongs to
        report_type: Type of report (detailed, executive, etc.)
        status: Current processing status
    """

    REPORT_TYPES = [
        ('detailed', 'Detailed Report'),
        ('executive', 'Executive Summary'),
        ('cost', 'Cost Optimization'),
        ('security', 'Security Assessment'),
        ('operations', 'Operational Excellence'),
    ]

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='detailed'
    )
    status = models.CharField(
        max_length=20,
        default='pending'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Azure Advisor Report'
        verbose_name_plural = 'Azure Advisor Reports'

    def __str__(self) -> str:
        return f"{self.client.company_name} - {self.get_report_type_display()}"
```

### React/TypeScript Frontend

- **Use TypeScript** for all new components
- **Follow Airbnb JavaScript Style Guide**
- **Use ESLint + Prettier** for formatting
- **Use functional components** with hooks
- **Write JSDoc comments** for complex functions

#### Component Style Example

```tsx
import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/Button';
import { reportService } from '@/services/reportService';

interface ReportCardProps {
  report: Report;
  onDownload?: (reportId: string) => void;
  className?: string;
}

/**
 * Component for displaying a report card with download functionality
 */
export const ReportCard: React.FC<ReportCardProps> = ({
  report,
  onDownload,
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const queryClient = useQueryClient();

  const downloadMutation = useMutation({
    mutationFn: reportService.downloadReport,
    onSuccess: () => {
      queryClient.invalidateQueries(['reports']);
    },
  });

  const handleDownload = useCallback(async () => {
    if (!report.id) return;

    setIsLoading(true);
    try {
      await downloadMutation.mutateAsync({
        reportId: report.id,
        format: 'pdf'
      });
      onDownload?.(report.id);
    } finally {
      setIsLoading(false);
    }
  }, [report.id, downloadMutation, onDownload]);

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900">
        {report.client.companyName}
      </h3>
      <p className="text-sm text-gray-600 mt-1">
        {report.reportType} - {report.status}
      </p>

      <div className="mt-4">
        <Button
          onClick={handleDownload}
          disabled={isLoading || report.status !== 'completed'}
          variant="primary"
          size="sm"
        >
          {isLoading ? 'Downloading...' : 'Download PDF'}
        </Button>
      </div>
    </div>
  );
};
```

## 🧪 Testing Guidelines

### Backend Testing

- **Write tests** for all new models, views, and services
- **Use pytest** and pytest-django
- **Follow AAA pattern** (Arrange, Act, Assert)
- **Mock external dependencies** (Azure services, etc.)

#### Test Example

```python
import pytest
from django.test import TestCase
from apps.clients.models import Client
from apps.reports.models import Report


class TestReportModel(TestCase):
    """Test cases for Report model"""

    def setUp(self):
        """Set up test data"""
        self.client = Client.objects.create(
            company_name='Test Company',
            contact_email='test@example.com'
        )

    def test_report_creation(self):
        """Test that a report can be created successfully"""
        # Arrange
        report_data = {
            'client': self.client,
            'report_type': 'detailed',
            'status': 'pending'
        }

        # Act
        report = Report.objects.create(**report_data)

        # Assert
        self.assertEqual(report.client, self.client)
        self.assertEqual(report.report_type, 'detailed')
        self.assertEqual(report.status, 'pending')
        self.assertIsNotNone(report.created_at)
```

### Frontend Testing

- **Use Testing Library** for component tests
- **Test user interactions** and edge cases
- **Mock API calls** using MSW or similar
- **Write integration tests** for critical flows

#### Test Example

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReportCard } from './ReportCard';
import { mockReport } from '@/test-utils/mocks';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ReportCard', () => {
  it('renders report information correctly', () => {
    render(<ReportCard report={mockReport} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText(mockReport.client.companyName)).toBeInTheDocument();
    expect(screen.getByText(/detailed/i)).toBeInTheDocument();
  });

  it('calls onDownload when download button is clicked', async () => {
    const mockOnDownload = jest.fn();

    render(
      <ReportCard report={mockReport} onDownload={mockOnDownload} />,
      { wrapper: createWrapper() }
    );

    fireEvent.click(screen.getByText(/download pdf/i));

    await waitFor(() => {
      expect(mockOnDownload).toHaveBeenCalledWith(mockReport.id);
    });
  });
});
```

## 📋 Pull Request Process

1. **Ensure your code passes all tests:**
   ```bash
   # Run all tests
   npm run test:backend
   npm run test:frontend
   ```

2. **Update documentation** if needed

3. **Create a pull request** with:
   - Clear, descriptive title
   - Detailed description of changes
   - Link to related issues
   - Screenshots for UI changes

4. **Pull Request Template:**
   ```markdown
   ## Description
   Brief description of the changes made.

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] New tests added (if applicable)
   - [ ] Manual testing completed

   ## Screenshots (if applicable)
   Add screenshots of UI changes.

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   ```

## 🔍 Code Review Process

- **All submissions** require review from maintainers
- **Be responsive** to feedback and questions
- **Be respectful** in discussions
- **Address all feedback** before the PR can be merged
- **Maintain code quality** standards

## 📚 Documentation

- **Update documentation** when adding new features
- **Use clear, concise language**
- **Include code examples** when helpful
- **Keep API documentation** up to date

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the bug
3. **Expected vs actual behavior**
4. **Environment details** (OS, browser, versions)
5. **Screenshots or error logs** if applicable

Use our bug report template:

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 91]
- Version: [e.g., 1.0.0]
```

## 💡 Feature Requests

For feature requests:

1. **Check existing issues** first
2. **Describe the problem** you're trying to solve
3. **Propose a solution** if you have one
4. **Consider the impact** on existing users

## 🏷️ Commit Message Guidelines

Use conventional commit format:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(reports): add cost optimization report type

Add new report type focused on cost savings recommendations.
Includes PDF generation and email delivery options.

Closes #123
```

```
fix(auth): resolve token refresh issue

Token refresh was failing due to incorrect header format.
Fixed by updating the authorization header construction.

Fixes #456
```

## 🎉 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for their contributions
- **Special thanks** in significant releases

## 📞 Getting Help

If you need help:

1. **Check the documentation** in the `docs/` folder
2. **Search existing issues** on GitHub
3. **Ask questions** in GitHub Discussions
4. **Join our Discord** (if applicable)
5. **Email maintainers** for sensitive issues

## 📋 Development Environment Tips

### Useful Commands

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Run database migrations
cd azure_advisor_reports
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Install new Python dependencies
pip install package-name
pip freeze > requirements.txt

# Install new Node dependencies
cd frontend
npm install package-name
```

### IDE Configuration

#### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./azure_advisor_reports/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 🙏 Thank You

Thank you for contributing to the Azure Advisor Reports Platform! Your efforts help make this tool better for cloud consultancies and MSPs worldwide.

---

*This contributing guide is a living document and may be updated as the project evolves.*