# SISTEMA-GUATEPASS

IMPORTANTE TENER PERMISOS DE IAM PARA CREAR ROLES (MEJOR TENER PERMISOS DE TODO POR SI ACASO)
Construir
sam build

Deployear
sam deploy --guided
    Stack Name: guatepass-stack
    AWS Region: us-east-1
    Confirm changes: Y

Verificar Creación
aws cloudformation describe-stacks --stack-name guatepass-stack --query 'Stacks[0].Outputs'
API_URL=$(aws cloudformation describe-stacks --stack-name guatepass-stack --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)
echo "API URL: $API_URL"

CARGAR DATA
python scripts/verify_data.py

VERIFICAR QUE SE HAYAN SUBIDO
python scripts/verify_data.py



TEST DE WEBHOOK
./scripts/test_webhook.sh
