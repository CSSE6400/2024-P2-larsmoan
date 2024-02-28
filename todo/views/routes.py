from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
} 
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    query = Todo.query

    completed = request.args.get('completed')
    if completed and completed.lower() == 'true':  # Case-insensitive comparison
        query = query.filter(Todo.completed == True)  #Database stores booleans

    # How many days ahead we want to get todos for
    window = int(request.args.get('window', 0))  # Default to 0 days
    if window:
        today = datetime.today()
        cutoff = today + timedelta(days=window)  
        query = query.filter(Todo.deadline_at <= cutoff)    #Not sure if the limit should be < or <=

    todos = query.all()   
    result = [todo.to_dict() for todo in todos]

    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    todo_columns = [column.key for column in Todo.__table__.columns]   #Valid columns in the database

    title = request.json.get('title')
    if not title:
        return jsonify({"Error": "No title present, can't be added to DB"}), 400
    
    #Not add a todo if it containts unknown fields
    unknown_fields = set(request.json.keys()) - set(todo_columns)
    if unknown_fields:
        return jsonify({"Error": f"Unknown fields in the request: {', '.join(unknown_fields)}"}), 400

    
    todo = Todo(
        title = request.json.get('title'),
        description = request.json.get('description'),
        completed = request.json.get('completed', False)
        )
    
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))

    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)

    todo_columns = [column.key for column in Todo.__table__.columns]   #Valid columns in the database
    unknown_fields = set(request.json.keys()) - set(todo_columns)

    if unknown_fields:
        return jsonify({"Error": f"Unknown fields in the request: {', '.join(unknown_fields)}"}), 400

    if todo is None:
        return jsonify({"Error": "todo cant be found"}), 404
    
    if request.json.get('id') and request.json.get('id') != todo.id:
        return jsonify({"Error": "Tried altering the id of a known entry"}), 400
    
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()
    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
       return jsonify({}), 200
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
