# Contribute to Xaibo

This guide will walk you through everything you need to know to contribute to the Xaibo AI agent framework.

## Prerequisites

Before you begin, make sure you have the following installed:

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [pnpm](https://pnpm.io/) (for UI contributions only)

## Local Xaibo Setup

Clone the repository:

```bash
git clone https://github.com/XpressAI/xaibo
cd xaibo
```

Install dependencies:

```bash
uv sync
```

## Contributing to Xaibo Core

The core framework is located at [`src/xaibo`](https://github.com/XpressAI/xaibo/tree/main/src/xaibo).

### Testing Your Core Changes

The `uvx` command allows you to point to your local development version instead of the installed package.

Create a test directory alongside your xaibo repo:

```bash
# From your working directory, create a test folder
mkdir ../test_new_feature
cd ../test_new_feature
```

This gives you a clean environment separate from your development code:

```
working_dir/
├── xaibo/          # Your cloned repo with your changes
└── test_new_feature/  # Your test directory (you are here)
```

Initialize a test agent using your local code:

```bash
uvx ../xaibo init my_test_agent
```

The `uvx` command points to your local xaibo directory (`../xaibo`) allowing you to test your changes directly.

## Contributing to Xaibo UI

The UI frontend is located at [`ui/`](https://github.com/XpressAI/xaibo/tree/main/ui). We use Svelte.

### Setting Up UI Development

Navigate to the UI directory and install dependencies:

```bash
# From the root xaibo directory
cd ui
pnpm install
```

Start the development server:

```bash
pnpm run dev
```

You'll see output like this, indicating the server is running:

```
VITE v6.2.1  ready in 4584 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

### Running a Xaibo Instance

The UI development server needs a running Xaibo instance to connect to, otherwise it'll be blank.

Run a Xaibo instance in another terminal tab:

```bash
# From the root directory
uv run xaibo dev
```

### View Your Changes

Now you can visit `http://localhost:5173/` to see your UI changes in real-time as you work.

## Contributing to Xaibo Documentation

Our documentation uses [MkDocs](https://www.mkdocs.org/) and follows the [Divio documentation system](https://docs.divio.com/documentation-system/).

### Working with Documentation

In the Xaibo base directory, start the local documentation server:

```bash
uv run mkdocs serve
```

### Adding New Documentation

Create your markdown files in the appropriate directory and update the `mkdocs.yml` configuration file to include your new pages.

Follow the Divio documentation principles:

- **Tutorials**: Learning-oriented, step-by-step guides for beginners
- **How-to guides**: Problem-oriented, specific task instructions
- **Reference**: Information-oriented, technical specifications
- **Explanation**: Understanding-oriented, conceptual background

## Other Ways to Contribute

Aside from contributing to the core framework, UI, and documentation, you can also help by:

### Reporting Issues and Feature Requests

For bugs:

- Search existing [issues](https://github.com/XpressAI/xaibo/issues) first
- Create a new issue with steps to reproduce, expected vs actual behavior, and your environment details

For feature requests:

- Check if someone has already suggested it
- Open a new issue describing the problem it solves and why it would be useful

## Getting Help

If you need help or have questions, check the existing [issues](https://github.com/XpressAI/xaibo/issues) or open a new one for support.

---

Thank you for contributing to Xaibo! Your contributions help make AI agent development more accessible and powerful for everyone.

**Join our community**: Connect with other contributors and users in our [Discord server](https://discord.gg/uASMzSSVKe) 🚀