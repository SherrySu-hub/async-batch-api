# Async Batch Processing API
English | [中文](https://github.com/SherrySu-hub/AI_deployment/blob/main/README_ZH.md)

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
## Timeout Configuration

This project includes a timeout handler to prevent long-running tasks from hanging the request. The default timeout is 2 seconds, and the API will return an HTTP 504 error if the prediction exceeds this limit.

You can customize this timeout in the following ways:

- **Local Development**:
By default, a 2-second timeout is applied. You can manually adjust this value in main.py on line 29:
  ```python
  timeout_seconds = get_timeout()
  ```

- **Docker Deployment**:
When deploying via Docker (e.g., using docker-compose), you can override the timeout by setting the environment variable timeout in your docker-compose.yml file:
  ```yaml
  environment:
    - timeout=1.0
  ```
This timeout controls how long the API will wait for a batch inference result before returning a timeout error. Adjust the value based on your model performance and server conditions.

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
