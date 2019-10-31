# qq_bot

本项目为酷Q的CoolQ HTTP API插件Python SDK 的服务框架，在原有基础上集成了插件管理、会话管理和一个简易后台，让使用Python的开发者能更加方便的开发CoolQ服务。仅支持 Python 3.6+

关于CoolQ HTTP API插件，见 [richardchien/coolq-http-api](https://github.com/richardchien/coolq-http-api)。

关于Python SDK，见 [richardchien/python-cqhttp](https://github.com/richardchien/python-cqhttp)。

## 用法
该框架需要Mysql，Redis的支持

### 安装环境

```sh
pip install pymysql,redis,cqhttp
```

### 建立必要数据库

```sql
CREATE TABLE `private_message_plugin`  (
  `plugin_name` varchar(50)  NOT NULL,
  `plugin_bname` varchar(50) NOT NULL,
  `package_name` varchar(200) NOT NULL,
  `active` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`plugin_name`)
  ) ;
CREATE TABLE `group_message_plugin`  (
  `plugin_name` varchar(50) NOT NULL,
  `plugin_bname` varchar(50) NOT NULL,
  `package_name` varchar(200) NOT NULL,
  PRIMARY KEY (`plugin_name`)
) ;
CREATE TABLE `group_message_plugin_activate`  (
  `g_id` varchar(20) NOT NULL,
  `plugin_name` varchar(50) NOT NULL,
  CONSTRAINT `fake_plugin_name` FOREIGN KEY (`plugin_name`) REFERENCES `group_message_plugin` (`plugin_name`) ON DELETE CASCADE ON UPDATE CASCADE
);

```

### 配置 CoolQ HTTP API插件

见 [richardchien/python-cqhttp](https://github.com/richardchien/python-cqhttp)

### 配置反向代理

将/admin/和/out/分辨映射到想要的端口或域名上。

### 配置setupfile.py 文件

```py
out_url = "your_out_address"
cq_api_root = 'your_api'
cq_access_token = 'your_token'
cq_secret = 'your_secret'
redis_host = 'host'
redis_port = "port"
redis_db = "db"
mysql_host = "host"
mysql_port = "port"
mysql_username = "username"
mysql_password = "your_password"
mysql_db = "your _db"
```

### 部署

`bot.run()` 只适用于开发环境，不建议用于生产环境，因此 SDK 从 1.2.1 版本开始提供 `bot.wsgi` 属性以获取其内部兼容 WSGI 的 app 对象，从而可以使用 Gunicorn、uWSGI 等软件来部署。

