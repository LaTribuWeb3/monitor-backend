from flask import Flask
from flask_cors import CORS, cross_origin
from flask import jsonify
import json
import os

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route("/")
@cross_origin()
def root():
    return "Hello"


@app.route("/overview/<client_id>")
@cross_origin()
def overview(client_id):
    f = open(f"{client_id}/overview.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/risk_params/<client_id>")
@cross_origin()
def risk_params(client_id):
    f = open(f"{client_id}/risk_params.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/oracles/<client_id>")
@cross_origin()
def oracles(client_id):
    f = open(f"{client_id}/oracles.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/accounts/<client_id>")
@cross_origin()
def accounts(client_id):
    f = open(f"{client_id}/accounts.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/dex_liquidity/<client_id>")
@cross_origin()
def dex_liquidity(client_id):
    f = open(f"{client_id}/dex_liquidity.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/usd_volume_for_slippage/<client_id>")
@cross_origin()
def usd_volume_for_slippage(client_id):
    f = open(f"{client_id}/usd_volume_for_slippage.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/assumptions_vs_reality/<client_id>")
@cross_origin()
def assumptions_vs_reality(client_id):
    f = open(f"{client_id}/assumptions_vs_reality.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/assets_std_ratio/<client_id>")
@cross_origin()
def assets_std_ratio(client_id):
    f = open(f"{client_id}/assets_std_ratio.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/simulation_configs/<client_id>")
@cross_origin()
def simulation_configs(client_id):
    f = open(f"{client_id}/simulation_configs.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/current_simulation_risk/<client_id>")
@cross_origin()
def current_simulation_risk(client_id):
    f = open(f"{client_id}/current_simulation_risk.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/lending_platform_current/<client_id>")
@cross_origin()
def lending_platform_current(client_id):
    f = open(f"{client_id}/lending_platform_current.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/whale_accounts/<client_id>")
@cross_origin()
def whale_accounts(client_id):
    f = open(f"{client_id}/whale_accounts.json")
    j = json.load(f)
    return jsonify(j)


@app.route("/open_liquidations/<client_id>")
@cross_origin()
def open_liquidations(client_id):
    f = open(f"{client_id}/open_liquidations.json")
    j = json.load(f)
    return jsonify(j)

@app.route("/current_simulation_config/<client_id>")
@cross_origin()
def current_simulation_config(client_id):
    f = open(f"{client_id}/current_simulation_config.json")
    j = json.load(f)
    return jsonify(j)

@app.route("/stability_pool/<client_id>")
@cross_origin()
def stability_pool(client_id):
    f = open(f"{client_id}/stability_pool.json")
    j = json.load(f)
    return jsonify(j)



if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
