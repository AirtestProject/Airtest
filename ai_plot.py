import os
import anyconfig
import numpy as np
from copy import deepcopy
from matplotlib import rc
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression


class PlotResult(object):

    def __init__(self, dir_path="", file_name=""):
        super(PlotResult, self).__init__()
        
        if file_name:
            file_path = os.path.join(dir_path, file_name)
            self.data = self.load_file(file_path)
            self.extract_data()
            self.analyze_data()
            self.predict_resource_usage()
        else:
            raise FileNotFoundError("Profile result file does not exist.")

    def load_file(self, file, print_info=True):
        if print_info:
            print("Loading config from:", repr(file))
        try:
            config = anyconfig.load(file, ignore_missing=True)
            return config
        except ValueError:
            print("Loading config failed...")
            return {}

    def extract_data(self):
        self.time_axis = []
        self.cpu_axis = []
        self.mem_axis = []
        self.timestamp_list = []
        plot_data = self.data.get("plot_data", [])
        
        for i in plot_data:
            timestamp = i["timestamp"]
            self.timestamp_list.append(timestamp)
            timestamp = round(timestamp, 1)
            cpu_percent = i["cpu_percent"]
            mem_gb_num = i["mem_gb_num"]
            date = datetime.fromtimestamp(timestamp)
            
            self.time_axis.append(date)
            self.cpu_axis.append(cpu_percent)
            self.mem_axis.append(mem_gb_num)
        
        self.get_each_method_maximun_cpu_mem()

    def get_each_method_maximun_cpu_mem(self):
        self.method_exec_info = deepcopy(self.data.get("method_exec_info", []))
        method_exec_info = deepcopy(self.method_exec_info)
        method_index = 0
        self.max_mem = 0
        
        for index, timestamp in enumerate(self.timestamp_list):
            if not method_exec_info:
                break
            
            start, end = method_exec_info[0]["start_time"], method_exec_info[0]["end_time"]
            
            if timestamp < start:
                continue
            
            if timestamp <= end:
                self.update_max_values(index, timestamp)
            else:
                self.update_method_exec_info(method_exec_info, method_index, timestamp)
                method_exec_info.pop(0)
                method_index += 1

    def update_max_values(self, index, timestamp):
        if self.cpu_axis[index] > getattr(self, 'cpu_max', 0):
            self.cpu_max = self.cpu_axis[index]
            self.cpu_max_time = timestamp
        if self.mem_axis[index] > getattr(self, 'mem_max', 0):
            self.mem_max = self.mem_axis[index]
            self.mem_max_time = timestamp

    def update_method_exec_info(self, method_exec_info, method_index, timestamp):
        if hasattr(self, 'cpu_max_time') and hasattr(self, 'mem_max_time'):
            method_exec_info[method_index].update({
                "cpu_max": self.cpu_max,
                "mem_max": self.mem_max,
                "cpu_max_time": self.cpu_max_time,
                "mem_max_time": self.mem_max_time
            })
        if self.mem_max > self.max_mem:
            self.max_mem = self.mem_max
        self.cpu_max, self.mem_max = 0, 0

    def analyze_data(self):
        # AI-Powered Anomaly Detection using Isolation Forest
        data = np.column_stack((self.cpu_axis, self.mem_axis))
        self.anomaly_model = IsolationForest(contamination=0.1)
        self.anomalies = self.anomaly_model.fit_predict(data)

    def predict_resource_usage(self):
        # Predictive Analytics using Linear Regression
        timestamps = np.array(self.timestamp_list).reshape(-1, 1)
        self.cpu_predictor = LinearRegression()
        self.cpu_predictor.fit(timestamps, self.cpu_axis)
        self.mem_predictor = LinearRegression()
        self.mem_predictor.fit(timestamps, self.mem_axis)

    def generate_insights(self):
        insights = []
        cpu_anomalies = np.where(self.anomalies == -1)[0]
        mem_anomalies = np.where(self.anomalies == -1)[1]

        if len(cpu_anomalies) > 0:
            insights.append(f"Anomalies detected in CPU usage at timestamps: {cpu_anomalies}.")
        else:
            insights.append("No CPU usage anomalies detected.")

        if len(mem_anomalies) > 0:
            insights.append(f"Anomalies detected in Memory usage at timestamps: {mem_anomalies}.")
        else:
            insights.append("No Memory usage anomalies detected.")

        future_time = self.timestamp_list[-1] + 600
        cpu_future = self.cpu_predictor.predict(np.array([future_time]).reshape(-1, 1))
        mem_future = self.mem_predictor.predict(np.array([future_time]).reshape(-1, 1))
        insights.append(f"Predicted CPU usage in 10 minutes: {cpu_future[0]:.2f}%")
        insights.append(f"Predicted Memory usage in 10 minutes: {mem_future[0]:.2f} MB")

        return "\n".join(insights)

    def _get_graph_title(self):
        start_time = datetime.fromtimestamp(int(self.timestamp_list[0]))
        end_time = datetime.fromtimestamp(int(self.timestamp_list[-1]))
        end_time = end_time.strftime('%H:%M:%S')
        title = "Timespan: %s —— %s" % (start_time, end_time)
        return title

    def plot_cpu_mem_keypoints(self):
        plt.figure(1)
        
        plt.subplot(311)
        title = self._get_graph_title()
        plt.title(title, loc="center")
        mem_ins = plt.plot(self.time_axis, self.mem_axis, "-", label="Mem(MB)", color='deepskyblue', linestyle='-', marker=',')
        plt.legend(mem_ins, ["Mem(MB)"], loc='upper right')
        plt.grid()
        plt.ylabel("Mem(MB)")
        plt.ylim(bottom=0)
        self.plot_method_exec_info(self.max_mem, 'mem_max_time')

        plt.subplot(312)
        cpu_ins = plt.plot(self.time_axis, self.cpu_axis, "-", label="CPU(%)", color='red', linestyle='-', marker=',')
        plt.legend(cpu_ins, ["CPU(%)"], loc='upper right')
        plt.grid()
        plt.xlabel("Time(s)")
        plt.ylabel("CPU(%)")
        plt.ylim(0, 120)
        self.plot_method_exec_info(100, 'cpu_max_time')

        plt.subplot(313)
        plt.xlabel('methods')
        plt.ylabel('keypoints number')
        method_list, method_pts_length_list, color_list = self.prepare_method_data()
        method_x = np.arange(len(method_list)) + 1
        plt.bar(method_x, method_pts_length_list, width=0.35, align='center', color=color_list, alpha=0.8)
        plt.xticks(method_x, method_list, size='small', rotation=30)
        
        for x, y in zip(method_x, method_pts_length_list):
            plt.text(x, y + 10, "%d" % y, ha="center", va="bottom", fontsize=7)
        plt.ylim(0, max(method_pts_length_list) * 1.2)

        plt.show()

        # Print AI-generated insights
        insights = self.generate_insights()
        print("AI-Generated Insights:")
        print(insights)

    def plot_method_exec_info(self, ylim, max_time_key):
        for method_exec in self.method_exec_info:
            start_date = datetime.fromtimestamp(method_exec["start_time"])
            end_date = datetime.fromtimestamp(method_exec["end_time"])
            plt.vlines(start_date, 0, ylim, colors="c", linestyles="dashed")
            plt.vlines(end_date, 0, ylim, colors="c", linestyles="dashed")
            
            x = datetime.fromtimestamp(method_exec[max_time_key])
            text = "%s: %d" % (method_exec["name"], method_exec["cpu_max"] if max_time_key == 'cpu_max_time' else method_exec["mem_max"])
            plt.text(x, method_exec["cpu_max"] if max_time_key == 'cpu_max_time' else method_exec["mem_max"], text, ha="center", va="bottom", fontsize=10)
            plt.plot(x, method_exec["cpu_max"] if max_time_key == 'cpu_max_time' else method_exec["mem_max"], 'ro' if max_time_key == 'cpu_max_time' else 'bo', label="point")

    def prepare_method_data(self):
        method_list, method_pts_length_list, color_list = [], [], []
        for method_exec in self.method_exec_info:
            for item in ["kp_sch", "kp_src", "good"]:
                method_list.append("%s-%s" % (method_exec["name"], item))
                method_pts_length_list.append(method_exec[item])
                color = "palegreen" if method_exec["result"] and item == "kp_sch" else \
                        "limegreen" if method_exec["result"] and item == "kp_src" else \
                        "deepskyblue" if method_exec["result"] and item == "good" else "tomato"
                color_list.append(color)
        return method_list, method_pts_length_list, color_list


def main():
    plot_object = PlotResult(dir_path="result", file_name="high_dpi.json")
    plot_object.plot_cpu_mem_keypoints()

if __name__ == '__main__':
    main()
