#!/bin/bash

# AWS FinOps Analyzer v4.0 Deployment Script
# Complete Clean Architecture Implementation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
STACK_NAME="finops-analyzer-v4"
ENVIRONMENT="production"
AWS_REGION="us-east-1"
S3_BUCKET_NAME="finops-reports-v4-$(date +%s)"
BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
HISTORICAL_DAYS=30
EMAIL_FROM=""
EMAIL_TO=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed."
        exit 1
    fi
    
    # Check zip
    if ! command -v zip &> /dev/null; then
        print_error "zip command is not available."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to validate parameters
validate_parameters() {
    print_status "Validating parameters..."
    
    if [[ -z "$EMAIL_FROM" ]]; then
        print_error "EMAIL_FROM is required. Use --email-from parameter."
        exit 1
    fi
    
    if [[ -z "$EMAIL_TO" ]]; then
        print_error "EMAIL_TO is required. Use --email-to parameter."
        exit 1
    fi
    
    # Validate region
    if ! aws ec2 describe-regions --region-names "$AWS_REGION" &> /dev/null; then
        print_error "Invalid AWS region: $AWS_REGION"
        exit 1
    fi
    
    # Validate historical days
    if [[ $HISTORICAL_DAYS -lt 1 || $HISTORICAL_DAYS -gt 365 ]]; then
        print_error "HISTORICAL_DAYS must be between 1 and 365"
        exit 1
    fi
    
    print_success "Parameters validation passed"
}

# Function to create deployment package
create_deployment_package() {
    print_status "Creating deployment package..."
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    PACKAGE_DIR="$TEMP_DIR/package"
    
    # Create package directory
    mkdir -p "$PACKAGE_DIR"
    
    # Copy source code
    cp -r src/ "$PACKAGE_DIR/"
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip3 install -r requirements.txt -t "$PACKAGE_DIR/" --no-deps
    
    # Create ZIP file
    cd "$PACKAGE_DIR"
    zip -r ../finops-analyzer-v4.zip . -x "*.pyc" "*__pycache__*" "*.git*" "tests/*"
    
    # Move ZIP to current directory
    mv ../finops-analyzer-v4.zip "$OLDPWD/"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    print_success "Deployment package created: finops-analyzer-v4.zip"
}

# Function to check Bedrock access
check_bedrock_access() {
    print_status "Checking Amazon Bedrock access..."
    
    # Try to list foundation models
    if aws bedrock list-foundation-models --region "$AWS_REGION" &> /dev/null; then
        print_success "Bedrock access confirmed"
        
        # Check if specific model is available
        if aws bedrock get-foundation-model --model-identifier "$BEDROCK_MODEL_ID" --region "$AWS_REGION" &> /dev/null; then
            print_success "Bedrock model $BEDROCK_MODEL_ID is available"
        else
            print_warning "Bedrock model $BEDROCK_MODEL_ID may not be available. Please check model access."
        fi
    else
        print_error "Cannot access Amazon Bedrock. Please ensure:"
        print_error "1. Bedrock is available in region $AWS_REGION"
        print_error "2. You have proper IAM permissions"
        print_error "3. Model access is granted in Bedrock console"
        exit 1
    fi
}

# Function to verify SES email
verify_ses_email() {
    print_status "Checking SES email verification..."
    
    # Check if email is verified
    if aws ses get-identity-verification-attributes --identities "$EMAIL_FROM" --region "$AWS_REGION" --query "VerificationAttributes.\"$EMAIL_FROM\".VerificationStatus" --output text 2>/dev/null | grep -q "Success"; then
        print_success "Email $EMAIL_FROM is verified in SES"
    else
        print_warning "Email $EMAIL_FROM is not verified in SES"
        print_warning "Please verify the email address in SES console or the notifications will fail"
    fi
}

# Function to deploy CloudFormation stack
deploy_stack() {
    print_status "Deploying CloudFormation stack..."
    
    # Deploy stack
    aws cloudformation deploy \
        --template-file cloudformation-v4.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            S3BucketName="$S3_BUCKET_NAME" \
            EmailFrom="$EMAIL_FROM" \
            EmailTo="$EMAIL_TO" \
            BedrockModelId="$BEDROCK_MODEL_ID" \
            HistoricalDays="$HISTORICAL_DAYS" \
            Environment="$ENVIRONMENT" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" \
        --tags \
            Application=FinOps-Analyzer \
            Version=4.0 \
            Environment="$ENVIRONMENT" \
            DeployedBy="$(whoami)" \
            DeployedAt="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    if [[ $? -eq 0 ]]; then
        print_success "CloudFormation stack deployed successfully"
    else
        print_error "CloudFormation deployment failed"
        exit 1
    fi
}

# Function to update Lambda function code
update_lambda_code() {
    print_status "Updating Lambda function code..."
    
    # Get function name from stack outputs
    FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
        --output text)
    
    if [[ -z "$FUNCTION_NAME" ]]; then
        print_error "Could not get Lambda function name from stack outputs"
        exit 1
    fi
    
    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://finops-analyzer-v4.zip \
        --region "$AWS_REGION"
    
    if [[ $? -eq 0 ]]; then
        print_success "Lambda function code updated successfully"
    else
        print_error "Failed to update Lambda function code"
        exit 1
    fi
    
    # Wait for update to complete
    print_status "Waiting for function update to complete..."
    aws lambda wait function-updated \
        --function-name "$FUNCTION_NAME" \
        --region "$AWS_REGION"
    
    print_success "Function update completed"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Install test dependencies
    pip3 install pytest pytest-asyncio pytest-cov pytest-mock
    
    # Run unit tests
    python3 -m pytest tests/unit/ -v --cov=src --cov-report=term-missing
    
    if [[ $? -eq 0 ]]; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
        exit 1
    fi
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Get function name
    FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
        --output text)
    
    # Create test event
    TEST_EVENT='{
        "request_type": "analysis",
        "regions": ["'$AWS_REGION'"],
        "analysis_period_days": 7,
        "include_cost_data": true,
        "save_report": false
    }'
    
    # Invoke function
    print_status "Invoking Lambda function for testing..."
    RESULT=$(aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --payload "$TEST_EVENT" \
        --region "$AWS_REGION" \
        response.json)
    
    # Check result
    if [[ $? -eq 0 ]]; then
        STATUS_CODE=$(echo "$RESULT" | jq -r '.StatusCode')
        if [[ "$STATUS_CODE" == "200" ]]; then
            print_success "Deployment test passed"
            
            # Show response summary
            if [[ -f response.json ]]; then
                SUCCESS=$(cat response.json | jq -r '.body.success // false')
                if [[ "$SUCCESS" == "true" ]]; then
                    print_success "Function executed successfully"
                else
                    print_warning "Function executed but returned an error:"
                    cat response.json | jq '.body.error_message // "Unknown error"'
                fi
                rm -f response.json
            fi
        else
            print_error "Function invocation failed with status code: $STATUS_CODE"
            exit 1
        fi
    else
        print_error "Failed to invoke Lambda function"
        exit 1
    fi
}

# Function to display deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo
    print_status "Deployment Information:"
    echo "  Stack Name: $STACK_NAME"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $AWS_REGION"
    echo "  S3 Bucket: $S3_BUCKET_NAME"
    echo
    
    # Get stack outputs
    print_status "Stack Outputs:"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
        --output table
    
    echo
    print_status "Next Steps:"
    echo "1. Verify email addresses in SES console if notifications fail"
    echo "2. Check CloudWatch Logs for function execution details"
    echo "3. Monitor S3 bucket for generated reports"
    echo "4. Review CloudWatch alarms for monitoring"
    echo
    print_status "Useful Commands:"
    echo "  View logs: aws logs tail /aws/lambda/\$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==\`LambdaFunctionName\`].OutputValue' --output text) --follow"
    echo "  List reports: aws s3 ls s3://$S3_BUCKET_NAME/finops-reports/ --recursive"
    echo "  Manual invoke: aws lambda invoke --function-name \$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==\`LambdaFunctionName\`].OutputValue' --output text) --payload '{}' response.json"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --stack-name NAME          CloudFormation stack name (default: finops-analyzer-v4)"
    echo "  --environment ENV          Environment name (default: production)"
    echo "  --region REGION            AWS region (default: us-east-1)"
    echo "  --s3-bucket NAME           S3 bucket name (default: auto-generated)"
    echo "  --email-from EMAIL         Verified SES email for notifications (required)"
    echo "  --email-to EMAIL           Email addresses for notifications (required)"
    echo "  --bedrock-model MODEL      Bedrock model ID (default: anthropic.claude-3-sonnet-20240229-v1:0)"
    echo "  --historical-days DAYS     Days of historical data (default: 30)"
    echo "  --skip-tests               Skip running tests"
    echo "  --skip-deployment-test     Skip deployment test"
    echo "  --help                     Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --email-from admin@company.com --email-to team@company.com"
    echo "  $0 --stack-name my-finops --environment staging --region us-west-2 --email-from admin@company.com --email-to team@company.com"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --s3-bucket)
            S3_BUCKET_NAME="$2"
            shift 2
            ;;
        --email-from)
            EMAIL_FROM="$2"
            shift 2
            ;;
        --email-to)
            EMAIL_TO="$2"
            shift 2
            ;;
        --bedrock-model)
            BEDROCK_MODEL_ID="$2"
            shift 2
            ;;
        --historical-days)
            HISTORICAL_DAYS="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-deployment-test)
            SKIP_DEPLOYMENT_TEST=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    print_status "Starting FinOps Analyzer v4.0 deployment..."
    echo
    
    check_prerequisites
    validate_parameters
    
    if [[ "$SKIP_TESTS" != "true" ]]; then
        run_tests
    fi
    
    create_deployment_package
    check_bedrock_access
    verify_ses_email
    deploy_stack
    update_lambda_code
    
    if [[ "$SKIP_DEPLOYMENT_TEST" != "true" ]]; then
        test_deployment
    fi
    
    show_deployment_info
    
    # Cleanup
    rm -f finops-analyzer-v4.zip
    
    print_success "Deployment completed successfully! 🚀"
}

# Run main function
main