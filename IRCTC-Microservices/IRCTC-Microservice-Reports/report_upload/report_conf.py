from multiprocessing import cpu_count



# Socket Path

bind = 'unix:/home/ubuntu/IRCTC-Microservice-Reports/report_upload/gunicorn.sock'



# Worker Options

workers = cpu_count() + 1

worker_class = 'uvicorn.workers.UvicornWorker'



# Logging Options

loglevel = 'debug'

accesslog = '/home/ubuntu/IRCTC-Microservice-Reports/report_upload/access_log'

errorlog =  '/home/ubuntu/IRCTC-Microservice-Reports/report_upload/error_log'
