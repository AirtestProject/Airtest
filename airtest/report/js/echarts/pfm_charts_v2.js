
// 基于准备好的dom，初始化echarts实例
//var myChart = echarts.init(document.getElementById('pfm_chart'), 'shine');

var unit = {0: ' %', 1: ' MB', 2: ' KB/S'};
// 指定图表的配置项和数据
option = {
//color: colors,
    title: {
        text: '性能数据监控'
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        },
        // tooltip 提示文字在这里补充
        formatter: function(params) {
            var title = get_time(params[0].name);
            if (title.title === "") {
                title = params[0].name;
            } else {
                title = title.title;
            }
            var content = title + "<br/>";
            $(params).each(function(i, n){
                if (n.value !== "") {
                    content +=  n.marker + " " + n.seriesName + " " + n.value + unit[n.seriesIndex] + "<br/>";
                } else {
                    content += n.marker + " " + n.seriesName + " " + "未获取" + "<br/>";
                }

            });
            return content;
        }
    },
    grid: {
        top: 80
    },
    legend: {
        data:['cpu使用率','pss内存占用','net网络流量']
    },
    toolbox: {
        feature: {
            saveAsImage: {}
        }
    },
    dataZoom: [
        {
            show: true,
            realtime: true,
            start: 0,
            end: 100,
            xAxisIndex: [0, 1]
        },
        {
            type: 'inside',
            realtime: true,
            start: 0,
            end: 100
        }],
    xAxis: [{
            type: 'category',
            boundaryGap: false,
            data: []
        },
        {
            type: 'category',
            axisTick: {
                alignWithLabel: true
            },
            axisLine: {
                onZero: false
            },
            boundaryGap: false,
            data: []
        }],
    yAxis: [{
            type: 'value',
            name: 'cpu使用率',
            position: 'left',
            nameGap: 27,
            axisLabel: {
                formatter: '{value}' + unit[0]
            }
        },
        {
            type: 'value',
            name: 'pss内存占用',
            position: 'right',
            nameGap: 27,
            offset: 80,
            axisLabel: {
                formatter: '{value}' + unit[1]
            }
        },
        {
            type: 'value',
            name: 'net网络流量',
            position: 'right',
            nameGap: 27,
            axisLabel: {
                formatter: '{value}' + unit[2]
            }
        }
        ],
    series: [
        {
            name:'cpu使用率',
            type:'line',
            yAxisIndex: 0,
            xAxisIndex: 0,
            markLine: {
                label: {
                    normal: {
                        show: true,
                        position: 'middle',
                        formatter: '视频当前播放位置'
                    }
                },
                animation: false,
                data: []
            }
        },
        {
            name:'pss内存占用',
            type:'line',
            yAxisIndex: 1,
            xAxisIndex: 0
        },
        {
            name:'net网络流量',
            type:'line',
            yAxisIndex: 2,
            xAxisIndex: 0
        }
    ]
};

// option_cpu
option_cpu = {
    title: {
        text: 'CPU数据监控'
    },
    tooltip : {
        trigger: 'axis',
        axisPointer : {            // 坐标轴指示器，坐标轴触发有效
            type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
        }
    },
    dataZoom: [
    {
        show: true,
        realtime: true,
        start: 0,
        end: 100,
        xAxisIndex: [0]
    },
    {
        type: 'inside',
        realtime: true,
        start: 0,
        end: 100
    }],
    grid: {
        top: 80
    },
    legend: {
        data:[]
    },
    xAxis: [{
            type: 'category',
            data: [1, 2,3,4, 5,6,7]
        }],
    yAxis: [{
            type: 'value'
    }],
    series: [
    ]
};

time_list = [];
function load_data() {

    $(".step_time").each(function(i){
        var step = $(this).closest("h2");
        //var d = {time: new Date($(this).text()), title: $(step).find(".step_title").text(), sid: $(step).data("stepid")};
        var d = {time: new Date($(this).text()), title: $(step).text(), sid: $(step).data("stepid")};
        time_list.push(d);
    });
    if (json_data === null) {
        console.log("cannot load performance data");
    } else {
        $.each(json_data, function(i, n) {
            if (n.serialno === "") {
                var myChart = echarts.init(document.getElementById('pfm'), 'shine');
                var myChartCpu = echarts.init(document.getElementById('pfm_cpu'), 'shine');
                option.title.text = '设备性能数据监控';
                option_cpu.title.text = 'CPU数据监控';
            } else {
                var myChart = echarts.init(document.getElementById('pfm_' + n.serialno), 'shine');
                var myChartCpu = echarts.init(document.getElementById('pfm_' + n.serialno + '_cpu'), 'shine');
                option.title.text = '设备' + n.serialno + '性能数据监控';
                option_cpu.title.text = '设备' + n.serialno + 'CPU数据监控';
            }
            option.xAxis[0].data = n.times;
            option.series[0].data = n.cpu;
            option.series[1].data = n.pss;
            option.series[2].data = n.net_flow;
            var steps = get_steps(n.times, time_list);
            option.xAxis[1].data = steps;
            myChart.setOption(option);
            if (i === (json_data.length - 1)) {
                recordMarkLine();
            }
            // option cpu
            option_cpu.xAxis[0].data = n.times;
            option_cpu.series = [];
            option_cpu.legend.data = [];
            $.each(Object.keys(n.cpu_freq), function(i, key){
                option_cpu.series.push({
                    name: '核心' + key,
                    type: 'bar',
                    stack: '总量',
                    data: n.cpu_freq[key]
                });
                option_cpu.legend.data.push('核心' + key);
            });
            myChartCpu.setOption(option_cpu);
        })

    }
}
load_data();


function get_time(time) {
    // 传入一个时间点，得到当前时间点的操作步骤是哪一步
    var t = new Date(time);
    var ret = {time: t, title: time, sid: "", index: 0};
    var index = 0;
    $(time_list).each(function(i, n){
        if (n.time <= t) {
            ret = n;
            index = i;
        } else {
            return true;
        }
    });
    ret.index = index;
    return ret;
}

function get_steps(x_times, step_times) {
    // 传入运行过程的时间列表和脚本内的执行步骤，得出一个x轴时间列表
    // 假设times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    // steps = [1, 5, 10]
    // 预期结果应该是 [0, 1, 1, 1, 1, 5, 5, 5, 5, 5, 10, 10]
    if (step_times === []) {
        return [];
    }
    var times = [];
    $.each(x_times, function(i, n) {
        var t = new Date(n);
        times.push(t);
    });
    var ret = [];
    var times_len = times.length;
    // 非常规情况，假如生成的log与脚本并不能同时对应上，直接把x轴内容返回
    if (step_times.length < 1) {
        return x_times;
    }
    if ((times[times_len - 1] < step_times[0].time) || (times[0] > step_times[step_times.length - 1])) {
        return x_times;
    }
    var i = 0;  // times的计数器
    var si = 1;  // steps的计数器
    var ls = step_times[0];  // 左边步骤
    var rs = step_times[0];
    if (step_times.length > 1) {  // 右边步骤
        rs = step_times[1];
    }

    while (si < step_times.length) {
        var t = times[i];
        while (t <= rs.time && i < (times_len - 1)) {
            if (t < ls.time) {
                // 小于时间范围的左边，说明步骤发生时间可能在轴外，直接把时间的值作为坐标值
                ret.push(x_times[i]);
            } else if ((t - rs.time) == 0) {
                // 假如与范围的右边相等，说明该步骤发生的时间正好与采样点同时
                ret.push(rs.title);
            }
            else {
                ret.push(ls.title);
            }
            i += 1;
            t = times[i];
        }
        ls = rs;
        si += 1;
        if (si >= step_times.length){
            break;
        }
        rs = step_times[si];
    }

    while (ret.length < times_len) {
        ret.push(rs.title);
    }

    return ret;

}

function click_listener(params) {
    var get_step = get_time(params.name);
    if (get_step.title !== "") {
        console.log(get_step.sid);
    }
}

function setMarkLine(xValue, charts) {
    // 在图上加一条竖直的mark line，可以标记当前时间点位置
    //var chartIns = echarts.getInstanceByDom(document.getElementById('pfm'));
    var op = {
        series: {
            markLine: {
                data: [{
                    xAxis: xValue
                }]
            }
        }
    };
    $.each(charts, function(i, n) {
        n.setOption(op);
    });
}

function recordMarkLine() {
    var charts = [];
    $(".pfm_chart").each(function(i, n){
        var c = echarts.getInstanceByDom(document.getElementById($(this).attr("id")));
        charts.push(c);
    });
    if (charts.length === 0) {
        return true;
    }
    var xAxis = charts[0].getOption().xAxis[0].data;
    if ((xAxis.length < 2) && (xAxis.length > 0)) {
        setMarkLine(xAxis[0], charts);
    } else {
        var i = 0;
        // 视频起始时间
        var startTime = new Date(xAxis[0]);
        var endTime = new Date(xAxis[xAxis.length - 1]);
        //var curTime = new Date(xAxis[i]);
        var curXTime = new Date(xAxis[i + 1]);
        $(".device-record").on("timeupdate", function(event) {
            // 根据视频的播放时间来移动图像上的markline
            if (i === 0) {
                setMarkLine(xAxis[0], charts);
            }
            var ctime = this.currentTime;
            var curTime = new Date(startTime.getTime() + ctime * 1000);
            if (curTime > endTime) {
                // 视频播放到最右超过脚本时间时，重置计数器
                i = 0;
                curXTime = new Date(xAxis[i + 1]);
                return true;
            }
            if (i >= xAxis.length) {
                return true;
            }
            while (curTime >= curXTime ) {
                i += 1;
                setMarkLine(xAxis[i], charts);
                if (i < xAxis.length) {
                    curXTime = new Date(xAxis[i + 1]);
                } else {
                    break;
                }
            }
            // 手工调整时间前移的情况
            while ((curTime < curXTime) && i > 0) {
                var prevTime = new Date(xAxis[i - 1]);
                if (curTime > prevTime) {
                    break;
                }
                curXTime = new Date(xAxis[i]);
                i -= 1;
                setMarkLine(xAxis[i], charts);
            }
        })
    }
}