
// 基于准备好的dom，初始化echarts实例
//var myChart = echarts.init(document.getElementById('pfm_chart'), 'shine');

//var colors = ['#5793f3', '#d14a61', '#675bba'];
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
        }
        // tooltip 提示文字在这里补充
    },
    grid: {
        right: '20%'
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
            end: 100
        },
        {
            type: 'inside',
            realtime: true,
            start: 0,
            end: 100
        }],
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: []
    },
    yAxis: [{
            type: 'value',
            name: 'cpu使用率',
            position: 'left',
            /*
            axisLine: {
                lineStyle: {
                    color: colors[0]
                }
            },
            */
            axisLabel: {
                formatter: '{value} %'
            }
        },
        {
            type: 'value',
            name: 'pss内存占用',
            position: 'right',
            offset: 80,
            /*
            axisLine: {
                lineStyle: {
                    color: colors[1]
                }
            },
            */
            axisLabel: {
                formatter: '{value} MB'
            }
        },
        {
            type: 'value',
            name: 'net网络流量',
            position: 'right',
            /*
            axisLine: {
                lineStyle: {
                    color: colors[2]
                }
            },
            */
            axisLabel: {
                formatter: '{value} KB/S'
            }
        }
        ],
    series: [
        {
            name:'cpu使用率',
            type:'line',
            yAxisIndex: 0,
            data:[],
            tooltip: {
                formatter: '{a0}: {c0}%'
            }
        },
        {
            name:'pss内存占用',
            type:'line',
            yAxisIndex: 1,
            data:[]
        },
        {
            name:'net网络流量',
            type:'line',
            yAxisIndex: 2,
            data:[]
        }
    ]
};
function load_data() {
    if (json_data === null) {
        console.log("test");
    } else {
        $.each(json_data, function(i, n) {
            if (n.serialno === "") {
                var myChart = echarts.init(document.getElementById('pfm'), 'shine');
                option.title.text = '设备性能数据监控';
            } else {
                var myChart = echarts.init(document.getElementById('pfm_' + n.serialno), 'shine');
                option.title.text = '设备' + n.serialno + '性能数据监控';
            }
            option.xAxis.data = n.times;
            option.series[0].data = n.cpu;
            option.series[1].data = n.pss;
            option.series[2].data = n.net_flow;
            myChart.setOption(option);
        })

    }
}
load_data();