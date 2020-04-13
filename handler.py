import json
import os
import boto3
import socket
import ssl

class Config:
    """Lambda function runtime configuration"""

    HOSTNAME = 'HOSTNAME'
    PORT = 'PORT'
    REPORT_AS_CW_METRICS = 'REPORT_AS_CW_METRICS'
    CW_METRICS_NAMESPACE = 'CW_METRICS_NAMESPACE'

    def __init__(self, event):
        self.event = event
        self.defaults = {
            self.HOSTNAME: 'example.com',
            self.PORT: 443,
            self.REPORT_AS_CW_METRICS: '1',
            self.CW_METRICS_NAMESPACE: 'TLSVersionCheck',
        }

    def __get_property(self, property_name):
        if property_name in self.event:
            return self.event[property_name]
        if property_name in os.environ:
            return os.environ[property_name]
        if property_name in self.defaults:
            return self.defaults[property_name]
        return None

    @property
    def hostname(self):
        return self.__get_property(self.HOSTNAME)

    @property
    def port(self):
        return self.__get_property(self.PORT)

    @property
    def timeout(self):
        return self.__get_property(self.TIMEOUT)

    @property
    def reportbody(self):
        return self.__get_property(self.REPORT_RESPONSE_BODY)

    @property
    def cwoptions(self):
        return {
            'enabled': self.__get_property(self.REPORT_AS_CW_METRICS),
            'namespace': self.__get_property(self.CW_METRICS_NAMESPACE),
        }


class TLSVerionCheck:
    """Execution of tls version check"""

    def __init__(self, config):
        self.config = config

    def execute(self):
        context = ssl.create_default_context()
        try:
            with socket.create_connection((self.config.hostname, self.config.port)) as sock:
                with context.wrap_socket(sock, server_hostname=self.config.hostname) as ssock:
                    version = ssock.version()

            result = {
                'TLSVersion': version.strip('TLSv')
            }
            print(f"TLS Version: {version}")
            # return structure with data
            return result
        except Exception as e:
            print(f"Failed TLS connection to {self.config.hostname}:{self.config.port}\n{e}")
            return {'Version': 0, 'Reason': str(e)}


class ResultReporter:
    """Reporting results to CloudWatch"""

    def __init__(self, config):
        self.config = config

    def report(self, result):
        if self.config.cwoptions['enabled'] == '1':
            try:
                endpoint = f"{self.config.hostname}:{self.config.port}"
                cloudwatch = boto3.client('cloudwatch')
                metric_data = [{
                    'MetricName': 'TLSVersion',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint}
                    ],
                    'Unit': 'None',
                    'Value': float(result['TLSVersion'])
                }]

                result = cloudwatch.put_metric_data(
                    MetricData=metric_data,
                    Namespace=self.config.cwoptions['namespace']
                )
                
                print(f"Sent data to CloudWatch requestId=:{result['ResponseMetadata']['RequestId']}")
            except Exception as e:
                print(f"Failed to publish metrics to CloudWatch:{e}")


def run_check(event, context):
    """Lambda function handler"""

    config = Config(event)
    check = TLSVerionCheck(config)

    result = check.execute()

    # report results
    ResultReporter(config).report(result)

    result_json = json.dumps(result, indent=4)
    # log results
    print(f"Result of checking  {config.hostname}:{config.port}\n{result_json}")

    # return to caller
    return result
