from flask import Flask, request, jsonify, g
import asyncio
from main_scratch import main,last_api_response
import json

app = Flask(__name__)

@app.route('/computer_usage/', methods=['POST'])
async def run_main():
    try:
        data = request.json
        if data and 'instruction' in data:
            import sys
            sys.argv = ["main_scratch.py", data['instruction']]              
        await main(g)
        if hasattr(g, "last_api_response") and g.last_api_response:
            with open("last_api_response.json", "w") as json_file:
                json.dump(g.last_api_response, json_file, indent=4)
            return jsonify({"status": "success", "api_response": g.last_api_response}), 200
        else:
            return jsonify({"status": "error", "message": "No API response recorded."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)