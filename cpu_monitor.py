import time
import subprocess
import logging
from prometheus_api_client import PrometheusConnect

# Set up logging
logging.basicConfig(
    filename='/var/log/devops_agent.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Prometheus connection
prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

def get_cpu_usage():
    query = '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    try:
        result = prom.custom_query(query)
        if result:
            usage = float(result[0]["value"][1])
            return round(usage, 2)
        else:
            return 0.0
    except Exception as e:
        logging.error(f"Failed to fetch CPU usage: {e}")
        return 0.0

def trigger_remediation():
    try:
        logging.info("Triggering remediation...")
        subprocess.run(["python3", "/home/ubuntu/remediation.py"], check=True)
        logging.info("Remediation completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Remediation script failed: {e}")

def monitor_cpu(threshold=80.0, duration=120):
    spike_start = None
    spike_triggered = False

    logging.info("Starting CPU monitoring...")

    while True:
        cpu = get_cpu_usage()
        logging.info(f"Current CPU usage: {cpu}%")

        if cpu > threshold:
            if spike_start is None:
                spike_start = time.time()
                logging.info(f"CPU spike started at {time.ctime(spike_start)}")
            elif time.time() - spike_start >= duration and not spike_triggered:
                logging.warning("CPU spike duration exceeded. Initiating remediation.")
                trigger_remediation()
                spike_triggered = True
                spike_start = None
        else:
            if spike_start is not None:
                logging.info("CPU returned to normal. Resetting spike timer.")
            spike_start = None
            spike_triggered = False

        time.sleep(10)

if __name__ == "__main__":
    monitor_cpu()
