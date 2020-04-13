# Lambda TLS version check

Lambda function to return the tls version of a `host:port` endpoint

Optionally, it can record metrics to CloudWatch.

## Inputs

All inputs are either defined as environment variables or as part of event data. Event data
will take priority over environment variables

`HOSTNAME` - hostname to be checked

`PORT` - http method to use, defaults to 443

`REPORT_AS_CW_METRICS` - set to 1 if you wish to store reported data as CW
custom metrics, 0 otherwise, defaults to 1

`CW_METRICS_NAMESPACE` - if CW custom metrics are being reported, this will determine
their namespace, defaults to 'TcpPortCheck'

## Outputs

By default, following properties will be rendered in output Json

`TLSVersion` - the TLS version as a float 

## Dependencies

Lambda function is having no external dependencies by design, so no additional packaging steps are required
for deploying it, such as doing `pip install [libname]`

## CloudWatch Metrics

In order to get some metrics which you can alert on, `REPORT_AS_CW_METRICS` and `CW_METRICS_NAMESPACE` environment
variables are used. Following metrics will be reported

- `TLSVersion` - the TLS version as a float 

## Deployment

You can either deploy Lambda manually or using [AWS SAM](https://aws.amazon.com/serverless/sam/).


### AWS SAM

Make sure you have set up your AWS credentials in your environment and an available s3 bucket in the same region.

```sh
sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket ${BUCKET}
sam deploy --template-file packaged.yaml --stack-name http-check --capabilities CAPABILITY_IAM
```

## Testing

### AWS SAM

build the code change

```
sam build
```

execute the test

```sh
sam local invoke Check --event test/google.json 
```

## Schedule execution

schedules can be added manually or through the SAM template using cloudwatch scheduled events
