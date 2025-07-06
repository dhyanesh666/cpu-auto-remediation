import subprocess
import time
from cpu_monitor import get_cpu_usage
from log_analysis import get_logs, analyze_logs
import boto3

def restart_container(container_name):
    print(f"[INFO] Restarting container: {container_name}")
    try:
        subprocess.run(["docker", "restart", container_name], check=True)
        print(f"[INFO] Container '{container_name}' restarted successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to restart container: {e}")
        return False

def verify_cpu_stability(threshold=50.0, wait_seconds=30):
    print(f"[INFO] Waiting {wait_seconds} seconds before checking CPU usage...")
    time.sleep(wait_seconds)
    cpu = get_cpu_usage()
    print(f"[INFO] CPU usage after restart: {cpu:.2f}%")
    return cpu < threshold

def send_sns_email(subject, message):
    try:
        sns = boto3.client('sns', region_name='ap-south-1')  # Replace with your AWS region
        topic_arn = 'arn:aws:sns:ap-south-1:885657313202:DevOpsAlert'  # Replace with your topic ARN

        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print("[INFO] SNS notification sent successfully.")
    except Exception as e:
        print(f"[ERROR] SNS notification failed: {e}")

if __name__ == "__main__":
    container_name = "my-test-container"

    logs = get_logs()
    rca_summary = analyze_logs(logs)

    if restart_container(container_name):
        if verify_cpu_stability():
            print("[INFO] CPU usage is now stable. Remediation successful.")
            send_sns_email(
                subject="DevOps Auto-Remediation Triggered",
                message=f"Container '{container_name}' was restarted after CPU spike.\n\nRoot Cause Analysis:\n{rca_summary}\n\nCPU is now stable."
            )
        else:
            print("[WARN] CPU still high. Further investigation may be needed.")
            send_sns_email(
                subject="DevOps Alert - CPU Still High After Remediation",
                message=f"Container '{container_name}' was restarted, but CPU usage remains high.\n\nRoot Cause Analysis:\n{rca_summary}"
            )
    else:
        print("[ERROR] Could not restart the container. Manual intervention required.")
        send_sns_email(
            subject="DevOps Remediation Failed",
            message=f"Attempt to restart container '{container_name}' failed.\n\nRoot Cause Analysis:\n{rca_summary}"
        )
