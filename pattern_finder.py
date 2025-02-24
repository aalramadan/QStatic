import json
import sys

with open("out.json") as file:
    qubit_data = json.load(file)

source_code_file = qubit_data["_filename"].replace(".xml","")
del qubit_data["_filename"]
print(source_code_file)

time_data = {}
for qubit in qubit_data:
    for action in qubit_data[qubit]["actions"]:
        time = action["time"]
        if time not in time_data:
            time_data[time] = []
        time_data[time].append(action | {"qubit":qubit})
keys = list(time_data.keys())
keys.sort()
time_data = {i:time_data[i] for i in keys}


patterns = {"horizontal-itr":[],"vertical-itr":[],"diagonal-itr":[],"recursion":[],"hadamard-cnot":[],"encapsulation":[]}

# Find Horizontal Iteration
for qubit in qubit_data:
    #print("QUBIT:",qubit)
    last_action = None
    count = 0
    lines = []
    for action in qubit_data[qubit]["actions"]:
        if "gate-call" in action["action"]:
            if last_action == action["type"].replace("c",""):
                count += 1
                lines += [action["line"]]
            else:
                if count >= 3:
                    patterns["horizontal-itr"].append({"qubit":qubit,"local":action["local_name"],"gate":last_action,"num":count,"lines":lines})
                last_action = action["type"].replace("c","")
                count = 1
                lines = [action["line"]]

    if count >= 3:
        patterns["horizontal-itr"].append({"qubit":qubit,"local":action["local_name"],"gate":last_action,"num":count,"lines":lines})

if "--refactor-horizontal-itr" in sys.argv:
    with open(source_code_file,'r') as file:
        code_text = file.readlines()

    for pattern in patterns["horizontal-itr"]:
        for_str = "for uint i in [0:" + str(pattern["num"])+"] {\n    "+pattern["gate"] + " " + pattern["local"] + ";\n}\n"

    start_line = pattern["lines"][0]
    code_text[start_line-1] = for_str


    for line in pattern["lines"][1:]:
        code_text[line-1] = ""

    with open(source_code_file+".horizontal_refactor",'w') as file:
        file.write("".join(code_text))


# Find Vertical Iteration
qubits = []
last_action = None
for time in time_data:
    for action in time_data[time]:
        if "gate-call" in action["action"]:
            if last_action == action["type"].replace("c","") and action["qubit"] not in qubits:
                qubits.append(action["qubit"])
            else:
                if len(qubits) >= 3:
                    patterns["vertical-itr"].append({"qubits":",".join(qubits),"gate":last_action})
                qubits = [action["qubit"]]
                last_action = action["type"].replace("c","")
if len(qubits) >= 3:
    patterns["vertical-itr"].append({"qubits":",".join(qubits),"gate":last_action})


# Find Diagonal Iteration
current_action = None
chained_qubits = []




# Find Recursion
for qubit in qubit_data:
    for action in qubit_data[qubit]["actions"]:
        if "gate-call" in action["action"]:
            if len(action["ctrl"].split(",")) >= 2:
                patterns["recursion"].append({"qubit":qubit,"gate":action["type"],"ctrl-qubits":action["ctrl"].split(",")})


# Find Hadamard-CNOTs
## First, find all qubits that have at least 2 H gates
candidates = []
for qubit in qubit_data:
    for i in range(len(qubit_data[qubit]["actions"])-2):
        action = qubit_data[qubit]["actions"][i]
        if action["action"] == "gate-call" and action["type"] == "h":
            next_action = qubit_data[qubit]["actions"][i+1]
            if next_action["action"] == "ctrl-gate-call" and next_action["type"] == "cx":
                third_action = qubit_data[qubit]["actions"][i+2]
                if third_action["action"] == "gate-call" and third_action["type"] == "h":
                    candidates.append([action | {"qubit":qubit},next_action | {"qubit":qubit},third_action | {"qubit":qubit}])

for candidate in candidates:
    ctrl_qubit = candidate[1]["ctrl"]
    ctrl_time = candidate[1]["time"]
    for i in range(len(qubit_data[ctrl_qubit]["actions"])-1):
        action = qubit_data[ctrl_qubit]["actions"][i]
        if action["time"] == ctrl_time:
            assert action["action"] == "ctrl"
            prev_action = qubit_data[ctrl_qubit]["actions"][i-1]
            next_action = qubit_data[ctrl_qubit]["actions"][i+1]
            if prev_action["action"] == "gate-call" and prev_action["type"] == "h" and next_action["action"] == "gate-call" and next_action["type"] == "h":
                patterns["hadamard-cnot"].append({"orig-target-qubit":candidate[0]["qubit"],"orig-ctrl-qubit":ctrl_qubit,
                    "local-target-qubit":candidate[0]["local_name"],"local-ctrl-qubit":action["local_name"],
                    "h_lines":[prev_action["line"],candidate[0]["line"],next_action["line"],candidate[2]["line"]],
                    "cnot_line":candidate[1]["line"]})
                break

# Refactor Hadamard
if "--refactor-hadamard" in sys.argv:
    # get original code
    with open(source_code_file,'r') as file:
        code_text = file.readlines()

    for pattern in patterns["hadamard-cnot"]:
        changed_cnot = "cx " + pattern["local-target-qubit"] + ", " + pattern["local-ctrl-qubit"] + ";\n"
        code_text[pattern["cnot_line"]-1] = changed_cnot
        for line in pattern["h_lines"]:
            code_text[line-1] = "\n"

    with open(source_code_file+".hadamard_refactor",'w') as file:
        file.write("".join(code_text))





# Encapsulation
def convert_action_to_tuple(action):
    return tuple(action.values())

# need action, and a substituted local name
def prepare_pattern(list):
    name_dict = {}
    place = 1
    for action in list:
        if action[5] in name_dict:
            pass
        else:
            name_dict[action[5]] = place
            place += 1

    return tuple((act[0],act[1],name_dict[act[5]]) for act in list)



ordered_list = []
for time in time_data:
    ordered_list.append(convert_action_to_tuple(time_data[time][0]))


max_len = len(ordered_list)
min_len = 3


for length in range(min_len,max_len+1):
    seen = {}
    for i in range(len(ordered_list) - length + 1):
        try:
            pattern = prepare_pattern(ordered_list[i : i + length])
        except IndexError as e:
            break

        if pattern in seen:
            seen[pattern].append({"lines":[x[4] for x in ordered_list[i : i + length]], "args":[x[5] for x in ordered_list[i : i + length]]})
        else:
            seen[pattern] = []
            seen[pattern].append({"lines":[x[4] for x in ordered_list[i : i + length]], "args":[x[5] for x in ordered_list[i : i + length]]})

    for pattern, data in seen.items():
        if len(data) > 1:
            patterns["encapsulation"].append({"pattern":pattern,"lines":[d["lines"] for d in data],"args": [d["args"] for d in data]})

# Refactor Encapsulation
if "--refactor-encapsulation" in sys.argv:
    # get original code
    with open(source_code_file,'r') as file:
        code_text = file.readlines()

    affected_lines = set()
    i = 0
    for pattern in patterns["encapsulation"]:
        gate_name = "gate"+str(i)
        i += 1
        func_text = "gate "+gate_name+" "
        for call in pattern["pattern"]:
            func_text += "q"+str(call[2])+","
        func_text = func_text[:-1] + "{\n"
        for call in pattern["pattern"]:
            func_text += "    " + call[1] + " " + str(call[2]) + ";\n"
        func_text += "}\n"

        j = 0
        for line_segment in pattern["lines"]:
            already_changed = any([(line in affected_lines) for line in line_segment])
            if already_changed:
                continue

            for line in line_segment:
                code_text[line - 1] = "\n"

            call_text = gate_name + " "
            for arg in pattern["args"][j]:
                call_text += arg+","
            call_text = call_text[:-1] + ';'
            j += 1
            code_text[line_segment[0]-1] = call_text

        code_text[0] = code_text[0] + func_text

    with open(source_code_file+".encapsulation_refactor",'w') as file:
        file.write("".join(code_text))











for pattern in patterns:
    print(pattern)
    for item in patterns[pattern]:
        print(f"\t{item}")

#print(patterns)




