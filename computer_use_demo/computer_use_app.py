from flask import Flask, request, jsonify
import asyncio
from main_scratch import main 
app = Flask(__name__)

@app.route('/computer_use/', methods=['POST'])
async def run_main():
    try:
        data = request.json
        if data and 'instruction' in data:
            import sys
            sys.argv = ["main_scratch.py", data['instruction']]              
        result = await main()
        return jsonify({"status": "success", "result_json": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)