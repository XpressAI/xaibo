# Xaibo Documentation

Welcome to the comprehensive documentation for Xaibo, a modular AI agent framework designed for building flexible AI systems with clean protocol-based interfaces.

## 📚 Documentation Overview

This documentation is organized into the following sections:

### **Getting Started**
- **[Home](index.md)** - Introduction to Xaibo and quick start guide
- **[Getting Started](getting-started.md)** - Installation, setup, and your first agent
- **[Core Concepts](core-concepts.md)** - Understanding Xaibo's fundamental principles

### **Framework Deep Dive**
- **[Features](features.md)** - Comprehensive overview of Xaibo's capabilities
- **[Architecture](architecture.md)** - Technical architecture and design patterns
- **[Project Structure](project-structure.md)** - Understanding the codebase organization

### **Development & Usage**
- **[Configuration](configuration.md)** - Agent configuration and customization
- **[Examples & Tutorials](examples.md)** - Practical examples and step-by-step tutorials
- **[Tools & Integrations](tools-and-integrations.md)** - Available tools and third-party integrations
- **[API Reference](api-reference.md)** - Complete API documentation

### **Operations & Maintenance**
- **[Deployment](deployment.md)** - Production deployment strategies
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Changelog](changelog.md)** - Version history and updates

### **Community & Contribution**
- **[Contributing](contributing.md)** - How to contribute to Xaibo development

## 🎯 Quick Navigation by User Type

### **New Users**
Start here to get up and running quickly:
1. [Home](index.md) - Understand what Xaibo is
2. [Getting Started](getting-started.md) - Install and create your first agent
3. [Core Concepts](core-concepts.md) - Learn the fundamentals
4. [Examples & Tutorials](examples.md) - Follow practical examples

### **Developers**
For building and customizing agents:
1. [Architecture](architecture.md) - Understand the technical design
2. [Configuration](configuration.md) - Learn agent configuration
3. [Tools & Integrations](tools-and-integrations.md) - Explore available tools
4. [API Reference](api-reference.md) - Detailed API documentation
5. [Project Structure](project-structure.md) - Navigate the codebase

### **DevOps/Operators**
For deploying and maintaining Xaibo:
1. [Deployment](deployment.md) - Production deployment guides
2. [Configuration](configuration.md) - Environment and system configuration
3. [Troubleshooting](troubleshooting.md) - Diagnose and fix issues
4. [Changelog](changelog.md) - Track updates and changes

### **Contributors**
For contributing to Xaibo development:
1. [Contributing](contributing.md) - Contribution guidelines
2. [Architecture](architecture.md) - Understand the codebase design
3. [Project Structure](project-structure.md) - Navigate the source code
4. [API Reference](api-reference.md) - Implementation details

## 🔧 Building and Serving Documentation

### **Prerequisites**
- Python 3.8 or higher
- `uv` package manager (recommended) or `pip`

### **Local Development**

#### Using uv (Recommended)
```bash
# Install documentation dependencies (included in dev dependency group)
uv sync --group dev

# Serve documentation locally with live reload
uv run mkdocs serve

# Build static documentation
uv run mkdocs build

# Build with strict mode (fails on warnings)
uv run mkdocs build --strict
```

#### Using pip
```bash
# Install documentation dependencies
pip install mkdocs>=1.6.1 mkdocs-material>=9.6.14 mkdocs-git-revision-date-localized-plugin>=1.4.5

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

### **Accessing Local Documentation**
- **Development server**: http://localhost:8000
- **Built files**: Located in `site/` directory after running `mkdocs build`

## 📝 Documentation Maintenance Guidelines

### **Content Standards**
- **Clarity**: Write clear, concise explanations suitable for the target audience
- **Examples**: Include practical code examples and use cases
- **Structure**: Use consistent heading hierarchy and formatting
- **Links**: Ensure all internal links are valid and use relative paths
- **Images**: Store images in `docs/images/` and use descriptive filenames

### **File Organization**
- **Main pages**: Direct children of `docs/` directory
- **Images**: Store in `docs/images/` subdirectory
- **Navigation**: Update `mkdocs.yml` nav section when adding new pages
- **Cross-references**: Use relative links between documentation pages

### **Writing Guidelines**
- **Audience-focused**: Consider the reader's experience level and goals
- **Actionable**: Provide clear steps and actionable instructions
- **Current**: Keep content up-to-date with the latest framework version
- **Tested**: Verify all code examples and instructions work correctly

### **Review Process**
1. **Content review**: Ensure accuracy and completeness
2. **Technical review**: Verify code examples and technical details
3. **Build test**: Run `mkdocs build --strict` to check for issues
4. **Link validation**: Verify all internal and external links work

### **Common Issues**
- **Broken links**: Use `mkdocs build --strict` to identify broken references
- **Missing images**: Ensure image files exist in `docs/images/`
- **Navigation**: Update `mkdocs.yml` when adding/removing pages
- **Git warnings**: Documentation files without git history will show timestamp warnings

## 🚀 Contributing to Documentation

We welcome contributions to improve the documentation! Here's how to help:

### **Types of Contributions**
- **Content improvements**: Fix errors, clarify explanations, add examples
- **New sections**: Add missing documentation for features or use cases
- **Structure improvements**: Enhance organization and navigation
- **Visual enhancements**: Add diagrams, screenshots, or other visual aids

### **Contribution Process**
1. **Fork** the repository
2. **Create** a feature branch for your documentation changes
3. **Make** your changes following the maintenance guidelines above
4. **Test** your changes with `uv run mkdocs serve`
5. **Validate** with `uv run mkdocs build --strict`
6. **Submit** a pull request with a clear description of your changes

### **Getting Help**
- **Issues**: Report documentation issues on GitHub
- **Discussions**: Join community discussions for questions and suggestions
- **Discord**: Connect with the community on our Discord server

---

**Last Updated**: This documentation is automatically updated with each build. For the most current information, always refer to the latest version of the documentation.