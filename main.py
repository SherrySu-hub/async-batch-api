import warnings
warnings.filterwarnings('ignore')
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
import logging
import io
from classification.inference import get_model, preprocess, batch_classification
import torch
from PIL import Image
import traceback
from functools import wraps
import os

app = FastAPI()

logger = logging.getLogger('gunicorn.error')
logger.setLevel(logging.INFO)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_timeout(env_var="timeout", default=2.0):
    try:
        return float(os.environ.get(env_var, default))
    except (TypeError, ValueError):
        return default
timeout_seconds = get_timeout()

'''
Batch Process
'''
class BatchProcessor:
    def __init__(self, queue, model, predict_function, result_dict, batch_size=16, batch_timeout=0.01, device='cpu'):
        self.queue = queue
        self.model = model
        self.predict = predict_function
        self.result_dict = result_dict
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.device = device

    async def process_batch(self):
        # run this program indefinitely
        while True:
            '''
            Retrieve data from the queue and append it to a list. 
            After reaching the maximum number of fetch attempts, process the list if it's not empty
            '''
            img_ids, batch = [], []
            for _ in range(self.batch_size):
                try:
                    # Set a timeout when retrieving data from the queue.
                    img_id, img = await asyncio.wait_for(self.queue.get(), timeout=self.batch_timeout)  
                    img_ids.append(img_id)
                    batch.append(img)
                # If timeout occurs and the list is empty, reset the fetch attempt count.
                except asyncio.TimeoutError:
                    if not batch:  
                        break

            # If the list is not empty, process the data.
            if batch:
                try:
                    batch_tensor = torch.cat(batch, dim=0)
                    batch_predictions = self._predict_batch(batch_tensor)
                    # Store each processed result along with its ID in a dictionary for easy retrieval later.
                    for img_id, prediction in zip(img_ids, batch_predictions):
                        self.result_dict[img_id].set_result((prediction))

                except Exception:
                    self._log_error()

    def _predict_batch(self, batch_tensor):
        return self.predict(imgs=batch_tensor, model=self.model, device=self.device)

    def _log_error(self):
        logger.info(f'{traceback.format_exc()}')

@asynccontextmanager
async def lifespan(app: FastAPI):

    print('start app')
    app.state.img_queue = asyncio.Queue()
    app.state.result_dict = {}

    batch_processor = BatchProcessor(
        queue=app.state.img_queue,
        model=get_model(device=device),
        predict_function=batch_classification,
        result_dict=app.state.result_dict,
        device=device
    )

    # run it as a background coroutine
    cls_task = asyncio.create_task(batch_processor.process_batch())

    try:
        yield  # Keep the app running
    finally:
        # Cancel the background task on shutdown
        cls_task.cancel()
        # Wait for the task to finish cancellation, suppressing any exceptions
        await asyncio.gather(cls_task, return_exceptions=True)
        print('App shutdown complete')

app.router.lifespan_context = lifespan

def exception_logger(timeout_seconds=2.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                msg = f"Timeout after {timeout_seconds}s in {func.__name__}"
                logger.error(msg)
                return JSONResponse(status_code=504, content={"detail": f"Request timed out after {timeout_seconds} seconds"})
            except Exception:
                tb = traceback.format_exc()
                logger.error(tb)
                return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
        return wrapper
    return decorator

'''
curl -X POST 127.0.0.1:5001/cls -F "file=@<file path>"
'''
@app.post("/cls")
@exception_logger(timeout_seconds=timeout_seconds)
async def predict(file: UploadFile):

    logger.info(f'Get the request')
    content = await file.read()

    image_data = io.BytesIO(content)
    img_id = id(image_data)

    img = preprocess(Image.open(image_data))

    # A future is an object that represents a delayed result for an asynchronous task.
    app.state.result_dict[img_id] = asyncio.Future()
    await app.state.img_queue.put((img_id, img))
    prediction = await app.state.result_dict[img_id]

    return {'prediction': prediction}
    
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)  # 
