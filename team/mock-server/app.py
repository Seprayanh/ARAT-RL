from flask import Flask, jsonify, request

app = Flask(__name__)

# 内存存储（模拟数据库）
db = {
    "products": {},       # productName -> {}
    "configs": {},        # productName:configName -> {}
    "features": {}        # productName:configName -> [featureName, ...]
}

# ── 1. 产品 ──────────────────────────────────────────
@app.route("/products/<productName>", methods=["POST"])
def create_product(productName):
    if not productName or len(productName) < 2:
        return jsonify({"error": "Invalid productName"}), 400
    if productName in db["products"]:
        return jsonify({"error": "Product already exists"}), 409
    db["products"][productName] = {}
    return jsonify({"message": f"Product {productName} created"}), 201

@app.route("/products", methods=["GET"])
def list_products():
    return jsonify(list(db["products"].keys())), 200

@app.route("/products/<productName>", methods=["GET"])
def get_product(productName):
    if productName not in db["products"]:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"productName": productName}), 200

@app.route("/products/<productName>", methods=["DELETE"])
def delete_product(productName):
    if productName not in db["products"]:
        return jsonify({"error": "Product not found"}), 404
    del db["products"][productName]
    return jsonify({"message": "Deleted"}), 200

# ── 2. 配置 ──────────────────────────────────────────
@app.route("/products/<productName>/configurations/<configName>", methods=["POST"])
def create_config(productName, configName):
    if productName not in db["products"]:
        return jsonify({"error": "Product not found"}), 404
    key = f"{productName}:{configName}"
    if key in db["configs"]:
        return jsonify({"error": "Config already exists"}), 409
    db["configs"][key] = {}
    db["features"][key] = []
    return jsonify({"message": f"Config {configName} created"}), 201

@app.route("/products/<productName>/configurations", methods=["GET"])
def list_configs(productName):
    if productName not in db["products"]:
        return jsonify({"error": "Product not found"}), 404
    configs = [k.split(":")[1] for k in db["configs"] if k.startswith(f"{productName}:")]
    return jsonify(configs), 200

# ── 3. Feature（论文 Figure 1 核心）─────────────────
@app.route("/products/<productName>/configurations/<configName>/features/<featureName>", methods=["POST"])
def add_feature(productName, configName, featureName):
    key = f"{productName}:{configName}"
    if productName not in db["products"]:
        return jsonify({"error": "Product not found"}), 404
    if key not in db["configs"]:
        return jsonify({"error": "Configuration not found"}), 404
    if featureName in db["features"][key]:
        return jsonify({"error": "Feature already exists"}), 409
    # 模拟偶发服务器错误（让 ARAT-RL 能捕获 500）
    if featureName == "error":
        return jsonify({"error": "Internal error"}), 500
    db["features"][key].append(featureName)
    return jsonify({}), 200    # 论文原始 spec：无结构化响应体

@app.route("/products/<productName>/configurations/<configName>/features", methods=["GET"])
def get_features(productName, configName):
    key = f"{productName}:{configName}"
    if productName not in db["products"]:
        return jsonify({"error": "Product not found"}), 404
    if key not in db["configs"]:
        return jsonify({"error": "Configuration not found"}), 404
    return jsonify(db["features"][key]), 200

@app.route("/products/<productName>/configurations/<configName>/features/<featureName>", methods=["DELETE"])
def delete_feature(productName, configName, featureName):
    key = f"{productName}:{configName}"
    if key not in db["features"] or featureName not in db["features"][key]:
        return jsonify({"error": "Feature not found"}), 404
    db["features"][key].remove(featureName)
    return jsonify({"message": "Deleted"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
