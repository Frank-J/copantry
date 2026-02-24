# API Key Handling Guide

## Why Keys Must Be Secret

Your API key is like a password. Anyone who has it can make requests that count against your quota. Never share it or commit it to GitHub.

## Local Development

Create a `.env` file in the project root:

```
GEMINI_API_KEY=paste_your_key_here
```

Add a `.gitignore` file in the project root to prevent it from being uploaded to GitHub:

```
.env
```

As long as `.env` is listed in `.gitignore`, it will never leave your computer.

## In Your Code

Never hardcode the key. Always load it from the environment:

```python
# NEVER do this
api_key = "AIzaSy..."

# Always do this
import os
api_key = os.getenv("GEMINI_API_KEY")
```

## Deployed App (Streamlit Cloud)

Streamlit Cloud has a built-in Secrets manager:
1. Go to your app's dashboard on share.streamlit.io
2. Click **Settings → Secrets**
3. Paste the following and save:

```
GEMINI_API_KEY = "paste_your_key_here"
```

The key is securely injected at runtime and never touches GitHub.

## Summary

| Where | How the key is stored |
|---|---|
| Your laptop | `.env` file (blocked from GitHub by `.gitignore`) |
| GitHub | Key does not exist here at all |
| Streamlit Cloud | Pasted into their Secrets dashboard |
