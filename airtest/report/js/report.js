/*
 * @Description: 
 * @Author: Era Chen
 * @Email: chenjiyun@corp.netease.com
 * @Date: 2019-08-08 17:41:44
 * @LastEditors  : Era Chen
 * @LastEditTime : 2020-01-09 16:53:46
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
  this.magnifyContainer = $('#magnify .content')
  this.magnifyPic = $('#magnify')
  this.scale = 0
  this.order = 'acc' // or dec
  this.duration = 'acc' // or dec
  this.status = 'acc' // or dec
  this.thumbnail_step_list = []

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
    if ($('#console pre.trace').length > 0) {
      setTimeout(function(){
        // 当log超过2w行，转换成高亮模式会导致卡顿
        if ($('#console pre.trace').text().length < 20000) {
          hljs.highlightBlock($('#console pre.trace')[0], null, false)
          }
      }, 0)
    }
    this.highlightBlock()
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
    this.stepRight.delegate('.fancybox', "click", function(e) {
      that.showMagnifyPic(this.outerHTML)
    })
    this.stepRight.delegate('.crop_image', "click", function(e) {
      that.showMagnifyPic(this.outerHTML)
    })
    this.magnifyPic.click(function(e) {
      if (e.target.tagName.toLowerCase() != 'img'){
        that.hideMagnifyPic()
      }
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
      that.steps.sort(that.sortSteps('duration_ms', that.duration == 'acc'))
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
    $("#close-console").click(function(){
      $('#console').fadeOut(300)
    })
    $("#show-console").click(function(){
      $('#console').fadeIn(300)
    })
    document.body.onkeydown= (e)=>{  
      e=window.event||e;
      switch(e.keyCode){  
        case 37:
          //左键
          this.jumpToPreThumbNail()
          break;
        case 38:
          //向上键
          //禁用触发页面滚动
          e.preventDefault();
          this.jumpToPreThumbNail()
          break;
        case 39:
          //右键
          this.jumpToNextThumbNail()
          break;
        case 40:
          //向下键
          //禁用触发页面滚动
          e.preventDefault();
          this.jumpToNextThumbNail()
          break;
        default:
          break;
      }  
    } 
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
    this.highlightBlock()
    var that = this
    if($(".step-args .fancybox").length>0){
      $('#step-right .fancybox .screen').load(function(e){
        // 存在截屏，并加载成功
        that.resetScale(this)
        that.convertSize($('.step-args .crop_image'), 80, 35)
        that.resetScreenshot($('#step-right .fancybox'))
      })
    }
  }

  this.highlightBlock = function(){
    if($('#step-right pre.trace').length>0){
      hljs.highlightBlock($('#step-right pre.trace')[0], null, false);
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
        step.duration_ms = getDelta(step.time, this.data.run_start)
      } else{
        step.duration_ms = getDelta(step.time, this.steps[i-1].time)
      }
      step.duration = getFormatDuration(step.duration_ms)
      step.index =  i
      step.status =  step.traceback ? 'fail' : 'success'
      this.thumbnail_step_list = this.original_steps.map(function(step){
        if(step.screen && step.screen.thumbnail) {
          return step.index
        }})
        this.thumbnail_step_list = this.thumbnail_step_list.filter((val)=>{
          return val != null
      })
    }
  }

  this.init_gallery = function(){
    var that = this
    var fragment = this.original_steps.map(function(step){
      if(step.screen && step.screen.thumbnail) {
        return '<div class="thumbnail" index="%s">'.format(step.index) + 
                  '<img src="%s" alt="%s"/>'.format(step.screen.thumbnail, step.screen.thumbnail) +
                  '<div class="time">%s</div>'.format(getFormatDuration2(getDelta(step.time, that.data.run_start))) +
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

  this.jumpToNextThumbNail = function() {
    this.jumpToThumbNail('next')
  }

  this.jumpToPreThumbNail = function() {
    this.jumpToThumbNail('pre')
  }

  this.jumpToThumbNail = function(op) {
    let cur_thumbnail_step_index = this.thumbnail_step_list.findIndex((val)=>{
      return val == this.currentStep
    })
    let nxt_thumbnail_step_index = 0
    
    if(op == 'next'){
      if(cur_thumbnail_step_index < this.thumbnail_step_list.length - 1){
        nxt_thumbnail_step_index = this.thumbnail_step_list[cur_thumbnail_step_index + 1]
      }
    }else if(op == 'pre'){
      if(cur_thumbnail_step_index > 0){
        nxt_thumbnail_step_index = this.thumbnail_step_list[cur_thumbnail_step_index - 1]
      }
    }
    this.currentStep = nxt_thumbnail_step_index
    this.currentPage = Math.ceil(this.currentStep / this.pagesize)
    this.setSteps(this.currentStep)
  }

  this.showMagnifyPic = function(fragment) {
    this.magnifyContainer.html(fragment)
    this.magnifyContainer.children().removeAttr('style')
    var fancybox = this.magnifyContainer.find('.fancybox')
    if (fancybox.length > 0){
      var that = this
      $('#magnify .fancybox .screen').load(function(e){
        // 存在截屏，并加载成功
        if (this.height > this.parentNode.offsetHeight){
          this.style.height = this.parentNode.offsetHeight + 'px'
        }
        that.resetScale(this)
        that.resetScreenshot($('#magnify .fancybox'))
      })
    }
    this.magnifyPic.fadeIn(300)
  }

  this.hideMagnifyPic = function() {
    this.magnifyPic.fadeOut(300)
  }

  this.setStepsLeft = function(){
    html = this.steps.length>0 ? '' : '<h4 class="no-steps"><span lang="en">Warning: No steps</span></h3>'
    var start = (this.currentPage-1)* this.pagesize
    start = start < 0 ? 0 : start
    var end = (this.currentPage)*this.pagesize
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
                  "<span lang='en'>Start: </span>" +
                  "<span class='content-val'>%s</span>" +
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
                              step.time ? getFormatDateTime(step.time): '--',
                              this.static, step.duration,
                              step.code ? step.code.name:"null")
    } catch (err) {
      console.log(err)
      return ""
    }
  }

  this.getStepRightArgs = function(step) {
    // 操作的参数
    try {
      argHtml = ''
      if (step.code) {
        for (var i = 0; i < step.code.args.length; i++) {
          arg = step.code.args[i]
          if (arg.image) {
            argHtml += ('<img class="crop_image desc" data-width="%s" data-height="%s" src="%s" title="%s">' +
                '<p class="desc">resolution: %s</p>')
                .format(arg.resolution[0], arg.resolution[1], arg.image, arg.image, arg.value.resolution)
          } else {
            val = typeof arg.value == 'object' ? JSON.stringify(arg.value) : arg.value
            argHtml += '<p class="desc">%s: %s</p>'.format(arg.key, val)
          }
        }
      }
    } catch (e) {
      console.error(e)
    }

    // 相似度
    if (step.screen && step.screen.confidence) {
      argHtml += '<p class="desc"><span class="point glyphicon glyphicon-play"></span><span lang="en">Confidence: </span>%s</p>'.format(step.screen.confidence)
    }

    argHtml = argHtml || '<p class="desc">None</p>'
    argHtml = "<div class='fluid infos'>" + argHtml + "</div>"
    argHtml += "<div class='fluid screens'>" + this.getStepRightScreen(step) + "</div>"
    argHtml += "<div class='fluid traces'>" + this.getStepRightTrace(step) + "</div>"
    return "<div class='step-args'><div class='bold'>Args:</div>" + argHtml + "</div>"
  }

  this.getStepRightScreen = function(step){
    if(step.screen && step.screen.src){
      var src = step.screen.src
      // 截屏
      var img = '<img class="screen" data-src="%s" src="%s" title="%s" onerror="hideFancybox(this);">'.format(src, src, src)

      // 点击位置
      var targets = ''
      for(var i=0; i < step.screen.pos.length; i++){
        var pos = step.screen.pos[i]
        var rect = JSON.stringify({'left': pos[0], "top": pos[1]})
        targets += "<img class='target' src='%simage/target.png' rect=%s>"
                  .format(this.static, rect)
      }

      // 线
      var vectors = ''
      for(var i=0; i < step.screen.vector.length; i++){
        var v = step.screen.vector[i]
        var rect = JSON.stringify({'left': v[0], "top": v[1]})
        vectors += ("<div class='arrow' data-index='%s' rect=%s>" +
                    '<div class="start"></div>' +
                    '<div class="line"></div>' +
                    '<div class="end"></div>' +
                  '</div>').format(this.currentStep, rect)
      }
      
      // 还有个rect <!-- rect area -->
      var rectors = ''
      for(var i=0;i<step.screen.rect.length; i++){
        var rect = step.screen.rect[i]
        rectors += "<div class='rect' rect='%s' ></div>"
                   .format(JSON.stringify(rect))
      }
      var res = step.screen.resolution
      res = res ? 'w=%s h=%s'.format(res[0], res[1]): ""

      return '<div class="fancybox" %s >%s</div>'.format(res, img + targets + vectors + rectors)
    } else{
      return ""
    }
  }

  this.getStepRightTrace = function(step){
    if(step.traceback || step.log){
      var logMessage = step.traceback || '' + step.log || '';
      return '<div class="bold">Logs:</div><div class="desc"><pre class="trace"><code class="python">%s</code></pre></div>'.format(logMessage)
    } else{
      return ""
    }
  }

  this.resetScale = function(dom){
    /**
     * @description: 重新计算截屏缩放的比例
     * @param {dom} dom img对象
     */
    imgWidth = dom.parentNode.getAttribute('w') || dom.naturalWidth
    dwidth = dom.width
    this.scale = dwidth / imgWidth
  }

  this.resetScreenshot = function(fancybox){
    // 重新设置targt、方框、连接线位置
    var screen = fancybox.find('.screen')
    this.convertPos(fancybox.find('.target'), screen, true)
    this.convertSize(fancybox.find('.rect'))
    this.convertPos(fancybox.find('.rect'), screen)
    this.showArrow(fancybox.find(".arrow"), screen)
    fancybox.css({
      'width': screen.width()
    })
  }

  this.convertPos = function(domList, screen,  withSize){
    for(var i=0; i<domList.length; i++){
      var rect = JSON.parse(domList[i].getAttribute('rect'))
      x = rect.left * this.scale
      y = rect.top * this.scale
      if(withSize){
        x -= domList[i].offsetWidth/2
        y -= domList[i].offsetHeight/2
      }
      domList[i].style.left = this.convertPosPersentage(x, screen , 'horizontal')
      domList[i].style.top = this.convertPosPersentage(y, screen, 'vertical')
    }
  }

  this.convertSize = function(domList, minWidth, minHeight) {
    for(var i=0;i<domList.length; i++){
      if (domList[i].tagName.toLowerCase() == 'img'){
        w = domList[i].clientWidth
        h = domList[i].clientHeight
      } else{
        var rect = JSON.parse(domList[i].getAttribute('rect'))
        w = rect.width
        h = rect.height
      }
      var scale = Math.max(this.scale, (minWidth || 0)/w, (minHeight || 0)/h)
      domList[i].style.width = (w * scale) + 'px'
      domList[i].style.height = (h * scale) + 'px'
    }
  }

  this.showArrow = function(dom, screen){
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
        'top': this.convertPosPersentage(start[1]* this.scale, screen, 'vertical'),
        'left': this.convertPosPersentage(start[0]*this.scale, screen, 'horizontal'),
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
    var list_len = this.steps.length
    this.paging.init({
      target:'#pageTool',
      pagesize: this.pagesize,
      count: this.steps.length,
      prevTpl: "<",
      nextTpl: ">",
      toolbar:true,
      pageSizeList: list_len>100 ? [10, 20, 50, 100, list_len] : [10, 20, 50, 100],
      changePagesize:function(ps){
        that.pagesize = parseInt(ps)
        that.currentPage = 1
        that.setStepsLeft()
      },
      callback:function(p){
        that.currentPage = parseInt(p)
        that.setStepsLeft()
      }
    });
    $('#pageTool').prepend('<span class="steps-total"><span lang="en">Total </span><span class="steps-account"></span></span>')
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

  this.convertPosPersentage = function(pixcel, screen, key){
    ret = ''
    if(key == 'horizontal'){
      ret = pixcel / screen.width() * 100 + '%'
    }
    else if (key == 'vertical'){
      ret = pixcel / screen.height() * 100 + '%'
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

function getFormatDateTime(timestamp){
  timestamp = getTimestamp(timestamp)
  return (new Date(timestamp)).Format("yyyy-MM-dd hh:mm:ss")
}

function getFormatDate(timestamp){
  timestamp = getTimestamp(timestamp)
  return (new Date(timestamp)).Format("yyyy / MM / dd")
}

function getFormatTime(timestamp){
  timestamp = getTimestamp(timestamp)
  return (new Date(timestamp)).Format("hh:mm:ss")
}

function getFormatDuration(delta) {
  // 格式化耗时， 格式为 0hr1min6s22ms
  ms = parseInt(delta % 1000)
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

function getFormatDuration2(delta) {
  // 返回耗时，格式为 00:00:19
  var midnight = (new Date(new Date().setHours(0, 0, 0, 0))).getTime()
  return (new Date(midnight + delta)).Format("hh:mm:ss")
}

function getDelta(end, start) {
  // 返回耗时 单位为毫秒, end 和 start 可能是timestamp，也可能是化数据
  return getTimestamp(end) - getTimestamp(start)
}

function getTimestamp(time) {
  // time有可能是时间戳，也可能是格式化的，返回为毫秒
  if(Number(time)){
    return Number(time) * 1000
  } else{
    return (new Date(time).getTime())
  }
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
  var pairs = query.split(/&|\?/);
  for(var i = 0;i < pairs.length; i++){
      var pos = pairs[i].indexOf("=");
      if(pos == -1) continue;
      var name = pairs[i].substring(0, pos);
      var value = pairs[i].substring(pos + 1);
      value = decodeURIComponent(value);
      args[name] = value;
  }
  // Connect :Android:///04157df490cb0b3f?cap_method=JAVACAP&&ori_method=ADBORI&&touch_method=ADBTOUCH
  // && 也会被分割
  if(args['connect']){
    var methods = []
    if(args['cap_method'])
      methods.push("cap_method=JAVACAP")
    if(args['ori_method'])
      methods.push("ori_method=ADBORI")
    if(args['touch_method'])
      methods.push("touch_method=ADBTOUCH")
    if(methods.length>0)
      args['connect'] = args['connect'] + '?' + methods.join('&&')
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
      return '<div class="info %s" title="%s"><span lang="en">%s</span>%s</div>'.format(k,args[k], formatStr(k), args[k])
    })
    back = '<a href="%s#detail" class="back" title="Back to multi-device report"><img src="%simage/back.svg"></a>'.format(args.back, data.static_root)
    $('#back_multi').html(back)
    container.html(fragment)
    result = args.status ? args.status : result
    $(".footer").hide()
  }
  set_task_status(result)
  $('.info.connect').append("<div class='copy_device'></div>")
  $(".info .copy_device").click(function(){
    copyToClipboard(this.parentNode.getAttribute('title'))
  })
}

function copyToClipboard(msg){
  const input = document.createElement('input')
  input.setAttribute('readonly', 'readonly');
  input.setAttribute('value', msg);
  document.body.appendChild(input);
  if (document.execCommand('copy')) {
    input.select();
    document.execCommand('copy');
    console.log('复制成功');
  } else{
    alert('Copy is not supported by the current browser, please change to chrome')
  }
  document.body.removeChild(input);
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
  $('.summary .info-value.duration').html(getFormatDuration(getDelta(data.run_end, data.run_start)))
  setImgAffix()
}

function hideFancybox(img) {
  // 图片加载失败的情况下，隐藏整个div
  $(img).parent().hide();
}

function setImgAffix(){
  // 延迟触发，等待其他元素渲染完成再去获取，否则获取的值有误
  setTimeout(() => {
  // 获取页面加载时快览与页面顶端的距离
  var stickyHeaderTop = $('.gallery .content').offset().top
  // 在快览滑动到顶端时将其设置为固钉，添加页面滚动的监听事件
  $(window).scroll(function(){
    if($(window).scrollTop() > stickyHeaderTop) {
            $('.gallery .content').css({position: 'fixed', top: '0px'})
    } else {
            $('.gallery .content').css({position: 'relative', top: '0px'})
    }
  })
    // 计算需要占位的高度
    var placeHolderHeight= $('.gallery .placeholder').height()
    var placeHolderWidth = $('.gallery .content').width()
    $('.gallery .placeholder').css({minHeight: placeHolderHeight})
    $('.gallery .content').css({maxWidth: placeHolderWidth})
  }, 500)
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
    copyToClipboard(this.getAttribute('path'))
  })

  // 从地址search部分加载设备信息等
  loadUrlInfo()
})
