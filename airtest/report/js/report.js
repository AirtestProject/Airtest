/*
 * @Description: 
 * @Author: Era Chen
 * @Email: chenjiyun@corp.netease.com
 * @Date: 2019-08-08 17:41:44
 * @LastEditors: Era Chen
 * @LastEditTime: 2019-09-26 11:03:15
 */
function StepPannel(data, root){
  this.data = data
  this.original_steps = data.steps
  this.steps = [].concat(data.steps)
  this.static = data.static_root
  this.currentStep = 0
  this.currentWrong = -1
  this.pagesize = 20
  this.currentPage = 1
  this.stepLeft = $('#step-left .step-list')
  this.stepRight = $('#step-right')
  this.scale = 0
  this.order = 'acc' // or dec
  this.duration = 'acc' // or dec
  this.status = 'acc' // or dec

  this.init = function(){
    // 初始化
    this.initStepData()
    this.bindEvents()
    this.init_gallery()
    this.init_pagenation()
    var steps = this.filterAssertSteps()
    if(steps.length >0){
      this.steps = steps
      this.filterSteps($('.filter#assert'))
    } else{
      this.setSteps()
    }
    this.init_video()
  }

  this.bindEvents = function(){
    // 绑定事件
    var that = this
    this.stepLeft.delegate('.step', 'click',function(e){
      if(e.target.className.indexOf("step-context") >=0 )
        that.jumpToCurrStep(Number(e.target.getAttribute('index')))
      else
        that.setStepRight(e.currentTarget.getAttribute('index'))
    })
    $('.gallery .content').delegate('.thumbnail', 'click', function(e){
      that.jumpToCurrStep(Number(this.getAttribute('index')))
    })
    $('.filter#all').click(function(){
      that.steps = [].concat(that.original_steps)
      that.filterSteps(this)
    })
    $('.filter#success').click(function(){
      that.steps = that.filterSuccessSteps()
      that.filterSteps(this)
    })
    $('.filter#fail').click(function(){
      that.steps = that.filterFailSteps()
      that.filterSteps(this)
    })
    $('.filter#assert').click(function(){
      that.steps = that.filterAssertSteps()
      that.filterSteps(this)
    })
    $('#jump-wrong').click(function(){
      that.steps = [].concat(that.original_steps)
      that.currentWrong = that.findCurrentWrongStep()
      if(that.currentWrong>=0){
        that.currentStep = that.currentWrong
        that.currentPage = Math.ceil(that.currentStep / that.pagesize)
        that.setSteps(that.currentStep)
      }
    })
    $('.order#order').click(function(){
      that.order = that.order == 'acc' ? 'dec' : 'acc'
      that.steps.sort(that.sortSteps('index', that.order == 'acc'))
      that.currentPage = 1
      that.setSteps()
    })
    $('.order#duration').click(function(){
      that.steps.sort(that.sortSteps('duration', that.duration == 'acc'))
      that.duration = that.duration == 'acc' ? 'dec' : 'acc'
      that.currentPage = 1
      that.setSteps()
    })
    $('.order#status').click(function(){
      that.steps.sort(that.sortSteps('status', that.status == 'acc'))
      that.status = that.status == 'acc' ? 'dec' : 'acc'
      that.currentPage = 1
      that.setSteps()
    })
  }

  this.sortSteps = function(attr, rev){
    //第二个参数没有传递 默认升序排列
    if(rev ==  undefined){
        rev = 1;
    }else{
        rev = (rev) ? 1 : -1;
    }
    return function(a,b){
        a = a[attr];
        b = b[attr];
        if(a < b){
            return rev * -1;
        }
        if(a > b){
            return rev * 1;
        }
        return 0;
    }
  }

  this.initStepRight = function(){
    // 设置高亮
    if($('pre.trace').length>0){
      hljs.highlightBlock($('pre.trace')[0], null, false);
    }
    var that = this
    if($(".step-args .fancybox").length>0){
      $('.fancybox .screen').load(function(e){
        // 存在截屏，并加载成功
        that.resetScale(this)
        that.resetScreenshot()
      })
    }
  }

  this.filterSteps = function(dom){
    $('.steps .filter').removeClass('active')
    $(dom).addClass('active')
    this.currentPage = 1
    this.setSteps()
  }

  this.setSteps = function(step){
    // 重设步骤页面内容
    step = step || (this.steps.length > 0 ? this.steps[0].index : 0)
    this.setPagenation()
    this.setStepRight(step)
  }

  this.initStepData = function(){
    for(var i = 0; i< this.steps.length; i++){
      step = this.steps[i]
      if(i == 0){
        step.duration = getFormatDuration(step.time, this.data.run_start)
      } else{
        step.duration = getFormatDuration(step.time, this.steps[i-1].time)
      }
      step.index =  i
      step.status =  step.traceback ? 'fail' : 'success'
    }
  }

  this.init_gallery = function(){
    var that = this
    var fragment = this.original_steps.map(function(step){
      if(step.screen && step.screen.thumbnail) {
        return '<div class="thumbnail" index="%s">'.format(step.index) + 
                  '<img src="%s" alt="%s"/>'.format(step.screen.thumbnail, step.screen.thumbnail) +
                  '<div class="time">%s</div>'.format(getFormatDuration2(step.time, that.data.run_start)) +
                '</div>'
      } else{
        return ""
      }
    })
    fragment = fragment.join('')
    if(fragment == ''){
      $('.gallery').hide()
    }else{
      $('.gallery .content').html(fragment)
    }
  }

  this.jumpToCurrStep = function(step) {
    // 跳至指定步骤
    step = step || (this.steps.length > 0 ? this.steps[0].index : 0)
    this.steps = [].concat(this.original_steps)
    this.currentPage = Math.floor(step / this.pagesize) +1
    this.setPagenation()
    this.setStepRight(step)
    $('.steps .filter').removeClass('active')
  }

  this.setStepsLeft = function(){
    html = this.steps.length>0 ? '' : '<h4 class="no-steps"><span lang="en">Warning: No steps</span></h3>'
    start = (this.currentPage-1)* this.pagesize
    start = start < 0 ? 0 : start
    end = (this.currentPage)*this.pagesize
    end =  end>this.steps.length ? this.steps.length : end
    for(var i = start; i< end; i++){
      var step = this.steps[i]
      var title = step.assert ? '<span lang="en">Assert: </span>' + step.assert : step.title
      html += '<div class="step" index="%s">'.format(step.index) +
                '<img src="%simage/step_%s.svg" alt="%s.svg"/>'.format(this.static, step.status, step.status) +
                '<span class="order"># %s</span>'.format(step.index +1) +
                '<span class="step_title" lang="en">%s</span>'.format(title) +
                '<span class="step-time">%s</span>'.format(step.duration) +
                '<img class="step-context" src="%simage/eye.svg" alt="eye.svg" index="%s"/>'.format(this.static, step.index) +
              '</div>'
    }
    this.stepLeft.html(html)
  }
  this.setStepRight = function(index){
    index = parseInt(index)
    if(!isNaN(index) && index>= 0 && index<this.original_steps.length){
      $('.gallery .thumbnail.active').removeClass('active')
      $('.gallery .thumbnail[index="%s"]'.format(index)).addClass('active')
      this.setStepRightHtml(index)
      this.initStepRight()
    }
  }

  this.setStepRightHtml = function(index){
    this.stepLeft.find('.step.active').removeClass('active')
    this.stepLeft.find(".step[index='%s']".format(index)).addClass('active')
    step = this.original_steps[index]
    this.currentStep = index
    success = step.traceback ? "fail" : "success"
    pass = step.traceback ? "Failed" : "Passed"
    title = step.code ? step.desc||step.code.name : step.desc
    title = title || step.title
    var head = "<div class='step-head'><span class='step-status %s'>%s</span><span>Step %s: %s</span></div>"
                  .format(success, pass , step.index+1, title)
    var infos = this.getStepRightInfo(step)
    var args = this.getStepRightArgs(step)
    this.stepRight.html(head + infos + args)
  }

  this.getStepRightInfo = function(step){
    // HTML 本步骤成功与否、耗时
    try{
      return ("<div class='step-infos'>"+
                "<div class='infos-li'>" +
                  "<span lang='en'>Status: </span>" +
                  "<span class='content-val %s'>%s</span>" +
                  "<img src='%simage/step_%s.svg'>" +
                "</div>" +
                "<div class='infos-li'>" +
                  "<span lang='en'>Duration: </span>" +
                  "<img src='%simage/time.svg'>" +
                  "<span class='content-val'>%s</span>" +
                "</div>" +
                "<div class='infos-li step-behavior'>" +
                  "<span lang='en'>Behavior: </span>" +
                  "<span class='content-val bold'>%s</span>" +
                "</div>" +
              "</div>").format(success, pass, this.static, success,
                              this.static, step.duration,
                              step.code.name)
    } catch (err) {
      console.log(err)
      return ""
    }
  }

  this.getStepRightArgs = function(step){
    // 操作的参数
    try{
      argHtml = ''
      if(step.code){
        for(var i=0; i < step.code.args.length; i++){
          arg = step.code.args[i]
          if(arg.image){
            argHtml += ('<img class="crop_image desc" data-width="%s" data-height="%s" src="%s" title="%s">' +
                    '<p class="desc">resolution: %s</p>')
                    .format(arg.resolution[0], arg.resolution[1], arg.image, arg.image, arg.value.resolution)
          }else{
            val = typeof arg.value == 'object' ? JSON.stringify(arg.value) : arg.value
            argHtml += '<p class="desc">%s: %s</p>'.format(arg.key,val)
          }
        }
      }
    } catch(e) {
      console.error(e)
    }

    // 相似度
    if(step.screen && step.screen.confidence){
      argHtml += '<p class="desc"><span class="point glyphicon glyphicon-play"></span><span lang="en">Confidence: </span>%s</p>'.format(step.screen.confidence)
    }

    argHtml =  argHtml || '<p class="desc">None</p>'
    argHtml = "<div class='fluid infos'>" + argHtml + "</div>"
    argHtml += "<div class='fluid screens'>" + this.getStepRightScrren(step) + "</div>"
    argHtml += "<div class='fluid traces'>" + this.getStepRightTrace(step) + "</div>"
    return "<div class='step-args'><div class='bold'>Args:</div>" + argHtml + "</div>"
  }

  this.getStepRightScrren = function(step){
    if(step.screen && step.screen.src){
      src = step.screen.src
      // 截屏
      img = '<img class="screen" data-src="%s" src="%s" title="%s">'.format(src, src, src)

      // 点击位置
      targets = ''
      for(var i=0; i < step.screen.pos.length; i++){
        pos = step.screen.pos[i]
        targets += '<img class="target" src="%simage/target.png" data-top="%s" data-left="%s" style="top:%spx;left:%spx;">'
                  .format(this.static, pos[1], pos[0], pos[1], pos[0])
      }

      // 线
      vectors = ''
      for(var i=0; i < step.screen.vector.length; i++){
        v = step.screen.vector[i]
        vectors += ('<div class="arrow" data-index="%s" data-x="%s" data-y="%s">' +
                    '<div class="start"></div>' +
                    '<div class="line"></div>' +
                    '<div class="end"></div>' +
                  '</div>').format(this.currentStep, v[0], v[1])
      }

      // 还有个rect <!-- rect area -->
      rectors = ''
      for(var i=0;i<step.screen.rect.length; i++){
        rect = step.screen.rect[i]
        rectors += "<div class='rect' ret='%s' style='left:%spx;top:%spx;width:%spx;height:%spx'></div>"
                   .format(JSON.stringify(rect), rect.left, rect.top, rect.width, rect.height)
      }

      return '<div class="fancybox">%s</div>'.format(img + targets + vectors + rectors)
    } else{
      return ""
    }
  }

  this.getStepRightTrace = function(step){
    if(step.traceback){
      return '<div class="desc"><pre class="trace"><code class="python">%s</code></pre></div>'.format(step.traceback)
    } else{
      return ""
    }
  }

  this.resetScale = function(dom){
    /**
     * @description: 重新计算截屏缩放的比例
     * @param {dom} dom img对象
     */
    imgWidth = dom.naturalWidth
    dwidth = dom.width
    this.scale = dwidth / imgWidth
    this.scale  = Math.round(this.scale  * 100) / 100
  }

  this.resetScreenshot = function(){
    // 重新设置targt、方框、连接线位置
    this.convertSize($('.step-args .crop_image'))
    this.convertPos($('.fancybox .target'), true)
    this.convertSize($('.fancybox .rect'))
    this.convertPos($('.fancybox .rect'))
    this.showArrow($(".fancybox .arrow"))
    $('.fancybox').css({
      'width': $('.fancybox .screen').width()
    })
  }

  this.convertPos = function(domList, withSize){
    for(var i=0; i<domList.length; i++){
      pos = $(domList[i]).position()
      x = pos.left * this.scale
      y = pos.top * this.scale
      if(withSize){
        x -= domList[i].offsetWidth/2
        y -= domList[i].offsetHeight/2
      }
      domList[i].style.left = this.convertPosPersentage(x, 'horizontal')
      domList[i].style.top = this.convertPosPersentage(y, 'vertical')
    }
  }

  this.convertSize = function(domList){
    for(var i=0;i<domList.length; i++){
      w = domList[i].clientWidth
      h = domList[i].clientHeight
      domList[i].style.width = (w * this.scale) + 'px'
      domList[i].style.height = (h * this.scale) + 'px'
    }
  }

  this.showArrow = function(dom){
    var start = this.original_steps[this.currentStep].screen.pos[0]
    var vector = this.original_steps[this.currentStep].screen.vector[0]
    if(vector && start){
      var vt_x = vector[0] * this.scale;
      var vt_y = - vector[1] * this.scale;
      var vt_width = Math.sqrt(vt_x * vt_x + vt_y * vt_y)
      var rotation = 360*Math.atan2(vt_y, vt_x)/(2*Math.PI)
      var rt =  'rotate(' + -rotation + 'deg)';
      var rotate_css = {
        '-ms-transform': rt,
        '-webkit-transform': rt,
        '-moz-transform': rt,
        'transform': rt,
        'transform-origin': '6px 15px',
      };
      dom.css(rotate_css);
      dom.css({
        'top': this.convertPosPersentage(start[1]* this.scale, 'vertical'),
        'left': this.convertPosPersentage(start[0]*this.scale, 'horizontal'),
        'width': vt_width
      });
    }
  }

  this.filterSuccessSteps = function(){
    // 筛选成功步骤
    arr = []
    for(var i=0; i<this.original_steps.length; i++){
      step = this.original_steps[i]
      if(step.traceback)
        continue
      else
        arr.push(step)
    }
    return arr
  }

  this.filterFailSteps = function(){
    // 筛选失败步骤
    arr = []
    for(var i=0; i<this.original_steps.length; i++){
      step = this.original_steps[i]
      if(step.traceback)
        arr.push(step)
      else
        continue
    }
    return arr
  }

  this.filterAssertSteps = function(){
    // 筛选断言步骤
    arr = []
    for(var i=0; i<this.original_steps.length; i++){
      step = this.original_steps[i]
      if(step.assert)
        arr.push(step)
      else
        continue
    }
    return arr
  }

  this.findCurrentWrongStep = function(){
    // 跳至错误步骤
    arr = this.filterFailSteps()
    if(arr.length>0){
      if(this.currentWrong == arr[arr.length-1].index)
        return arr[0].index
      for(var i=0; i<arr.length; i++){
        if(arr[i].index > this.currentWrong)
          return arr[i].index
      }
    }
    return -1
  }

  this.init_pagenation = function(){
    //生成分页控件
    this.paging = new Paging();
    var that = this
    this.paging.init({
      target:'#pageTool',
      pagesize: this.pagesize,
      count: this.steps.length,
      prevTpl: "<",
      nextTpl: ">",
      toolbar:true,
      pageSizeList: this.steps.length>100 ? [10, 20, 50, 100, 'All'] : [10, 20, 50, 100],
      changePagesize:function(ps){
        if(ps == 'All')
          that.pagesize = this.steps.length
        else
          that.pagesize = parseInt(ps)
        that.currentPage = 1
        that.setStepsLeft()
      },
      callback:function(p){
        that.currentPage = parseInt(p)
        that.setStepsLeft()
      }
    });
    $('#pageTool').prepend('<span class="stpes-total"><span lang="en">Total </span><span class="steps-account"></span></span>')
  }

  this.setPagenation = function(){
    if(this.steps.length > this.pagesize)
      $('#pageTool').show()
    else
      $('#pageTool').hide()
    this.paging.render({
      'count': this.steps.length
    })
    $('#pageTool .steps-account').html(this.steps.length)
    this.paging.go(this.currentPage)
  }

  this.init_video = function(){
    var container = $('.gif-wrap')
    if($('.gif-wrap .embed-responsive').length>0) {
      $('.gif-wrap .minimize').click(function(){
        container.removeClass('show')
      })
      $('.gif-wrap .maximize').click(function(){
        container.addClass('show')
      })
      $('.gif-wrap .close').click(function(){
        container.hide()
      })
    }else {
      container.hide()
    }
  }

  this.convertPosPersentage = function(pixcel, key){
    ret = ''
    if(key == 'horizontal'){
      ret = pixcel /$('.fancybox .screen').width() * 100 + '%'
    }
    else if (key == 'vertical'){
      ret = pixcel / $('.fancybox .screen').height() * 100 + '%'
    }
    return ret
  }
}


String.prototype.format= function(){
  var args = Array.prototype.slice.call(arguments);
  var count=0;
  return this.replace(/%s/g,function(s,i){
    return args[count++];
  });
}

Date.prototype.Format = function (fmt) { //author: meizz
  var o = {
    "M+": this.getMonth() + 1, //月份
    "d+": this.getDate(), //日
    "h+": this.getHours(), //小时
    "m+": this.getMinutes(), //分
    "s+": this.getSeconds(), //秒
    "q+": Math.floor((this.getMonth() + 3) / 3), //季度
    "S": this.getMilliseconds() //毫秒
  };
  if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
  for (var k in o)
  if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
  return fmt;
}

function getFormatDate(timestamp){
  timestamp = getTimestamp(timestamp)
  return (new Date(timestamp)).Format("yyyy / MM / dd")
}

function getFormatTime(timestamp){
  timestamp = getTimestamp(timestamp)
  return (new Date(timestamp)).Format("hh:mm:ss")
}

function getFormatDuration(end, start) {
  // 返回耗时，格式为 0hr1min6s22ms
  var delta = getTimestamp(end) - getTimestamp(start)
  return getDelta(parseInt(delta))
}

function getFormatDuration2(end, start) {
  // 返回耗时，格式为 00:00:19
  var delta = getTimestamp(end) - getTimestamp(start)
  var midnight = (new Date(new Date().setHours(0, 0, 0, 0))).getTime()
  return (new Date(midnight + delta)).Format("hh:mm:ss")
}

function getTimestamp(time) {
  // time有可能是时间戳，也可能是格式化的，返回为毫秒
  if(Number(time)){
    return Number(time) * 1000
  } else{
    return (new Date(time).getTime())
  }
}

function getDelta(delta){
  // 计算消耗时间，end - start，以0hr1min6s22ms 格式
  ms = delta % 1000
  delta = parseInt(delta / 1000)
  s = delta % 60
  delta = parseInt(delta/ 60)
  m = delta % 60
  h = parseInt(delta/ 60)

  msg = ''
  if(h == 0)
    if(m == 0)
      if(s==0)
        msg =  ms + "ms"
      else
        msg = s + "s " + ms + "ms"
    else
      msg = m + 'min ' + s + "s " + ms + "ms"
  else
    msg = h + 'hr ' + m + 'min ' + s + "s " + ms + "ms"
  return msg
}

function toggleCollapse(dom){
  if(dom.hasClass('collapse')){
    dom.removeClass('collapse')
  } else{
    dom.addClass('collapse')
  }
}

function urlArgs(){
  var args = {};
  var query = location.search.substring(1);
  var pairs = query.split("&");
  for(var i = 0;i < pairs.length; i++){
      var pos = pairs[i].indexOf("=");
      if(pos == -1) continue;
      var name = pairs[i].substring(0, pos);
      var value = pairs[i].substring(pos + 1);
      value = decodeURIComponent(value);
      args[name] = value;
  }
  return args;
}


var formatStr = function(str) {
  return (str.charAt(0).toUpperCase()+str.slice(1)).replace(/_/g, ' ') + ':'
};

function loadUrlInfo(){
  // 根据search信息，在summary下面插入设备信息，仅限多机运行的时候使用
  args = urlArgs()
  result = data.test_result ? 'Passed' : 'Failed'
  if(args.type) {
    var container = $('#device')
    container.addClass('show')
    var keys = ["device", "connect", "accomplished", "rate", "succeed", 'failed', "no_of_device", "no_of_script", "type"]
    args.rate = (args.succeed / args.accomplished * 100).toFixed(2) + '%'
    args.failed = args.accomplished - args.succeed
    args['no_of_device'] = args.device_no
    args['no_of_script'] = args.script_no
    var fragment  = keys.map(function(k){
      return '<div class="info %s"><span lang="en">%s</span>%s</div>'.format(k, formatStr(k), args[k])
    })
    back = '<a href="%s" class="back" title="Back to multi-device report"><img src="%simage/back.svg"></a>'.format(args.back, data.static_root)
    $('#back_multi').html(back)
    container.html(fragment)
    result = args.status ? args.status : result
    $(".footer").hide()
  }
  set_task_status(result)
}

function set_task_status(result){
  src = "%simage/%s.svg".format(data.static_root, result=='Passed' ? 'success' : 'fail')
  $('.summary #result-img').attr('src', src)
  $('.summary #result-img').attr('alt', result)
  $('.summary #result-desc').addClass(result=='Passed' ? 'green' : 'red')
  $('.summary #result-desc').html("[%s]".format(result))
}

function init_page(){
  $('.summary .info-sub.start').html(getFormatDate(data.run_start))
  $('.summary .info-sub.time').html(getFormatTime(data.run_start) + '-' + getFormatTime(data.run_end))
  $('.summary .info-value.duration').html(getFormatDuration(data.run_end, data.run_start))
}

$(function(){
  init_page()
  stepPanel = new StepPannel(data)
  stepPanel.init()
  $("img").error(function () {
    var orsrc = $(this).attr("src")
    if(!orsrc){ return }
    if(orsrc.indexOf("report.gif") > -1){
      setTimeout(function(){
        $(this).attr("src", 'report.gif?timestamp=' + new Date().getTime());
      }.bind(this), 5000)
      return
    }
    $(this).unbind("error")
    .addClass('error-img')
    .attr("src", data.static_root + "image/broken.png")
    .attr("orgin-src", orsrc);
  });

  // 延迟加载图片
  lazyload();

  // 自动收缩过长的脚本描述
  var descHeight = 100;
  descWrap = $('.summary .airdesc')
  if($('.summary .desc-content').height()>descHeight) {
    descWrap.addClass('long collapse')
    $(".summary .show-more").click(function(){
      toggleCollapse(descWrap)
    })
  }

  // 复制脚本地址到粘贴版
  $('#copy_path').click(function(){
    const input = document.createElement('input')
    input.setAttribute('readonly', 'readonly');
    input.setAttribute('value', this.getAttribute('path'));
    document.body.appendChild(input);
    if (document.execCommand('copy')) {
      input.select();
      document.execCommand('copy');
      console.log('复制成功');
    } else{
      alert('Copy is not supported by the current browser, please change to chrome')
    }
    document.body.removeChild(input);
  })

  // 从地址search部分加载设备信息等
  loadUrlInfo()
})
