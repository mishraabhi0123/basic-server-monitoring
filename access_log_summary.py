import sys
from datetime import datetime

ELB = "nginx"
# ELB = "apache"

def convert_to_date(date_string):
  datetime_object = datetime.strptime(date_string, "%d/%b/%Y:%H:%M:%S")
  return datetime_object

def table_print(map, total, table_header):
    print("\n")
    data = [table_header]
    for (key, value) in map.items():
        data.append([key, value, (value*100 / total)])   

    data[1:] = sorted(data[1:], key=lambda x: x[1], reverse=True)

    column_widths = [max(len(str(item)) for item in column) for column in zip(*data)]
    for row in data:
        formatted_row = [str(item).ljust(width) for item, width in zip(row, column_widths)]
        print(" | ".join(formatted_row))

def get_data_nginx(line):
    components = line.split()
    status_code = components[8]
    log_time = convert_to_date(components[3][1:])
    method_string = components[5][1:]
    try:
        response_time = line.split('" ')[-1].split(" ")[0]
        response_time = float(response_time) * 100
    except:
        response_time = None
    return {
        "status_code": status_code,
        "log_time": log_time,
        "method": method_string,
        "response_time": response_time
    }


def get_data_apache(line):
    components = line.split()
    status_code = components[9]
    log_time = convert_to_date(components[4][1:])
    method_string = components[6][1:]
    try:
        response_time = int(components[11])
        response_time = response_time / 1000 # convert to milliseconds
    except: 
        response_time = None
    return {
        "status_code": status_code,
        "log_time": log_time,
        "method": method_string,
        "response_time": response_time
    }


def get_index(lines, time):
    search_from = 0
    search_till = len(lines)
    middle = None

    while search_from < search_till:
        middle = search_from + (search_till - search_from) // 2
        data = get_data(lines[middle])
        middle_time = data.get("log_time")

        # search right
        if (middle_time - time).total_seconds() <= -2:
            search_from = middle + 1

        # found case
        elif (middle_time - time).total_seconds() <= 2:
            return middle
        
        # search left
        elif (middle_time - time).total_seconds() > 2:
            search_till = middle - 1


def validate_range(min_value, max_value):
    def validator(value):
        if (value > min_value and value <= max_value):
            return True
        else:
            return False
        
    return validator



get_data = get_data_apache if ELB == 'apache' else get_data_nginx
file_path = sys.argv[1]
time_range = sys.argv[2] if len(sys.argv) > 2 else None

start_time = time_range.split("---")[0] if time_range and len(time_range.split("-")[0]) > 5 else None
end_time = time_range.split("---")[1] if time_range and len(time_range.split("-")) > 1 and len(time_range.split("-")) > 5 else None

status_map = {}
request_method_count_map = {}
response_time_range_count_map = {
    "0-100": 0,
    "100-200": 0,
    "200-300": 0,
    "300-400": 0,
    "400-800": 0,
    "800-1s": 0,
    "1s-2s": 0,
    "2s-5s": 0,
    "5s-10s": 0,
    "10s-20s": 0,
    "20s-40s": 0,
    "40s-1m": 0,
    "> 1m": 0,
}

response_time_range_validator = {
    "0-100": validate_range(0, 100),
    "100-200": validate_range(100, 200),
    "200-300": validate_range(200, 300),
    "300-400": validate_range(300, 400),
    "400-800": validate_range(400, 800),
    "800-1s": validate_range(800, 1000),
    "1s-2s": validate_range(1000, 2000),
    "2s-5s": validate_range(2000, 5000),
    "5s-10s": validate_range(5000, 10000),
    "10s-20s": validate_range(100000, 20000),
    "20s-40s": validate_range(20000, 40000),
    "40s-1m": validate_range(40000, 60000),
    "> 1m": validate_range(60000, 350000),
}


total = 0

with open(file_path, 'r') as file:
    lines = file.readlines()
    start_time = convert_to_date(start_time) if start_time else get_data(lines[0])['log_time']
    end_time = convert_to_date(end_time) if end_time else get_data(lines[-1])['log_time']

    start_index = get_index(lines, start_time)
    end_index = get_index(lines, end_time)
    total = end_index - start_index + 1

    for i in range(start_index, end_index + 1, 1):
        line = lines[i]    
        data = get_data(line)
        log_time = data["log_time"]
        status_code = data["status_code"]
        method_string = data["method"]
        response_time = data["response_time"]
        
        if response_time is not None:
            for (range_name, validate) in response_time_range_validator.items():
                if (validate(response_time)):
                    response_time_range_count_map[range_name] += 1 
            

        if status_code.isnumeric():
          if status_code in status_map:
              status_map[status_code] += 1
          else:
              status_map[status_code] = 1

        if len(method_string) < 8 and len(method_string) >= 3 and method_string.isalpha():
          if method_string in request_method_count_map:
              request_method_count_map[method_string] += 1 
          else:
              request_method_count_map[method_string] = 1


status_header = ["Status Code", "Count", "Percentage"]
method_header = ["Request Method", "Count", "Percentage"]
response_time_header = ["Range(ms)", "Count", "Percentage"]

table_print(status_map, total, status_header)
table_print(request_method_count_map, total, method_header)
table_print(response_time_range_count_map, total, response_time_header)

print("\n")
print("Total: ", total)
print("requests per seconds: ", total / (end_time - start_time).total_seconds())
print("\n")
