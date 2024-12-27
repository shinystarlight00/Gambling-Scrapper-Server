import traceback
from flask import Flask
from flask import request
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
statusOG = {
    "RustyPot Coinflip": 0,
    "RustyPot Jackpot": 0,

    "BanditCamp Crates": 0,
    "BanditCamp Wheel": 0,
    "BanditCamp Spinner": 0,
    "BanditCamp Misc": 0,

    # "RustClash Roulette": 0,
    # "RustClash Cases": 0,
    # "RustClash Misc": 0,

    "RustMagic Live": 0,
}
status = statusOG.copy()

# Set Status
@app.post('/set')
def setStatus():
    global status
    try:
        data = dict(request.get_json(force=True))
        key = data["key"]

        try: status[key]
        except: status[key] = 0

        if data["status"]: status[key] += 1
        else: status[key] -= 1

        return status
    except:
        print(traceback.format_exc())

# Get Status
@app.get("/get")
def getStatus():
    global status
    print(status)
    try:
        result = {}

        for i in range(len(status.keys())):
            keys = list(status.keys())
            result[keys[i]] = status[keys[i]] > 0

        status = statusOG
        return result
    except:
        print(traceback.format_exc())
        return {}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8484, debug=True, threaded=True)