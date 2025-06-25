# Async Batch Processing API

This project provides a **general-purpose asynchronous batch processing API framework** built with FastAPI and asyncio. It supports any task that benefits from batch inference, such as image classification, NLP prediction, video frame processing, and more.

---

## Features

- Asynchronous queue with background batch processing
- Pluggable model and task function for different use cases
- Production-ready with Gunicorn + UvicornWorker
- Easy deployment via Docker

---

## Project Structure

```
.
├── main.py                 # FastAPI entrypoint, manages requests and task queue
├── gunicorn_config.py      # Gunicorn configuration
├── classification/
│   └── inference.py        # Example task logic (image classification, replaceable)
├── Dockerfile
├── docker-compose.yml
```
---

##  Running the API

### Development
```bash
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```
Use this for local development and testing. Supports hot-reloading.

### Production (Gunicorn)

```bash
gunicorn main:app -c gunicorn_config.py
```
Note: Gunicorn is only supported on Linux/Unix environments.
For Windows users, please deploy via Docker or use uvicorn directly in production mode.

### Docker (Cross-platform)
```bash
docker-compose up --build -d
```
Recommended for consistent deployment across platforms.
The service will be available at:
```
http://localhost:5001/cls
```
---

## API Usage

### POST `/cls`

**Parameters:**
- `file`: Upload a file (e.g., image, document)

**Example:**
```bash
curl -X POST http://localhost:5001/cls -F "file=@path/to/image.jpg"
```

**Response:**
```json
{
  "prediction": [your result here]
}
```

---

## Task Customization

To support other tasks (e.g., NLP, video, tabular), modify:

- `classification/inference.py`: implement `get_model`, `preprocess`, and `batch_classification`
- `BatchProcessor`: handles async batch queuing and processing
- API route logic can be extended for multiple tasks and endpoints

---

## Gunicorn Configuration (`gunicorn_config.py`)

- `workers = 1`
- `threads = 8`
- `worker_class = 'uvicorn.workers.UvicornWorker'`
- `bind = '0.0.0.0:5001'`

>  These values can be adjusted based on hardware and workload:
> - Use more `workers` on multi-core servers for CPU-bound tasks
> - Increase `threads` for I/O-bound or high-concurrency API loads

---

## Python Dependencies

Example: `requirements.txt`
```txt
fastapi
uvicorn
...
```
Additional packages may be required depending on your task (e.g., `transformers`, `opencv-python`).
