# Dependency layout

The project has separate dependency layers so the application image does not
install notebook and data-collection tooling.

## Runtime

`requirements.txt` is installed by `Dockerfile` and contains only dependencies
needed by the FastAPI service, Telegram bot, shared retrieval runtime, and LLM
clients.

## Pipeline

`requirements-pipeline.txt` adds the downloader, Playwright, OCR, article
preparation, embedding, and index-building dependencies. Install it when
running jobs under `data-pipeline/`.

## Experiments

`requirements-experiments.txt` adds Jupyter and exploratory libraries used by
notebooks under `experiments/notebooks/`. It includes the pipeline layer because
the notebooks execute pipeline utilities.

## Development

`requirements-dev.txt` adds only the test runner and HTTP test client to the
production runtime.

The package list was reduced from the existing environment by keeping direct
imports used by each layer and excluding transitive packages, Jupyter internals,
Chroma telemetry dependencies, and unused experimental libraries from the
production requirements.

Install the layer needed for the task:

```bash
pip install -r requirements.txt
pip install -r requirements-pipeline.txt
pip install -r requirements-experiments.txt
pip install -r requirements-dev.txt
```

The API downloads the BGE-M3 model from Hugging Face on first startup. Set
`HF_TOKEN` in the root `.env` to an access token, and the model cache is kept
under `data/huggingface/` through the Compose data mount.
