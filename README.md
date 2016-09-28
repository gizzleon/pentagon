# pentagon / 教五大楼

---

## 时间线
1. 2016/09/27 - pentagon v0.9

## 什么是pentagon
Pentagon将东南大学本科生选课常用的操作封装起来，并提供了一个图形界面方便同学选择自己想要的课程。登陆前需要在右边的面板中配置好选课列表。开始选课后选课操作会执行10,000次，可以通过`Interval`（时间间隔）来控制总时间。

## 如何配置选课列表
在`Type`中选择你想要选的课的类别，拼音对照关系如下：

 - tuijian - 在选课主页面可以服从推荐的课程
 - renwen - 人文社科类课程
 - jingguan - 经济管理类课程
 - ziran - 自然科学类课程
 - seminar - seminar研讨课

在`Keyword`中输入你想选的课程的关键词，可以是课程名称或任课老师。请注意，程序会从页面中寻找最先匹配的字段，所以请尽可能**完整并准确地输入关键词**。

另外，在`Keyword`中输入`*`并添加后，该条规则的优先级会高于同一`Type`的规则。在`tuijian`（服从推荐）的类别中，`*`意味着选择所有能够服推的课程；而在其他类别中，`*`意味着在该类别所有能够选择的课程中任选一门。

## 待完成
1. 解决编码问题，完全汉化程序。
2. 加入[验证码识别模块][1]。

## 其他y
- Pentagon是基于[seu-jwc-fker][2]改写而来的
- 若显示"初始化失败"请尝试能否手动在浏览器中进入选课页面
- 本程序旨在帮助同学理性选择自己喜欢的课程，同时尽量避免对手动选课的同学造成太大不公平，所以有一些额外的限制
- 任何能够获取源码的人都有权对此源码进行任何的修改与使用。但如若要发布成可执行文件，请尽量考虑手动选课的同学和教务处服务器的负载能力
- 如果出现BUG可以联系：`gizzle.y@live.com`；欢迎PR



  [1]: https://github.com/gizzleon/SEU-jwc-decoder
  [2]: https://github.com/SnoozeZ/seu-jwc-fker