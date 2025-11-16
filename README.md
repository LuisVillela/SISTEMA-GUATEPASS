# SISTEMA-GUATEPASS

IMPORTANTE TENER PERMISOS DE IAM PARA CREAR ROLES (MEJOR TENER PERMISOS DE TODO POR SI ACASO)
NECESITA PYTHON 3.12
AWS CLI
SAM CLI

Deployear
sam deploy --guided
    Stack Name: guatepass-stack
    AWS Region: us-east-1
    Confirm changes: Y

CARGAR DATA
python scripts/load_initial_data.py
python scripts/populate_tags.py

VERIFICAR QUE SE HAYAN SUBIDO
python scripts/verify_data.py


TEST DE WEBHOOK
./scripts/test_webhook.sh


VERIFICAR PROCESSOR
sleep 120
./scripts/test_webhook.sh
./scripts/verify_processor.sh
sleep 45
python scripts/check_transactions.py

        Stack Name [guatepass-stack]:
        AWS Region [us-east-1]: 
        Parameter Environment [dev]: 
        #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
        Confirm changes before deploy [y/N]: y
        #SAM needs permission to be able to create roles to connect to the resources in your template
        Allow SAM CLI IAM role creation [Y/n]: y
        #Preserves the state of previously provisioned resources when an operation fails
        Disable rollback [y/N]: y
        WebhookValidatorFunction has no authentication. Is this okay? [y/N]: y
        PaymentHistoryFunction has no authentication. Is this okay? [y/N]: y
        InvoiceHistoryFunction has no authentication. Is this okay? [y/N]: y
        TagsManagementFunction has no authentication. Is this okay? [y/N]: y
        TagsManagementFunction has no authentication. Is this okay? [y/N]: y
        TagsManagementFunction has no authentication. Is this okay? [y/N]: y
        TagsManagementFunction has no authentication. Is this okay? [y/N]: y
        Save arguments to configuration file [Y/n]: n

CORRER TODO
CONSTRUIR Y SUBIR A AWS
sam build
sam deploy --guided
    Stack Name: guatepass-stack
    AWS Region: us-east-1
    Confirm changes: Y
CARGAR DATA
python scripts/load_initial_data.py
python scripts/populate_tags.py
CORRER TESTS
python tests/test_all.py (correr tests de los 3 modulos diferentes) -> SUCIO
DASHBOARDS
python scripts/create_dashboard.py (crear dashboards)
python scripts/verify_monitoring.py (verificar creación de dashboards)

logs ->  Busca: /aws/lambda/notification-handler-dev
