import json
import boto3
import uuid
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Tasks')

def lambda_handler(event, context):
    print("EVENTO RECEBIDO:")
    print(json.dumps(event, indent=2))

    http_method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod')
    path = event.get('rawPath') or event.get('path')

    body = {}
    if http_method in ['POST', 'PUT']:
        try:
            raw_body = event.get('body', '{}')
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError as e:
            print("Erro ao decodificar JSON:", str(e))
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Corpo da requisição não é um JSON válido"})
            }

    # POST /tasks
    if http_method == 'POST' and path == '/tasks':
        task_id = str(uuid.uuid4())
        titulo = body.get('titulo')
        descricao = body.get('descricao')
        data = body.get('data')

        item = {
            'id': task_id,
            'titulo': titulo,
            'descricao': descricao,
            'data': data
        }

        table.put_item(Item=item)
        return {"statusCode": 201, "body": json.dumps(item)}

    # GET /tasks/{id}
    if http_method == 'GET' and path.startswith('/tasks/'):
        task_id = event.get('pathParameters', {}).get('id') or path.split('/')[-1]
        res = table.get_item(Key={'id': task_id})
        item = res.get('Item')
        if item:
            return {"statusCode": 200, "body": json.dumps(item)}
        else:
            return {"statusCode": 404, "body": json.dumps({"msg": "Tarefa não encontrada"})}

    # PUT /tasks/{id}
    if http_method == 'PUT' and path.startswith('/tasks/'):
        task_id = event.get('pathParameters', {}).get('id') or path.split('/')[-1]
        titulo = body.get('titulo')
        descricao = body.get('descricao')
        data = body.get('data')

        table.update_item(
            Key={'id': task_id},
            UpdateExpression="SET titulo = :t, descricao = :d, #dt = :dt",
            ExpressionAttributeNames={'#dt': 'data'},
            ExpressionAttributeValues={
                ':t': titulo,
                ':d': descricao,
                ':dt': data
            }
        )
        return {"statusCode": 200, "body": json.dumps({"msg": "Tarefa atualizada"})}

    # DELETE /tasks/{id}
    if http_method == 'DELETE' and path.startswith('/tasks/'):
        task_id = event.get('pathParameters', {}).get('id') or path.split('/')[-1]
        table.delete_item(Key={'id': task_id})
        return {"statusCode": 200, "body": json.dumps({"msg": "Tarefa excluída"})}

    # GET /tasks_by_date?data=dd/mm/yyyy
    if http_method == 'GET' and (path == '/tasks_by_date' or path.startswith('/tasks_by_date')):
        data_param = (event.get('queryStringParameters') or {}).get('data')
        if not data_param:
            return {
                "statusCode": 400,
                "body": json.dumps({"msg": "Parâmetro 'data' é obrigatório"})
            }

        result = table.scan(FilterExpression=Attr('data').eq(data_param))
        return {"statusCode": 200, "body": json.dumps(result['Items'])}

    return {
        "statusCode": 400,
        "body": json.dumps({"msg": "Rota não suportada"})
    }
