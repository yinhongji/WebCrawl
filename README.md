# WebCrawl
这里ng为不带登录权限的爬虫，ng_login为带登录权限的爬虫

这里为了方便，写了一个test.py来调用两个爬虫，每个爬虫都留了url接口
对于ng文件夹来说使用命令如下：

scrapy crawl url -a url=http://test.com

对于ng_login文件夹来说使用命令如下：

scrapy crawl url -a url=http://test.com/login.php -a username=admin -a password=admin

这里的ng_login会自动识别登录form的用户名和密码的name，为白名单配置（效果来说一般般），配置接口为url.py的第33行和34行

最后结果都是会写到图数据库里的，图数据库配置在pipeline.py的第10行，根据自己需求进行修改！
