from multiprocessing import cpu_count



# Socket Path

bind = 'unix:/home/ubuntu/IRCTC-Microservice-Reports/report_upload/gunicorn.sock'
#bind = "127.0.0.1:8000"


# Worker Options

workers = cpu_count() + 1

worker_class = 'uvicorn.workers.UvicornWorker'



# Logging Options

loglevel = 'debug'

accesslog = '/home/ubuntu/IRCTC-Microservice-Reports/access_log'

errorlog =  '/home/ubuntu/IRCTC-Microservice-Reports/error_log'
