import pika

# Pika (rabbitMQ) client setup
credentials = pika.PlainCredentials("guest", "guest")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", credentials=credentials)
)
channel = connection.channel()

channel.exchange_declare(exchange="asr-task", exchange_type="fanout")

message = "pin"
channel.basic_publish(exchange="asr-taks", routing_key="", body=message)
print(" [x] Sent %r" % message)
connection.close()
