CHECK=tls-version-check
BUCKET=my-bucket
STACKNAME=tls-version-check
AWSREGION=ap-southeast-2
COMMIT=$(shell git rev-parse --verify HEAD)

build-image:
	echo "docker image not required"

build:
	zip "${COMMIT}.zip" "handler.py"

test:
	echo "no python unit tests yet"
	
deploy:
	sam package --region ${AWSREGION} --template-file template.yaml --output-template-file packaged.yaml --s3-bucket ${BUCKET}
	sam deploy --region ${AWSREGION} --template-file packaged.yaml --stack-name ${STACKNAME}-${COMMIT} --capabilities CAPABILITY_IAM
	aws cloudformation wait stack-create-complete --region ${AWSREGION} --stack-name ${STACKNAME}-${COMMIT}
	
lambda-test:
	aws lambda invoke --function-name ${CHECK} --payload file://./test/google.json lambda-test-1.json --log-type Tail --query 'LogResult' --output text | base64 -d
	if grep -q "errorMessage" lambda-test-*.json; then echo "\nLambda tests failed"; exit 1; else echo "\nLambda tests passed";	fi

destroy:
	aws cloudformation delete-stack --region ${AWSREGION} --stack-name ${STACKNAME}-${COMMIT}