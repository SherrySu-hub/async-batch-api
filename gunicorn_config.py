import logging

loglevel = 'info'
accesslog = 'api.log'
workers = 1
threads = 16
worker_class = 'uvicorn.workers.UvicornWorker'  # 使用 Uvicorn 作為 worker
bind = '0.0.0.0:5001'

error_logger = logging.getLogger('gunicorn.error')
error_logger.setLevel(logging.INFO)
handler = logging.FileHandler('api.log')
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(process)d - %(thread)d] ||| %(filename)s %(funcName)s : %(message)s'))
error_logger.addHandler(handler)


