import json
import os
import pika

# Pika (rabbitMQ) client setup
credentials = pika.PlainCredentials("guest", "guest")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", credentials=credentials)
)
channel = connection.channel()

# Fetch exchange name
exchange = os.getenv("Q_EXCHANGE")
assert exchange is not None, "env.var 'Q_EXCHANGE' not defined!"
# channel.exchange_declare(exchange=exchange, exchange_type="topic")

# Send a message
message = json.dumps(["hello"])
channel.basic_publish(exchange=exchange, routing_key="hotword.detected", body=message)
print(" [x] Sent %r" % message)

connection.close()
