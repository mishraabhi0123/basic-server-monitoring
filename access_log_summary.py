import sys
from datetime import datetime

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

def get_data(line):
    components = line.split()
    status_code = components[8]
    log_time = convert_to_date(components[3][1:])
    method_string = components[5][1:]
    return {
        "status_code": status_code,
        "log_time": log_time,
        "method": method_string
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


file_path = sys.argv[1]
time_range = sys.argv[2] if len(sys.argv) > 2 else None

start_time = time_range.split("---")[0] if time_range and len(time_range.split("-")[0]) > 5 else None
end_time = time_range.split("---")[1] if time_range and len(time_range.split("-")) > 1 and len(time_range.split("-")) > 5 else None

status_map = {}
request_method_count_map = {}
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

table_print(status_map, total, status_header)
table_print(request_method_count_map, total, method_header)

print("\n")
print("Total: ", total)
print("requests per seconds: ", total / (end_time - start_time).total_seconds())
print("\n")
