#!/bin/sh

generate_random_data() {
    # Function to generate a random alphanumeric string of length 10
    head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 10
}

while true; do
    current_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    random_message=$(generate_random_data)
    json_message="{\"@timestamp\":\"$current_timestamp\",\"message\":\"$random_message\"}"

    echo "Sending JSON message:"
    echo "$json_message"

    echo "$json_message" | kafka-console-producer.sh --broker-list localhost:9092 --topic test.dev --property parse.key=true --property key.separator=:

    sleep 1  # Wait for 1 second before sending the next message
done