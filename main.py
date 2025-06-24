import warnings
warnings.filterwarnings('ignore')
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvicorn
import logging
import io
from classification.inference import get_model, preprocess, batch_classification
import torch
from PIL import Image
import traceback

app = FastAPI()

logger = logging.getLogger('gunicorn.error')
logger.setLevel(logging.INFO)

# multi-thread
executor = ThreadPoolExecutor(max_workers=4)

result_dict = {}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        while True:
            img_ids, batch = [], []
            # Wait until we have enough requests in the queue
            for _ in range(self.batch_size):
                try:
                    img_id, img = await asyncio.wait_for(self.queue.get(), timeout=self.batch_timeout)
                    img_ids.append(img_id)
                    batch.append(img)
                except asyncio.TimeoutError:
                    if not batch:  # No requests in the queue
                        break

            if batch:
                try:
                    batch_tensor = torch.cat(batch, dim=0)
                    batch_predictions = self._classify_batch(batch_tensor)
                    for img_id, prediction in zip(img_ids, batch_predictions):
                        self.result_dict[img_id].set_result((prediction))

                except Exception as e:
                    print(e)
                    self._log_error(e)

    def _classify_batch(self, batch_tensor):
        return self.predict(imgs=batch_tensor, model=self.model, device=self.device)

    def _log_error(self, exception):
        tb = traceback.extract_tb(exception.__traceback__)
        _, line, func, text = tb[-1]
        logger.info(f"Batch processing error: {func} at line {line}: {text}\n{str(exception)}")

@asynccontextmanager
async def lifespan(app: FastAPI):

    print('start app')
    # Queue
    app.state.img_queue = asyncio.Queue()

    batch_processor = BatchProcessor(
        queue=app.state.img_queue,
        model=get_model(device=device),
        predict_function=batch_classification,
        result_dict=result_dict,
        device=device
    )

    # run in the background
    cls_task = asyncio.create_task(batch_processor.process_batch())

    try:
        yield  # Keep the app running
    finally:
        cls_task.cancel()
        await asyncio.gather(cls_task, return_exceptions=True)
        print('App shutdown complete')

app.router.lifespan_context = lifespan

'''
curl -X POST 127.0.0.1:5001/cls -F "file=@<file path>"
'''
@app.post("/cls")
async def predict(file: UploadFile):

    logger.info(f'Get the request')
    try:
        content = await file.read()

        image_data = io.BytesIO(content)  # get image
        img_id = id(image_data)

        img = preprocess(Image.open(image_data))

        result_dict[img_id] = asyncio.Future()  # A future is an object that represents a delayed result for an asynchronous task.
        await app.state.img_queue.put((img_id, img))
        prediction = await result_dict[img_id]
    
        return {'prediction': prediction}

    except Exception:
        print(f'{traceback.print_exc()}')
        logger.info(f'{traceback.print_exc()}')
        raise HTTPException(status_code=500)  # 500
    
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)  # 