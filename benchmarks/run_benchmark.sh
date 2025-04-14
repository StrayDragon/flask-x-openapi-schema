#!/bin/bash
# Run the full benchmark workflow

# Start the Flask server in the background
echo "Starting Flask server..."
python -c "from benchmarks.locustfile import app; app.run(host='0.0.0.0', port=5000)" &
SERVER_PID=$!

# Wait for the server to start
echo "Waiting for server to start..."
sleep 3

# Run the locust benchmark
echo "Running locust benchmark..."
locust -f benchmarks/locustfile.py --headless -u 20 -r 5 -t 10s --csv=benchmarks/results --host=http://localhost:5000

# Generate the report
echo "Generating benchmark report..."
python benchmarks/locust_report.py

# Kill the server
echo "Stopping Flask server..."
kill $SERVER_PID

echo "Benchmark complete!"