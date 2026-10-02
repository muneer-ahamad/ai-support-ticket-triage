# Deployment Checklist

## Local first-run checklist

1. Install Python 3.12.
2. Create and activate a virtual environment.
3. Install `requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Put your Gemini API key in `.env`.
6. Run `pytest -q`.
7. Run `streamlit run ui/streamlit_app.py`.
8. Try both an auto-route ticket and a security ticket that requires review.
9. Run `uvicorn app.api:app --reload` and test `/docs`.
10. Run `python evals/run_evals.py` and commit the generated `evals/results.md` if you want measured results visible in the repo.

## Streamlit Community Cloud

- Repository: your GitHub repository
- Branch: `main`
- Entrypoint: `ui/streamlit_app.py`
- Python: `3.12`
- Required secret:

```toml
GEMINI_API_KEY = "your-real-key"
```

Do not upload `.env`.

## Docker API

```bash
docker build -t ai-ticket-triage .
docker run --rm -p 8000:8000 --env-file .env ai-ticket-triage
```

Open `http://localhost:8000/docs`.

## GitHub push

```bash
git init
git add .
git commit -m "Build AI support ticket triage system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

If the remote repository already has files, clone it first and place the project files inside it instead of force-pushing over existing history.
