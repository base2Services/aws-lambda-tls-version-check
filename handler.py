import json
import os
import boto3
import socket
import ssl

class Config:
    """Lambda function runtime configuration"""

    HOSTNAME = 'HOSTNAME'
    PORT = 'PORT'
    CHECK_MAX_SUPPORTED = 'CHECK_MAX_SUPPORTED'
    REPORT_AS_CW_METRICS = 'REPORT_AS_CW_METRICS'
    CW_METRICS_NAMESPACE = 'CW_METRICS_NAMESPACE'
    PROTOCOLS = 'PROTOCOLS'

    def __init__(self, event):
        self.event = event
        self.defaults = {
            self.HOSTNAME: 'example.com',
            self.PORT: 443,
            self.CHECK_MAX_SUPPORTED: '1',
            self.REPORT_AS_CW_METRICS: '1',
            self.CW_METRICS_NAMESPACE: 'TLSVersionCheck',
            self.PROTOCOLS: ['SSLv2','SSLv3','TLSv1','TLSv1.1','TLSv1.2']
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
    def check_max(self):
        return self.__get_property(self.CHECK_MAX_SUPPORTED)
    
    def protocols(self):
        return self.__get_property(self.PROTOCOLS)
        
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
        result = {}
        
        if self.config.check_max == '1':
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            result['MaxVersion'] = self.protocol_to_int(self.get_version(context))
        
        for protocol in self.config.protocols():
            try:
                prot = self.get_protocol(protocol)
                context = ssl.SSLContext(prot)
                version = self.get_version(context,protocol)
                result[protocol] = 1 if version == protocol else 0
            except ValueError as e:
                print(f"Failed TLS connection to {self.config.hostname}:{self.config.port} with error: {e}")
                result[protocol] = 0          
        
        return result
        
    def get_version(self, context, protocol=None):
        try:
            with socket.create_connection((self.config.hostname, self.config.port)) as sock:
                with context.wrap_socket(sock, server_hostname=self.config.hostname) as ssock:
                    return ssock.version()
        except ssl.SSLError as e:
            if e.reason == 'WRONG_VERSION_NUMBER':
                print(f"{self.config.hostname}:{self.config.port} doesn't support TLS protocol {protocol}")
            else:
                print(f"Failed {protocol} TLS connection to {self.config.hostname}:{self.config.port} with error: {e}")
        except Exception as e:
            print(f"Failed {protocol} TLS connection to {self.config.hostname}:{self.config.port} with error: {e}")
        
        return None
            
    def get_protocol(self,protocol):
        
        if protocol == 'SSLv2':
            if ssl.HAS_SSLv2:
                return ssl.PROTOCOL_SSLv2
        elif protocol == 'SSLv3':
            if ssl.HAS_SSLv3:
                return ssl.PROTOCOL_SSLv3
        elif protocol == 'TLSv1':
            if ssl.HAS_TLSv1:
                return ssl.PROTOCOL_TLSv1
        elif protocol == 'TLSv1.1':
            if ssl.HAS_TLSv1_1:
                return ssl.PROTOCOL_TLSv1_1
        elif protocol == 'TLSv1.2':
            if ssl.HAS_TLSv1_2:
                return ssl.PROTOCOL_TLSv1_2
            
        raise ValueError(f"Unknown or unsupported SSL/TLS protocol {protocol} by the client")
    
    def protocol_to_int(self, protocol):
        if protocol == 'SSLv2':
            return 1
        elif protocol == 'SSLv3':
            return 2
        elif protocol == 'TLSv1':
            return 3
        elif protocol == 'TLSv1.1':
            return 4
        elif protocol == 'TLSv1.2':
            return 5
        else:
            return 0

class ResultReporter:
    """Reporting results to CloudWatch"""

    def __init__(self, config):
        self.config = config

    def report(self, result):
        if self.config.cwoptions['enabled'] == '1':
            try:
                endpoint = f"{self.config.hostname}:{self.config.port}"
                cloudwatch = boto3.client('cloudwatch')
                metric_data = []
                
                for check, value in resuls.items():
                    metric_data.append({
                        'MetricName': check,
                        'Dimensions': [
                            {'Name': 'Endpoint', 'Value': endpoint}
                        ],
                        'Unit': 'None',
                        'Value': int(value)
                    })

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
