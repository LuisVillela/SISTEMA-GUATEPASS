#!/usr/bin/env python3
import boto3
import json
from datetime import datetime, timedelta

def check_processor_logs():
    print(" OBTENIENDO LOGS DEL LAMBDA PROCESSOR...")
    
    cloudwatch = boto3.client('logs')
    lambda_name = 'transaction-processor-dev'
    log_group_name = f'/aws/lambda/{lambda_name}'
    
    try:
        # Obtener los últimos log streams
        response = cloudwatch.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        print("Últimos log streams:")
        for stream in response['logStreams']:
            stream_name = stream['logStreamName']
            first_event = datetime.fromtimestamp(stream['firstEventTimestamp']/1000)
            last_event = datetime.fromtimestamp(stream['lastEventTimestamp']/1000)
            print(f"   {stream_name}")
            print(f"     Primero: {first_event.strftime('%H:%M:%S')}")
            print(f"     Último:  {last_event.strftime('%H:%M:%S')}")
            
            # Obtener los logs de este stream
            print(f"     Logs:")
            log_events = cloudwatch.get_log_events(
                logGroupName=log_group_name,
                logStreamName=stream_name,
                limit=20
            )
            
            for event in log_events['events']:
                message = event['message'].strip()
                if any(keyword in message.lower() for keyword in ['error', 'exception', 'traceback', 'guardar', 'transacc']):
                    print(f"        {message}")
            
            print()
            
    except Exception as e:
        print(f" Error accediendo a logs: {str(e)}")

if __name__ == "__main__":
    check_processor_logs()
