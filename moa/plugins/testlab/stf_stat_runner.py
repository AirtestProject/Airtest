# encoding=utf-8
import stf
import csv

def get_stf_device():
    req = ""
    available_device = stf.get_device_list_rest(req, "usable")
    available_device_count = len(available_device)
    present_device = stf.get_device_list_rest(req, "present")
    present_device_count = len(present_device)
    data = [
        ("Available","Present"),
        (available_device_count,present_device_count)
        ]
    with open("data.csv","wb") as f:
        writer = csv.writer(f)
        for item in data:
            writer.writerow(item)


if __name__ == "__main__":
    get_stf_device()
