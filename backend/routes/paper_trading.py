"""Authenticated paper-order and portfolio endpoints."""

from flask import Blueprint, current_app, jsonify, request

paper_blueprint = Blueprint("paper_trading", __name__)


def _user(): return current_app.extensions["identity"].user_id(request)


@paper_blueprint.get("/paper/account")
def account(): return jsonify(current_app.extensions["paper_execution"].account(_user()))


@paper_blueprint.get("/paper/orders")
def orders(): return jsonify({"orders": current_app.extensions["paper_execution"].orders(_user())})


@paper_blueprint.post("/paper/orders")
def place_order(): return jsonify(current_app.extensions["paper_execution"].place_order(_user(), request.get_json(silent=True) or {})), 201


@paper_blueprint.post("/paper/orders/<order_id>/cancel")
def cancel_order(order_id): return jsonify(current_app.extensions["paper_execution"].cancel(_user(), order_id))


@paper_blueprint.get("/paper/ledger")
def ledger(): return jsonify({"entries": current_app.extensions["paper_execution"].ledger(_user())})
