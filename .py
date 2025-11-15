#!/usr/bin/env python3
import boto3
from datetime import datetime, timezone

def check_processor_logs_detailed():
    logs = boto3.client('logs')
    
    print("=== LOGS DETALLADOS DEL PROCESSOR ===\n")
    
    log_group = '/aws/lambda/transaction-processor-dev'
    
    try:
        # Obtener el log stream más reciente
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        for stream in streams['logStreams']:
            stream_name = stream['logStreamName']
            print(f"📋 Log Stream: {stream_name}")
            print(f"   Último evento: {datetime.fromtimestamp(stream['lastEventTimestamp']/1000, tz=timezone.utc).strftime('%H:%M:%S')}")
            
            # Obtener logs de este stream
            log_events = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                limit=20
            )
            
            print("   Mensajes recientes:")
            for event in log_events['events']:
                message = event['message'].strip()
                # Filtrar mensajes relevantes
                if any(keyword in message.lower() for keyword in ['procesando', 'transaccion', 'guard', 'error', 'monto', 'pago']):
                    print(f"     🔍 {message}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_processor_logs_detailed()