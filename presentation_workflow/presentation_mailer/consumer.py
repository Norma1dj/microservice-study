import json
import pika
from pika.exceptions import AMQPConnectionError
import django
import os
import time
import sys
from django.core.mail import send_mail


sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "presentation_mailer.settings")
django.setup()

# this function extracts information from the message body, such as the presenter's email, name, and presentation title.
def process_approval(ch, method, properties, body):
    message = json.loads(body.decode("utf-8"))
    presenter_email = message["presenter_email"]
    presenter_name = message["presenter_name"]
    presentation_title = message["title"]
    
# composes an email subject and body to notify the presenter that their presentation has been accepted
    subject = "Your presentation has been accepted"
    body = f"{presenter_name}, we're happy to tell you that your presentation '{presentation_title}' has been accepted"

    send_mail(
        subject=subject,
        message=body,
        from_email="admin@conference.go",
        recipient_list=[presenter_email],
    )


def process_rejection(ch, method, properties, body):
    message = json.loads(body.decode("utf-8"))
    presenter_email = message["presenter_email"]
    presenter_name = message["presenter_name"]
    presentation_title = message["title"]

    subject = "Your presentation has been rejected"
    body = f"{presenter_name}, we regret to inform you that your presentation '{presentation_title}' has been rejected"

    send_mail(
        subject=subject,
        message=body,
        from_email="admin@conference.go",
        recipient_list=[presenter_email],
    )


while True:
    try:
        #establish connection to RabbitMq server line 53 and 54
        #creates the channel line 56
        #Queues are declared 58 and 59
        parameters = pika.ConnectionParameters(host='rabbitmq')
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='presentation_approvals')
        channel.queue_declare(queue='presentation_rejections')

        # The consumer is set up for each queue using queue name, callback function, and auto acknowledge once processed
        channel.basic_consume(
            queue='presentation_approvals',
            on_message_callback=process_approval,
            auto_ack=True,
        )
        # The consumer is set up for each queue using queue name, callback function, and auto acknowledge once processed
        channel.basic_consume(
            queue='presentation_rejections',
            on_message_callback=process_rejection,
            auto_ack=True,
        )
        # start the consumer and start listening for incoming messages
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print("Could not connect to RabbitMQ")
        time.sleep(2.0)
