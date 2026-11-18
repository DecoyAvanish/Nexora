from flask import Blueprint,current_app,jsonify
public_blueprint=Blueprint("public_content",__name__)
@public_blueprint.get("/public/model-card")
def model_card():return jsonify(current_app.extensions["public_content"].model_card())
@public_blueprint.get("/public/architecture")
def architecture():return jsonify(current_app.extensions["public_content"].architecture())
@public_blueprint.get("/public/demo")
def demo():return jsonify(current_app.extensions["public_content"].demo())
