// 基于准备好的dom，初始化echarts实例
//var myChart = echarts.init(document.getElementById('pfm_chart'), 'shine');

//var colors = ['#5793f3', '#d14a61', '#675bba'];
// 指定图表的配置项和数据
extra_data_option = {
//color: colors,
    title: {
        text: '引擎数据监控'
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        }
        // tooltip 提示文字在这里补充
    },
    legend: {
        data:['fps']
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
            name: 'fps',
            position: 'left',
            /*
            axisLine: {
                lineStyle: {
                    color: colors[0]
                }
            },
            */
            axisLabel: {
                formatter: '{value}'
            }
        }
        ],
    series: [
        {
            name:'fps',
            type:'line',
            yAxisIndex: 0,
            data:[],
            tooltip: {
                formatter: '{a0}: {c0}%'
            }
        }
    ]
};
function load_extra_data() {
    if (json_data === null) {
        console.log("test");
    } else {
        $("#fps").hide();
        $.each(json_data, function(i, n) {
            if (n.extra_data) {
                $("#fps").show();
                var myChart = echarts.init(document.getElementById('fps'), 'shine');
                extra_data_option.xAxis.data = n.extra_data.times;
                extra_data_option.series[0].data = n.extra_data.fps;
                myChart.setOption(extra_data_option);

            }
        })

    }
}
load_extra_data();