# autop-server
Server of autop

# Roadmap

* **2021-10-18**

  **Done**:
  
  1. kubernetes资源管理数据库设计
  2. logging模块添加输出模块名字功能
  3. 三种配置方式优先级确定(命令行 > 系统变量 > 配置文件), 由configuration模块实现
  4. ORM由sqlalchemy修改为Tortoise ORM

  **TODO**:

  1. 删除Host类型资源管理功能。暂时只保留kubernetes类型计算资源管理功能
  2. Application对象添加deployment, container_name字段, 外键绑定pod id
  3. server 启动后自动watch kubernetes api, 监控namespace, controller(目前只关注deployment), pod变化,并记录到MySQL

    
* **2021-11-08**

  **Done**:
  
  1. kubernetes资源管理数据库设计
  2. logging模块添加输出模块名字功能
  3. 三种配置方式优先级确定(命令行 > 系统变量 > 配置文件), 由configuration模块实现
  4. ORM由sqlalchemy修改为Tortoise ORM
  5. 删除Host类型资源管理功能。暂时只保留kubernetes类型计算资源管理功能
  6. Application对象添加deployment, container_name字段, 外键绑定pod id
  
  
  **TODO**:

  1. ~~server 启动后自动watch kubernetes api, 监控namespace, controller(目前只关注deployment), pod变化,并记录到MySQL~~
  2. namespace对象添加is_business flag, 减少前端api无用business显示
  3. application日志滚动