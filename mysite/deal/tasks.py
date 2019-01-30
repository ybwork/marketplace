from celery import Celery

app = Celery('tasks', backend='rpc://', broker='amqp://localhost')


@app.task
def perform_payment():
    return 'perform_payment'
