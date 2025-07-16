# type: ignore
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///expense_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Real API Keys configuration
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
app.config['GOOGLE_CALENDAR_CLIENT_ID'] = os.getenv('GOOGLE_CALENDAR_CLIENT_ID')
app.config['GOOGLE_CALENDAR_CLIENT_SECRET'] = os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET')

# Mock API configuration (for demo purposes)
app.config['MOCK_PLAID_ENABLED'] = True
app.config['MOCK_VENMO_ENABLED'] = True

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Initialize Gemini AI (will be configured when API key is provided)
gemini_model = None
if app.config.get('GEMINI_API_KEY'):
    try:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
        gemini_model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"Gemini AI configuration failed: {e}")
        gemini_model = None

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    google_calendar_token = db.Column(db.Text, nullable=True)  # Store OAuth token
    monthly_budget = db.Column(db.Float, default=0.0)
    budget_categories = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PersonalExpense(db.Model):
    __tablename__ = 'personal_expenses'
    
    expense_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Categorized by Gemini
    gemini_confidence = db.Column(db.Float, nullable=True)  # AI confidence score
    receipt_image_url = db.Column(db.String(255), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Group(db.Model):
    __tablename__ = 'groups'
    
    group_id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    role = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class SharedExpense(db.Model):
    __tablename__ = 'shared_expenses'
    
    expense_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'), nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    suggested_split_type = db.Column(db.String(20), nullable=True)  # Gemini suggestion
    split_type = db.Column(db.String(20), default='equal')
    receipt_image_url = db.Column(db.String(255), nullable=True)
    calendar_reminder_id = db.Column(db.String(100), nullable=True)  # Google Calendar event ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExpenseSplit(db.Model):
    __tablename__ = 'expense_splits'
    
    split_id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('shared_expenses.expense_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount_owed = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

class MockPayment(db.Model):
    __tablename__ = 'mock_payments'
    
    payment_id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    to_user = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mock_venmo_id = db.Column(db.String(100), nullable=True)  # Simulated transaction ID
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)
    current_spending = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Gemini AI Helper Functions
def categorize_expense_with_gemini(description, amount):
    """Use Gemini to categorize an expense and provide insights"""
    if not gemini_model:
        # Fallback categorization when Gemini is not available
        return {
            "category": "Other",
            "confidence": 0.5,
            "insight": "Gemini AI not configured - using fallback categorization",
            "budget_tip": "Configure Gemini API key for AI-powered categorization"
        }
    
    try:
        prompt = f"""
        Categorize this expense and provide insights:
        Description: {description}
        Amount: ${amount}
        
        Please respond with JSON in this format:
        {{
            "category": "one of: Food, Transportation, Entertainment, Shopping, Bills, Healthcare, Education, Travel, Other",
            "confidence": 0.95,
            "insight": "Brief insight about this expense",
            "budget_tip": "Optional tip for budgeting"
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        # Parse JSON from response
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        # Fallback categorization
        return {
            "category": "Other",
            "confidence": 0.5,
            "insight": "Unable to categorize automatically",
            "budget_tip": "Consider adding more details for better categorization"
        }

def suggest_split_type_with_gemini(expense_description, amount, group_size):
    """Use Gemini to suggest the best way to split an expense"""
    try:
        prompt = f"""
        Suggest the best way to split this expense among {group_size} people:
        Description: {expense_description}
        Amount: ${amount}
        
        Respond with JSON:
        {{
            "suggested_split": "equal/by_usage/by_income",
            "reasoning": "Why this split makes sense",
            "alternative": "Alternative split option if applicable"
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        return json.loads(response.text.strip())
    except Exception as e:
        return {
            "suggested_split": "equal",
            "reasoning": "Equal split is fair for most shared expenses",
            "alternative": "Consider usage-based if expense varies by person"
        }

def generate_budget_insights_with_gemini(user_expenses, budget_data):
    """Generate personalized budget insights using Gemini"""
    try:
        expense_summary = [f"{exp.category}: ${exp.amount}" for exp in user_expenses[-10:]]
        
        prompt = f"""
        Analyze this user's recent spending and provide insights:
        Recent expenses: {expense_summary}
        Monthly budget: ${budget_data.get('monthly_budget', 0)}
        
        Provide JSON response:
        {{
            "spending_trend": "increasing/decreasing/stable",
            "top_category": "category user spends most on",
            "insight": "Key insight about spending patterns",
            "recommendation": "Actionable recommendation",
            "budget_alert": "Warning if overspending in any category"
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        return json.loads(response.text.strip())
    except Exception as e:
        return {
            "spending_trend": "stable",
            "insight": "Keep tracking expenses for better insights",
            "recommendation": "Continue monitoring your spending habits"
        }

# Google Calendar Helper Functions
def create_calendar_reminder(user_token, expense_description, amount, due_date):
    """Create a Google Calendar reminder for unpaid expenses"""
    try:
        credentials = Credentials.from_authorized_user_info(json.loads(user_token))
        service = build('calendar', 'v3', credentials=credentials)
        
        event = {
            'summary': f'Payment Reminder: {expense_description}',
            'description': f'Don\'t forget to follow up on ${amount} expense: {expense_description}',
            'start': {
                'dateTime': due_date.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': (due_date + timedelta(hours=1)).isoformat(),
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},       # 1 hour before
                ],
            },
        }
        
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return event_result.get('id')
    except Exception as e:
        print(f"Calendar error: {e}")
        return None

# Mock API Functions
def mock_plaid_import_transactions(user_id):
    """Simulate importing transactions from Plaid"""
    mock_transactions = [
        {"description": "Starbucks Coffee", "amount": 4.75, "date": datetime.now() - timedelta(days=1)},
        {"description": "Uber Ride", "amount": 12.50, "date": datetime.now() - timedelta(days=2)},
        {"description": "Grocery Store", "amount": 67.32, "date": datetime.now() - timedelta(days=3)},
        {"description": "Netflix Subscription", "amount": 15.99, "date": datetime.now() - timedelta(days=4)},
    ]
    
    imported_expenses = []
    for transaction in mock_transactions:
        # Use Gemini to categorize
        gemini_result = categorize_expense_with_gemini(transaction["description"], transaction["amount"])
        
        expense = PersonalExpense(
            user_id=user_id,
            amount=transaction["amount"],
            description=transaction["description"],
            category=gemini_result["category"],
            gemini_confidence=gemini_result["confidence"],
            transaction_date=transaction["date"]
        )
        db.session.add(expense)
        imported_expenses.append(expense)
    
    db.session.commit()
    return imported_expenses

def mock_venmo_send_request(from_user_id, to_user_id, amount, description):
    """Simulate sending a Venmo payment request"""
    mock_transaction_id = f"venmo_mock_{datetime.now().timestamp()}"
    
    payment = MockPayment(
        from_user=to_user_id,  # Person who owes money
        to_user=from_user_id,  # Person who paid and is requesting
        amount=amount,
        mock_venmo_id=mock_transaction_id,
        status='pending'
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return {
        "transaction_id": mock_transaction_id,
        "status": "sent",
        "message": f"Mock payment request for ${amount} sent successfully"
    }

# Basic Routes
@app.route('/')
def index():
    return jsonify({
        'message': 'Divy - Personal & Social Expense Manager API',
        'version': '2.0.0',
        'status': 'running',
        'features': ['Gemini AI Integration', 'Google Calendar Reminders', 'Mock Plaid/Venmo']
    })

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception:
        db_status = 'disconnected'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'gemini_ai': 'configured' if app.config.get('GEMINI_API_KEY') else 'not configured',
        'google_calendar': 'configured' if app.config.get('GOOGLE_CALENDAR_CLIENT_ID') else 'not configured'
    })

# Authentication Routes (same as before)
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            monthly_budget=data.get('monthly_budget', 0.0)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        access_token = create_access_token(identity=new_user.user_id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'user_id': new_user.user_id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, data['password']):
            access_token = create_access_token(identity=user.user_id)
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Personal Expense Routes with Gemini Integration
@app.route('/api/personal/expenses', methods=['POST'])
@jwt_required()
def add_personal_expense():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Use Gemini to categorize and provide insights
        gemini_result = categorize_expense_with_gemini(data['description'], data['amount'])
        
        expense = PersonalExpense(
            user_id=user_id,
            amount=data['amount'],
            description=data['description'],
            category=gemini_result['category'],
            gemini_confidence=gemini_result['confidence'],
            transaction_date=datetime.fromisoformat(data['transaction_date']),
            is_recurring=data.get('is_recurring', False)
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'expense': {
                'expense_id': expense.expense_id,
                'amount': expense.amount,
                'description': expense.description,
                'category': expense.category,
                'gemini_insight': gemini_result.get('insight'),
                'budget_tip': gemini_result.get('budget_tip')
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personal/import-mock', methods=['POST'])
@jwt_required()
def import_mock_transactions():
    """Simulate importing transactions from Plaid"""
    try:
        user_id = get_jwt_identity()
        imported_expenses = mock_plaid_import_transactions(user_id)
        
        return jsonify({
            'message': f'Successfully imported {len(imported_expenses)} transactions',
            'expenses': [{
                'description': exp.description,
                'amount': exp.amount,
                'category': exp.category,
                'confidence': exp.gemini_confidence
            } for exp in imported_expenses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Shared Expense Routes with Gemini Integration
@app.route('/api/shared/expenses', methods=['POST'])
@jwt_required()
def add_shared_expense():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get group info for split suggestion
        group = Group.query.get(data['group_id'])
        group_size = GroupMember.query.filter_by(group_id=data['group_id']).count()
        
        # Use Gemini to suggest split type
        split_suggestion = suggest_split_type_with_gemini(
            data['description'], 
            data['amount'], 
            group_size
        )
        
        expense = SharedExpense(
            group_id=data['group_id'],
            paid_by=user_id,
            amount=data['amount'],
            description=data['description'],
            category=data.get('category', 'Other'),
            suggested_split_type=split_suggestion['suggested_split'],
            split_type=data.get('split_type', 'equal')
        )
        
        db.session.add(expense)
        db.session.flush()  # Get the expense_id
        
        # Create splits for group members
        group_members = GroupMember.query.filter_by(group_id=data['group_id']).all()
        split_amount = data['amount'] / len(group_members)
        
        for member in group_members:
            if member.user_id != user_id:  # Don't create split for person who paid
                split = ExpenseSplit(
                    expense_id=expense.expense_id,
                    user_id=member.user_id,
                    amount_owed=split_amount
                )
                db.session.add(split)
        
        db.session.commit()
        
        return jsonify({
            'expense': {
                'expense_id': expense.expense_id,
                'amount': expense.amount,
                'description': expense.description,
                'split_suggestion': split_suggestion
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Mock Payment Routes
@app.route('/api/payments/mock-venmo-request', methods=['POST'])
@jwt_required()
def send_mock_payment_request():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        result = mock_venmo_send_request(
            user_id,
            data['to_user_id'],
            data['amount'],
            data['description']
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Insights Routes
@app.route('/api/insights/budget', methods=['GET'])
@jwt_required()
def get_budget_insights():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        recent_expenses = PersonalExpense.query.filter_by(user_id=user_id).order_by(PersonalExpense.created_at.desc()).limit(20).all()
        
        insights = generate_budget_insights_with_gemini(recent_expenses, {
            'monthly_budget': user.monthly_budget or 0.0
        })
        
        return jsonify(insights), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers (same as before)
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is required'}), 401

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )
