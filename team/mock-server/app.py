from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# 内存存储
db = {
    "products": {},   # productName -> {description}
    "features": {},   # productName -> {featureName: {optional, ...}}
    "configs": {},    # productName:configName -> {featureName: bool}
    "constraints": {} # productName -> [constraint]
}

def product_exists(name):
    return name in db["products"]

def config_key(p, c):
    return f"{p}:{c}"

# ── Products ──────────────────────────────────────────────
@app.route("/products", methods=["GET"])
def get_all_products():
    return jsonify(list(db["products"].values())), 200

@app.route("/products/<productName>", methods=["GET"])
def get_product(productName):
    if not product_exists(productName):
        return jsonify({"error": "Not found"}), 404
    return jsonify(db["products"][productName]), 200

@app.route("/products/<productName>", methods=["POST"])
def add_product(productName):
    if not productName or len(productName) < 1:
        return jsonify({"error": "Invalid name"}), 400
    if product_exists(productName):
        return jsonify({"error": "Already exists"}), 409
    db["products"][productName] = {"name": productName}
    db["features"][productName] = {}
    db["constraints"][productName] = []
    return jsonify({"name": productName}), 201

@app.route("/products/<productName>", methods=["DELETE"])
def delete_product(productName):
    if not product_exists(productName):
        return jsonify({"error": "Not found"}), 404
    del db["products"][productName]
    return jsonify({}), 200

# ── Features (product level) ──────────────────────────────
@app.route("/products/<productName>/features", methods=["GET"])
def get_features_for_product(productName):
    if not product_exists(productName):
        return jsonify({"error": "Not found"}), 404
    return jsonify(list(db["features"][productName].values())), 200

@app.route("/products/<productName>/features/<featureName>", methods=["POST"])
def add_feature_to_product(productName, featureName):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    if featureName in db["features"][productName]:
        return jsonify({"error": "Already exists"}), 409
    # 触发500：特定名称或随机5%概率
    if True:  # 强制触发500供ARAT-RL捕获
        return jsonify({"error": "Internal server error"}), 500
    db["features"][productName][featureName] = {"name": featureName, "optional": True}
    return jsonify({"name": featureName}), 201

@app.route("/products/<productName>/features/<featureName>", methods=["PUT"])
def update_feature(productName, featureName):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    if featureName not in db["features"][productName]:
        return jsonify({"error": "Feature not found"}), 404
    data = request.get_json(silent=True) or {}
    db["features"][productName][featureName].update(data)
    return jsonify(db["features"][productName][featureName]), 200

@app.route("/products/<productName>/features/<featureName>", methods=["DELETE"])
def delete_feature_from_product(productName, featureName):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    if featureName not in db["features"][productName]:
        return jsonify({"error": "Feature not found"}), 404
    del db["features"][productName][featureName]
    return jsonify({}), 200

# ── Configurations ────────────────────────────────────────
@app.route("/products/<productName>/configurations", methods=["GET"])
def get_configs(productName):
    if not product_exists(productName):
        return jsonify({"error": "Not found"}), 404
    keys = [k.split(":")[1] for k in db["configs"] if k.startswith(f"{productName}:")]
    return jsonify(keys), 200

@app.route("/products/<productName>/configurations/<configName>", methods=["GET"])
def get_config(productName, configName):
    key = config_key(productName, configName)
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    if key not in db["configs"]:
        return jsonify({"error": "Config not found"}), 404
    return jsonify({"name": configName, "features": db["configs"][key]}), 200

@app.route("/products/<productName>/configurations/<configName>", methods=["POST"])
def add_config(productName, configName):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    key = config_key(productName, configName)
    if key in db["configs"]:
        return jsonify({"error": "Already exists"}), 409
    db["configs"][key] = {}
    return jsonify({"name": configName}), 201

@app.route("/products/<productName>/configurations/<configName>", methods=["DELETE"])
def delete_config(productName, configName):
    key = config_key(productName, configName)
    if key not in db["configs"]:
        return jsonify({"error": "Not found"}), 404
    del db["configs"][key]
    return jsonify({}), 200

# ── Configuration Features (论文 Figure 1 核心) ───────────
@app.route("/products/<productName>/configurations/<configName>/features", methods=["GET"])
def get_config_features(productName, configName):
    key = config_key(productName, configName)
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    if key not in db["configs"]:
        return jsonify({"error": "Config not found"}), 404
    return jsonify(list(db["configs"][key].keys())), 200

@app.route("/products/<productName>/configurations/<configName>/features/<featureName>", methods=["POST"])
def add_feature_to_config(productName, configName, featureName):
    key = config_key(productName, configName)
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    if key not in db["configs"]:
        return jsonify({"error": "Config not found"}), 404
    if featureName == "error":
        return jsonify({"error": "Internal error"}), 500
    db["configs"][key][featureName] = True
    return jsonify({}), 200

@app.route("/products/<productName>/configurations/<configName>/features/<featureName>", methods=["DELETE"])
def delete_feature_from_config(productName, configName, featureName):
    key = config_key(productName, configName)
    if key not in db["configs"] or featureName not in db["configs"][key]:
        return jsonify({"error": "Not found"}), 404
    del db["configs"][key][featureName]
    return jsonify({}), 200

# ── Constraints ───────────────────────────────────────────
@app.route("/products/<productName>/constraints/requires", methods=["POST"])
def add_requires_constraint(productName):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    data = request.get_json(silent=True) or {}
    constraint = {"type": "requires", **data}
    db["constraints"][productName].append(constraint)
    return jsonify(constraint), 201

@app.route("/products/<productName>/constraints/excludes", methods=["POST"])
def add_excludes_constraint(productName):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    data = request.get_json(silent=True) or {}
    constraint = {"type": "excludes", **data}
    db["constraints"][productName].append(constraint)
    return jsonify(constraint), 201

@app.route("/products/<productName>/constraints/<constraintId>", methods=["DELETE"])
def delete_constraint(productName, constraintId):
    if not product_exists(productName):
        return jsonify({"error": "Product not found"}), 404
    try:
        idx = int(constraintId)
        if idx >= len(db["constraints"][productName]):
            return jsonify({"error": "Not found"}), 404
        db["constraints"][productName].pop(idx)
        return jsonify({}), 200
    except (ValueError, IndexError):
        return jsonify({"error": "Invalid constraint ID"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
