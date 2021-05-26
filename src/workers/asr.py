import pika
import subprocess


# Pika (rabbitMQ) client setup
credentials = pika.PlainCredentials("guest", "guest")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq", credentials=credentials)
)
channel = connection.channel()
channel.exchange_declare(exchange="asr-task", exchange_type="fanout")

result = channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange="asr-task", queue=queue_name)

print("[*] Waiting for asr-task. To exit press CTRL+C")


def callback(ch, method, properties, body):
    print("Received a request to launch ASR")
    # cmd = (
    #     "cat /root/audios/phiona-test-1.wav | "
    #     "/root/wav2letter/build/inference/inference/examples/simple_streaming_asr_example "
    #     "--input_files_base_path /root/model"
    # )
    cmd = (
        "/root/wav2letter/build/inference/inference/examples/multithreaded_streaming_asr_example "
        "--input_audio_files /root/audios/phiona-test-1.wav "
        "--input_files_base_path /root/model "
        "--output_files_base_path /root/audios"
    )
    ps = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        executable="/bin/bash",
    )
    output = ps.communicate()[0]
    print(output)


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()
