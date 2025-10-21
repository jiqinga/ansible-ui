/**
 * 🇨🇳 中文常量定义
 * 
 * 包含中文环境下的常用常量和配置
 */

/**
 * 📅 中文日期相关常量
 */
export const CHINESE_DATE = {
  // 星期
  WEEKDAYS: ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'],
  WEEKDAYS_SHORT: ['日', '一', '二', '三', '四', '五', '六'],
  
  // 月份
  MONTHS: [
    '一月', '二月', '三月', '四月', '五月', '六月',
    '七月', '八月', '九月', '十月', '十一月', '十二月'
  ],
  MONTHS_SHORT: [
    '1月', '2月', '3月', '4月', '5月', '6月',
    '7月', '8月', '9月', '10月', '11月', '12月'
  ],
  
  // 季节
  SEASONS: ['春季', '夏季', '秋季', '冬季'],
  
  // 时间段
  TIME_PERIODS: {
    MORNING: '上午',
    AFTERNOON: '下午',
    EVENING: '晚上',
    NIGHT: '深夜',
    DAWN: '凌晨'
  },
  
  // 相对时间
  RELATIVE_TIME: {
    NOW: '刚刚',
    MINUTES_AGO: '分钟前',
    HOURS_AGO: '小时前',
    DAYS_AGO: '天前',
    WEEKS_AGO: '周前',
    MONTHS_AGO: '个月前',
    YEARS_AGO: '年前'
  }
} as const

/**
 * 🔢 中文数字常量
 */
export const CHINESE_NUMBERS = {
  DIGITS: ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'],
  UNITS: ['', '十', '百', '千', '万', '十万', '百万', '千万', '亿'],
  
  // 序数词
  ORDINALS: ['第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十'],
  
  // 量词
  QUANTIFIERS: {
    GENERAL: '个',
    PEOPLE: '位',
    ANIMALS: '只',
    BOOKS: '本',
    PAPERS: '张',
    BOTTLES: '瓶',
    CUPS: '杯',
    CARS: '辆',
    BUILDINGS: '栋',
    FLOORS: '层'
  }
} as const

/**
 * 🎯 状态相关常量
 */
export const CHINESE_STATUS = {
  // 任务状态
  TASK_STATUS: {
    PENDING: '等待中',
    RUNNING: '运行中',
    SUCCESS: '成功',
    FAILED: '失败',
    CANCELLED: '已取消',
    TIMEOUT: '超时',
    PAUSED: '已暂停',
    RESUMED: '已恢复'
  },
  
  // 连接状态
  CONNECTION_STATUS: {
    ONLINE: '在线',
    OFFLINE: '离线',
    CONNECTING: '连接中',
    DISCONNECTED: '已断开',
    UNKNOWN: '未知'
  },
  
  // 系统状态
  SYSTEM_STATUS: {
    HEALTHY: '健康',
    WARNING: '警告',
    CRITICAL: '严重',
    ERROR: '错误',
    MAINTENANCE: '维护中'
  },
  
  // 通用状态
  GENERAL_STATUS: {
    ACTIVE: '活跃',
    INACTIVE: '非活跃',
    ENABLED: '已启用',
    DISABLED: '已禁用',
    LOADING: '加载中',
    COMPLETED: '已完成',
    PROCESSING: '处理中',
    WAITING: '等待中'
  }
} as const

/**
 * 🏷️ 优先级常量
 */
export const CHINESE_PRIORITY = {
  LEVELS: {
    LOW: '低优先级',
    NORMAL: '普通',
    MEDIUM: '中等',
    HIGH: '高优先级',
    URGENT: '紧急',
    CRITICAL: '极其重要'
  },
  
  NUMERIC: {
    1: '最低',
    2: '较低',
    3: '普通',
    4: '较高',
    5: '最高'
  }
} as const

/**
 * 👥 角色权限常量
 */
export const CHINESE_ROLES = {
  ADMIN: '系统管理员',
  OPERATOR: '操作员',
  VIEWER: '查看者',
  GUEST: '访客',
  USER: '普通用户',
  MODERATOR: '协调员',
  EDITOR: '编辑者',
  OWNER: '所有者',
  MEMBER: '成员'
} as const

/**
 * 📊 文件类型常量
 */
export const CHINESE_FILE_TYPES = {
  DOCUMENT: '文档',
  IMAGE: '图片',
  VIDEO: '视频',
  AUDIO: '音频',
  ARCHIVE: '压缩包',
  CODE: '代码文件',
  DATA: '数据文件',
  EXECUTABLE: '可执行文件',
  FONT: '字体文件',
  OTHER: '其他文件'
} as const

/**
 * 🌐 网络相关常量
 */
export const CHINESE_NETWORK = {
  PROTOCOLS: {
    HTTP: 'HTTP协议',
    HTTPS: 'HTTPS协议',
    FTP: 'FTP协议',
    SSH: 'SSH协议',
    TCP: 'TCP协议',
    UDP: 'UDP协议'
  },
  
  STATUS_CODES: {
    200: '请求成功',
    201: '创建成功',
    400: '请求错误',
    401: '未授权',
    403: '禁止访问',
    404: '未找到',
    500: '服务器错误',
    502: '网关错误',
    503: '服务不可用'
  }
} as const

/**
 * 📏 单位常量
 */
export const CHINESE_UNITS = {
  // 长度单位
  LENGTH: {
    MM: '毫米',
    CM: '厘米',
    M: '米',
    KM: '千米',
    INCH: '英寸',
    FOOT: '英尺'
  },
  
  // 重量单位
  WEIGHT: {
    G: '克',
    KG: '千克',
    T: '吨',
    LB: '磅',
    OZ: '盎司'
  },
  
  // 面积单位
  AREA: {
    M2: '平方米',
    KM2: '平方千米',
    HA: '公顷',
    ACRE: '英亩'
  },
  
  // 体积单位
  VOLUME: {
    ML: '毫升',
    L: '升',
    M3: '立方米',
    GAL: '加仑'
  },
  
  // 温度单位
  TEMPERATURE: {
    C: '摄氏度',
    F: '华氏度',
    K: '开尔文'
  },
  
  // 存储单位
  STORAGE: {
    B: '字节',
    KB: '千字节',
    MB: '兆字节',
    GB: '吉字节',
    TB: '太字节',
    PB: '拍字节'
  }
} as const

/**
 * 🎨 颜色相关常量
 */
export const CHINESE_COLORS = {
  BASIC: {
    RED: '红色',
    ORANGE: '橙色',
    YELLOW: '黄色',
    GREEN: '绿色',
    BLUE: '蓝色',
    PURPLE: '紫色',
    PINK: '粉色',
    BROWN: '棕色',
    BLACK: '黑色',
    WHITE: '白色',
    GRAY: '灰色'
  },
  
  SEMANTIC: {
    PRIMARY: '主色',
    SECONDARY: '辅助色',
    SUCCESS: '成功色',
    WARNING: '警告色',
    DANGER: '危险色',
    INFO: '信息色'
  }
} as const

/**
 * 📱 设备类型常量
 */
export const CHINESE_DEVICES = {
  DESKTOP: '桌面电脑',
  LAPTOP: '笔记本电脑',
  TABLET: '平板电脑',
  MOBILE: '手机',
  WATCH: '智能手表',
  TV: '智能电视',
  OTHER: '其他设备'
} as const

/**
 * 🌍 地区相关常量
 */
export const CHINESE_REGIONS = {
  // 中国省份（简化版）
  PROVINCES: [
    '北京', '上海', '天津', '重庆',
    '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东',
    '河南', '湖北', '湖南', '广东', '海南',
    '四川', '贵州', '云南', '陕西', '甘肃', '青海',
    '台湾', '内蒙古', '广西', '西藏', '宁夏', '新疆',
    '香港', '澳门'
  ],
  
  // 时区
  TIMEZONES: {
    'Asia/Shanghai': '北京时间',
    'UTC': '协调世界时',
    'America/New_York': '纽约时间',
    'Europe/London': '伦敦时间',
    'Asia/Tokyo': '东京时间'
  }
} as const

/**
 * 🔧 操作类型常量
 */
export const CHINESE_OPERATIONS = {
  CREATE: '创建',
  READ: '查看',
  UPDATE: '更新',
  DELETE: '删除',
  COPY: '复制',
  MOVE: '移动',
  RENAME: '重命名',
  UPLOAD: '上传',
  DOWNLOAD: '下载',
  IMPORT: '导入',
  EXPORT: '导出',
  BACKUP: '备份',
  RESTORE: '恢复',
  SYNC: '同步',
  REFRESH: '刷新'
} as const

/**
 * 📋 表单相关常量
 */
export const CHINESE_FORM = {
  VALIDATION_MESSAGES: {
    REQUIRED: '此字段为必填项',
    EMAIL_INVALID: '请输入有效的邮箱地址',
    PHONE_INVALID: '请输入有效的手机号码',
    PASSWORD_WEAK: '密码强度太弱',
    PASSWORD_MISMATCH: '两次输入的密码不一致',
    NUMBER_INVALID: '请输入有效的数字',
    URL_INVALID: '请输入有效的URL地址',
    DATE_INVALID: '请输入有效的日期'
  },
  
  PLACEHOLDERS: {
    EMAIL: '请输入邮箱地址',
    PHONE: '请输入手机号码',
    PASSWORD: '请输入密码',
    CONFIRM_PASSWORD: '请确认密码',
    USERNAME: '请输入用户名',
    SEARCH: '请输入搜索关键词',
    REMARK: '请输入备注信息'
  }
} as const

/**
 * 🎯 业务相关常量
 */
export const CHINESE_BUSINESS = {
  // Ansible 相关
  ANSIBLE: {
    PLAYBOOK: 'Playbook',
    INVENTORY: '主机清单',
    TASK: '任务',
    ROLE: '角色',
    MODULE: '模块',
    VARIABLE: '变量',
    TEMPLATE: '模板',
    HANDLER: '处理器'
  },
  
  // 系统监控
  MONITORING: {
    CPU: 'CPU使用率',
    MEMORY: '内存使用率',
    DISK: '磁盘使用率',
    NETWORK: '网络状态',
    LOAD: '系统负载',
    UPTIME: '运行时间'
  }
} as const

/**
 * 🎨 主题相关常量
 */
export const CHINESE_THEME = {
  MODES: {
    LIGHT: '浅色模式',
    DARK: '深色模式',
    AUTO: '跟随系统'
  },
  
  SIZES: {
    SMALL: '小',
    MEDIUM: '中',
    LARGE: '大',
    EXTRA_LARGE: '特大'
  }
} as const