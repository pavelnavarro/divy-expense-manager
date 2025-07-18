# backend/routes/gemini_routes.py
from flask import Blueprint, request, jsonify
from backend.utils.gemini_utils import _MODEL

gemini_bp = Blueprint('gemini', __name__)

@gemini_bp.route('/api/gemini/payments', methods=['POST'])
def get_payment_suggestions():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    
    if not _MODEL or not prompt:
        return jsonify(output="Gemini model not available or prompt missing."), 400

    try:
        response = _MODEL.generate_content(prompt)
        return jsonify(output=response.text), 200
    except Exception as e:
        return jsonify(output="Error: " + str(e)), 500
