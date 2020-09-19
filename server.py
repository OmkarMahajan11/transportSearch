from flask import Flask
from flask import request
import json
import csv
import random
import jwt

# id is internally assigned. It is a unique random number between 1 to 100
# register method JSON is name, contact number, address

app = Flask(__name__)

def authenticate(auth_token):
      with open('data/auth_file.txt', 'r') as f:
          l = f.read().split('\n')
      if auth_token not in l:
          return json.dumps({"message":"authentication failed"})

def access(auth_token):
    decoded = jwt.decode(auth_token, "imperium")
    username = decoded["username"]
    with open('data/user_creds.csv', 'r') as f:
        reader = csv.reader(f)
        l = list(reader)[1:]
    for i in range(len(l)):
        if l[i][1] == username:
            id = l[i][0]
    with open('data/user.csv', 'r') as f:
        reader = csv.reader(f)
        l = list(reader)[1:] 
    for i in range(len(l)):               
        if l[i][0] == id:
            return l[i][-1]

@app.route('/register', methods=["POST"])
def register():
    newuser = [request.json["name"], request.json["contact_number"], request.json["address"]]
    usercreds = [request.json["username"], request.json["password"]]
    with open('data/user.csv', 'r', newline='') as f:
        reader = csv.reader(f)
        l = list(reader)
    id = random.randint(1, 100)
    while id in [i[0] for i in l[1:]]:
        id = random.randint(1, 100)
    newuser.insert(0, id)
    usercreds.insert(0, id)
    l.append(newuser)
    with open('data/user.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(l)
    with open('data/user_creds.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(usercreds)    
    return json.dumps({"message":"registeration successful"})

@app.route('/login', methods=['POST'])
def login():
    username = request.json["username"]
    password = request.json["password"]
    with open('data/user_creds.csv', 'r', newline='') as f:
        reader = csv.reader(f)
        l = list(reader)[1:]
    uflag = False 
    pflag = False    
    for i in l:        
        if i[1] == username:
            uflag = True
            if i[2] == password:
                pflag = True
                break
    if not uflag:
        return json.dumps({"login":"failed", "message":"no such user"})
    elif not pflag:
        return json.dumps({"login":"failed", "message":"incorrect password"})
    else:
        payload = {"username":username, "password":password}
        key = "imperium"
        auth_token = jwt.encode(payload, key)
        with open("data/auth_file.txt", 'a') as f:
            f.write(auth_token.decode())
            f.write('\n')
        return json.dumps({"login":"successful", "auth_token":auth_token.decode()})
         
@app.route('/modify', methods=['PATCH'])
def modify():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    decoded = jwt.decode(auth_token, "imperium")
    username = decoded["username"]
    password = decoded["password"]    
    new_password = request.json['new_password']
    with open('data/user_creds.csv', 'r', newline='') as f:
        reader = csv.reader(f)
        l = list(reader)      
    for i in l:        
        if i[1] == username:
            if i[2] == password:
                i[2] = new_password
            break    
    with open('data/user_creds.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(l)
    return json.dumps({"message":"password modified sussesfully"})

@app.route("/delete", methods=["DELETE"])
def delete():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    decoded = jwt.decode(auth_token, "imperium")
    username = decoded["username"]
    # remove form user creds file    
    with open('data/user_creds.csv', 'r', newline='') as f:
        reader = csv.reader(f)
        l = list(reader)  
    for i in l:
        if i[1] == username:
            id = i[0]
            l.remove(i)
    with open('data/user_creds.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(l)
    # remove from user file
    with open('data/user.csv', 'r', newline='') as f:
        reader = csv.reader(f)
        l1 = list(reader)           
    for i in l1:
        if i[0] == id:
            l1.remove(i)
    with open('data/user.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(l1)   
    with open('data/auth_file.txt', 'r') as f:
          l = f.read().split('\n')
    for i in l:
        if auth_token == i:
            l.remove(i)
    with open('data/auth_file.txt', 'w') as f:
          for i in l:
              f.write(i)
              f.write('\n')                       
    return json.dumps({"message":"user deleted successfully"})

@app.route('/user/list', methods=["GET"])
def userlist():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}    
    headers = ["id", "name", "contact_number", "address", "access"]    
    with open('data/user.csv', newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)   
        l = list(reader)[1:]
    return json.dumps({"users":l})     

@app.route("/bus/create", methods=["POST"])
def create_bus():
    newbus = [request.json["id"], request.json["bus_number"], request.json["departure_loc"], request.json["arrival_loc"], request.json["journey_duration"], request.json["fare"]]
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"} 
    with open('data/buses.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(newbus)
    return json.dumps({"message":"New bus created successfully"})

@app.route("/bus/list", methods=["POST"])
def bus_details():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}
    headers = ["id","bus_number","departure_loc","arrival_loc","journey_duration","fare"]    
    with open("data/buses.csv", 'r',newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)
        l = list(reader)[1:]
    return json.dumps({"busess":l})        

@app.route("/bus/search", methods=["POST"])
def search_bus():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    headers = ["id", "bus_number", "departure_loc", "arrival_loc", "journey_duration", "fare"]    
    search_n = request.json["bus_number"]
    with open("data/buses.csv", 'r', newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)
        l = list(reader)   
    for i in l:
        if i["bus_number"] == str(search_n):
            return json.dumps(i)    
    return json.dumps({"message":"no such bus"})

@app.route("/bus/delete", methods=["DELETE"])
def delete_bus():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}
    with open("data/buses.csv", 'r', newline='') as f:
        reader = csv.reader(f)
        l = list(reader)
    for i in l:
        if i[1] == str(del_n):
            l.remove(i)
    with open("data/buses.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(l)
    return json.dumps({"message":"deletion successful"})

# bus number is the primary key

@app.route("/bus/modify", methods=["PATCH"])
def modify_bus():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}    
    headers = ["id", "bus_number", "departure_loc", "arrival_loc", "journey_duration", "fare"]     
    with open("data/buses.csv", 'r', newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)
        l = list(reader) 
    flag = False    
    for i in l:
        if i["bus_number"] == str(request.json["bus_number"]):
            i["departure_loc"] = request.json["departure_loc"]
            i["arrival_loc"] = request.json["arrival_loc"]
            i["journey_duration"] = request.json["journey_duration"]
            i["fare"] = request.json["fare"]    
            flag = True
            break
    if not flag:
        return json.dumps({"message":"no such bus"})
    with open("data/buses.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerows(l)         
    return json.dumps({"message":"modification successful"})            

@app.route("/train/create", methods=["POST"])
def create_train():
    newtrain = [request.json["id"], request.json["train_number"], request.json["departure_loc"], request.json["arrival_loc"], request.json["journey_duration"], request.json["fare"]]
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}    
    with open('data/trains.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(newtrain)
    return json.dumps({"message":"New train created successfully"})    

@app.route("/train/list", methods=["POST"])
def train_details():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}    
    headers = ["id","train_number","departure_loc","arrival_loc","journey_duration","fare"]    
    with open("data/trains.csv", 'r',newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)
        l = list(reader)[1:]
    return json.dumps({"trains":l}) 

@app.route("/train/search", methods=["POST"])
def search_train():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    headers = ["id", "train_number", "departure_loc", "arrival_loc", "journey_duration", "fare"]    
    search_n = request.json["train_number"]
    with open("data/trains.csv", 'r', newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)
        l = list(reader)   
    for i in l:
        if i["train_number"] == str(search_n):
            return json.dumps(i)    
    return json.dumps({"message":"no such train"})

@app.route("/train/delete", methods=["DELETE"])
def delete_train():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}    
    del_n = request.json["train_number"]
    with open("data/trains.csv", 'r', newline='') as f:
        reader = csv.reader(f)
        l = list(reader)
    for i in l:
        if i[1] == str(del_n):
            l.remove(i)
    with open("data/trains.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(l)
    return json.dumps({"message":"deletion successful"})

@app.route("/train/modify", methods=["PATCH"])
def modify_train():
    auth_token = request.json['auth_token']
    res = authenticate(auth_token)
    if res is not None:
        return res
    if access(auth_token) == "user":
        return {"access":"denied", "message":"admin acess required"}    
    headers = ["id", "train_number", "departure_loc", "arrival_loc", "journey_duration", "fare"]     
    with open("data/trains.csv", 'r', newline='') as f:
        reader = csv.DictReader(f, fieldnames=headers)
        l = list(reader) 
    search_n = request.json["train_number"]   
    flag = False
    for i in l:
        if i["train_number"] == str(search_n):
            i["departure_loc"] = request.json["departure_loc"]
            i["arrival_loc"] = request.json["arrival_loc"]
            i["journey_duration"] = request.json["journey_duration"]
            i["fare"] = request.json["fare"]    
            flag = True
            break
    if not flag:
        return json.dumps({"message":"no such train"})
    with open("data/trains.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerows(l) 
    return json.dumps({"message":"modification successful"})  