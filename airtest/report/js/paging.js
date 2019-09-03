!function(t, i) {
    "function" == typeof define && define.amd ? define(["jquery"], i) : "object" == typeof exports ? module.exports = i() : t.Query = i(window.Zepto || window.jQuery || $)
}(this, function(t) {
    return {
        getQuery: function(t, e, s) {
            new RegExp("(^|&|#)" + t + "=([^&]*)(&|$|#)","i");
            s = s || window;
            var a, n, r = s.location.href, l = "";
            if (a = "#" == e ? r.split("#") : r.split("?"),
            "" != (n = 1 == a.length ? "" : a[1])) {
                gg = n.split(/&|#/);
                var h = gg.length;
                for (str = arguments[0] + "=",
                i = 0; i < h; i++)
                    if (0 == gg[i].indexOf(str)) {
                        l = gg[i].replace(str, "");
                        break
                    }
            }
            return decodeURI(l)
        },
        getForm: function(i) {
            var e = {}
              , s = {};
            t(i).find("*[name]").each(function(i, a) {
                var n, r = t(a).attr("name"), l = t.trim(t(a).val()), h = [];
                if ("" != r && !t(a).hasClass("getvalued")) {
                    if ("money" == t(a).data("type") && (l = l.replace(/\,/gi, "")),
                    "radio" == t(a).attr("type")) {
                        var c = null;
                        t("input[name='" + r + "']:radio").each(function() {
                            t(this).is(":checked") && (c = t.trim(t(this).val()))
                        }),
                        l = c || ""
                    }
                    if ("checkbox" == t(a).attr("type")) {
                        var c = [];
                        t("input[name='" + r + "']:checkbox").each(function() {
                            t(this).is(":checked") && c.push(t.trim(t(this).val()))
                        }),
                        l = c.length ? c.join(",") : ""
                    }
                    if (t(a).attr("listvalue") && (e[t(a).attr("listvalue")] || (e[t(a).attr("listvalue")] = [],
                    t("input[listvalue='" + t(a).attr("listvalue") + "']").each(function() {
                        if ("" != t(this).val()) {
                            var i = t(this).attr("name")
                              , s = {};
                            if ("json" == t(this).data("type") ? s[i] = JSON.parse(t(this).val()) : s[i] = t.trim(t(this).val()),
                            t(this).attr("paramquest")) {
                                var n = JSON.parse(t(this).attr("paramquest"));
                                s = t.extend(s, n)
                            }
                            e[t(a).attr("listvalue")].push(s),
                            t(this).addClass("getvalued")
                        }
                    }))),
                    t(a).attr("arrayvalue") && (e[t(a).attr("arrayvalue")] || (e[t(a).attr("arrayvalue")] = [],
                    t("input[arrayvalue='" + t(a).attr("arrayvalue") + "']").each(function() {
                        if ("" != t(this).val()) {
                            var i = {};
                            if (i = "json" == t(this).data("type") ? JSON.parse(t(this).val()) : t.trim(t(this).val()),
                            t(this).attr("paramquest")) {
                                var s = JSON.parse(t(this).attr("paramquest"));
                                i = t.extend(i, s)
                            }
                            e[t(a).attr("arrayvalue")].push(i)
                        }
                    }))),
                    "" != r && !t(a).hasClass("getvalued"))
                        if (r.match(/\./)) {
                            if (h = r.split("."),
                            n = h[0],
                            3 == h.length)
                                s[h[1]] = s[h[1]] || {},
                                s[h[1]][h[2]] = l;
                            else if ("json" == t(a).data("type")) {
                                if (s[h[1]] = JSON.parse(l),
                                t(a).attr("paramquest")) {
                                    var p = JSON.parse(t(a).attr("paramquest"));
                                    s[h[1]] = t.extend(s[h[1]], p)
                                }
                            } else
                                s[h[1]] = l;
                            e[n] ? e[n] = t.extend({}, e[n], s) : e[n] = s
                        } else
                            e[r] = l
                }
            });
            var a = {};
            for (var n in e) {
                var r = e[n];
                a[n] = "object" == typeof r ? JSON.stringify(r) : e[n]
            }
            return t(".getvalued").removeClass("getvalued"),
            a
        },
        setHash: function(i) {
            var e = "";
            i = t.extend(this.getHash(), i);
            var s = [];
            for (var a in i)
                "" != i[a] && s.push(a + "=" + encodeURIComponent(i[a]));
            return e += s.join("&"),
            location.hash = e,
            this
        },
        getHash: function(t) {
            if ("string" == typeof t)
                return this.getQuery(t, "#");
            var i = {}
              , e = location.hash;
            if (e.length > 0) {
                e = e.substr(1);
                for (var s = e.split("&"), a = 0, n = s.length; a < n; a++) {
                    var r = s[a].split("=");
                    r.length > 0 && (i[r[0]] = decodeURI(r[1]) || "")
                }
            }
            return i
        }
    }
}),
function(t, i) {
    "function" == typeof define && define.amd ? define(["jquery", "query"], i) : "object" == typeof exports ? module.exports = i() : t.Paging = i(window.Zepto || window.jQuery || $, Query)
}(this, function(t, i) {
    function e() {
        var t = Math.random().toString().replace(".", "");
        this.id = "Paging_" + t
    }
    return t.fn.Paging = function(i) {
        var s = [];
        return t(this).each(function() {
            var a = t.extend({
                target: t(this)
            }, i)
              , n = new e;
            n.init(a),
            s.push(n)
        }),
        s
    }
    ,
    e.prototype = {
        init: function(i) {
            this.settings = t.extend({
                callback: null,
                pagesize: 10,
                current: 1,
                prevTpl: "Prev",
                nextTpl: "Next",
                firstTpl: "First",
                lastTpl: "Last",
                ellipseTpl: "...",
                toolbar: !1,
                hash: !1,
                pageSizeList: [5, 10, 15, 20]
            }, i),
            this.target = t(this.settings.target),
            this.container = t('<div id="' + this.id + '" class="ui-paging-container"/>'),
            this.target.append(this.container),
            this.render(this.settings),
            this.format(),
            this.bindEvent()
        },
        render: function(t) {
            void 0 !== t.count ? this.count = t.count : this.count = this.settings.count,
            void 0 !== t.pagesize ? this.pagesize = t.pagesize : this.pagesize = this.settings.pagesize,
            void 0 !== t.current ? this.current = t.current : this.current = this.settings.current,
            this.pagecount = Math.ceil(this.count / this.pagesize),
            this.format()
        },
        bindEvent: function() {
            var i = this;
            this.container.on("click", "li.js-page-action,li.ui-pager", function(e) {
                if (t(this).hasClass("ui-pager-disabled") || t(this).hasClass("focus"))
                    return !1;
                t(this).hasClass("js-page-action") ? (t(this).hasClass("js-page-first") && (i.current = 1),
                t(this).hasClass("js-page-prev") && (i.current = Math.max(1, i.current - 1)),
                t(this).hasClass("js-page-next") && (i.current = Math.min(i.pagecount, i.current + 1)),
                t(this).hasClass("js-page-last") && (i.current = i.pagecount)) : t(this).data("page") && (i.current = parseInt(t(this).data("page"))),
                i.go()
            })
        },
        go: function(t) {
            var e = this;
            this.current = t || this.current,
            this.current = Math.max(1, e.current),
            this.current = Math.min(this.current, e.pagecount),
            this.format(),
            this.settings.hash && i.setHash({
                page: this.current
            }),
            this.settings.callback && this.settings.callback(this.current, this.pagesize, this.pagecount)
        },
        changePagesize: function(t) {
            this.render({
                pagesize: t
            }),
            this.settings.changePagesize && this.settings.changePagesize.call(this, this.pagesize, this.current, this.pagecount)
        },
        format: function() {
            var i = "<ul>";
            if (i += '<li class="js-page-first js-page-action ui-pager" >' + this.settings.firstTpl + "</li>",
            i += '<li class="js-page-prev js-page-action ui-pager">' + this.settings.prevTpl + "</li>",
            this.pagecount > 6) {
                if (i += '<li data-page="1" class="ui-pager">1</li>',
                this.current <= 2)
                    i += '<li data-page="2" class="ui-pager">2</li>',
                    i += '<li data-page="3" class="ui-pager">3</li>',
                    i += '<li class="ui-paging-ellipse">' + this.settings.ellipseTpl + "</li>";
                else if (this.current > 2 && this.current <= this.pagecount - 2)
                    this.current > 3 && (i += "<li>" + this.settings.ellipseTpl + "</li>"),
                    i += '<li data-page="' + (this.current - 1) + '" class="ui-pager">' + (this.current - 1) + "</li>",
                    i += '<li data-page="' + this.current + '" class="ui-pager">' + this.current + "</li>",
                    i += '<li data-page="' + (this.current + 1) + '" class="ui-pager">' + (this.current + 1) + "</li>",
                    this.current < this.pagecount - 2 && (i += '<li class="ui-paging-ellipse" class="ui-pager">' + this.settings.ellipseTpl + "</li>");
                else {
                    i += '<li class="ui-paging-ellipse" >' + this.settings.ellipseTpl + "</li>";
                    for (var e = this.pagecount - 2; e < this.pagecount; e++)
                        i += '<li data-page="' + e + '" class="ui-pager">' + e + "</li>"
                }
                i += '<li data-page="' + this.pagecount + '" class="ui-pager">' + this.pagecount + "</li>"
            } else
                for (var e = 1; e <= this.pagecount; e++)
                    i += '<li data-page="' + e + '" class="ui-pager">' + e + "</li>";
            i += '<li class="js-page-next js-page-action ui-pager">' + this.settings.nextTpl + "</li>",
            i += '<li class="js-page-last js-page-action ui-pager">' + this.settings.lastTpl + "</li>",
            i += "</ul>",
            this.container.html(i),
            1 == this.current && (t(".js-page-prev", this.container).addClass("ui-pager-disabled"),
            t(".js-page-first", this.container).addClass("ui-pager-disabled")),
            this.current == this.pagecount && (t(".js-page-next", this.container).addClass("ui-pager-disabled"),
            t(".js-page-last", this.container).addClass("ui-pager-disabled")),
            this.container.find('li[data-page="' + this.current + '"]').addClass("focus").siblings().removeClass("focus"),
            this.settings.toolbar && this.bindToolbar()
        },
        bindToolbar: function() {
            for (var i = this, e = t('<li class="ui-paging-toolbar"><select class="ui-select-pagesize"></select><input type="text" class="ui-paging-count"/></li>'), s = t(".ui-select-pagesize", e), a = "", n = 0, r = this.settings.pageSizeList.length; n < r; n++)
                a += '<option value="' + this.settings.pageSizeList[n] + '">' + this.settings.pageSizeList[n] + "</option>";
            s.html(a),
            s.val(this.pagesize),
            t("input", e).val(this.current),
            t("input", e).click(function() {
                t(this).select()
            }).keydown(function(e) {
                if (13 == e.keyCode) {
                    var s = parseInt(t(this).val()) || 1;
                    i.go(s)
                }
            }),
            t("a", e).click(function() {
                var e = parseInt(t(this).prev().val()) || 1;
                i.go(e)
            }),
            s.change(function() {
                i.changePagesize(t(this).val())
            }),
            this.container.children("ul").append(e)
        }
    },
    e
});
