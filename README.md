# Minecraft 区块自动重置器 (ARC Chunk Auto Resetter)

## 📋 项目简介

**ARC Chunk Auto Resetter** 是一个专为Minecraft服务器设计的智能区块重置工具，特别针对使用 **EndStone ARC Core 领地插件** 的服务器。该工具可以安全地重置世界中未被领地保护的区块，让这些区块重新生成，同时完全保护玩家的建筑和领地。

### ✨ 主要特点

- 🛡️ **智能领地保护** - 自动识别并保护所有领地覆盖的区块
- 🔧 **额外保护距离** - 可在领地边界外设置额外的保护区域
- 🎯 **精确区块控制** - 支持手动指定要保护的特定区块
- 🖥️ **双操作模式** - 提供命令行版本和友好的图形界面
- 📊 **实时进度显示** - 详细的操作进度和统计信息
- 🌍 **多维度支持** - 支持主世界、下界、末地三个维度
- 🔍 **预览功能** - 执行前可预览将要进行的操作
- ⚡ **高性能处理** - 基于Amulet Core API，稳定高效

## 🎯 使用场景

- **服务器地图重置** - 重置过度开发的区域，保留玩家建筑
- **资源区更新** - 定期重置资源采集区域，保持资源丰富
- **地形修复** - 修复被破坏的自然地形，恢复原始风貌
- **版本升级** - 让旧区块重新生成以获得新版本特性

## 🛠️ 安装要求

### 系统要求
- **操作系统**: Windows 10/11, macOS, Linux
- **Python版本**: Python 3.8 或更高版本
- **内存**: 建议 4GB 以上（处理大世界时需要更多内存）

### 依赖包

本项目已提供 `requirements.txt` 作为标准依赖清单，推荐使用它来安装依赖。

```bash
# 克隆或进入项目目录后
pip install -r requirements.txt
```

### 使用 Miniforge 创建 Python 3.13 环境（推荐）

为避免系统 Python 污染，推荐使用 Miniforge（基于 conda-forge 的轻量级发行版）创建隔离环境。

1) 安装 Miniforge（选择本机平台安装器）
- Windows: 打开浏览器访问 `https://github.com/conda-forge/miniforge/releases` 下载并安装最新的 Miniforge3 Windows 安装包

2) 创建并激活名为 `amulet` 的 Python 3.13 环境
```bash
conda create -n amulet python=3.13
conda activate amulet
```

3) 安装项目依赖（基于 requirements.txt）
```bash
pip install -r requirements.txt
```

## 📦 文件结构

```
ARC-Chunk-Auto-Reseter/
├── ChunkAutoResetter.py      # 核心重置逻辑
├── ChunkResetterGUI.py       # 图形用户界面
├── land_data_reader.py       # 领地数据读取器
├── start_gui.bat            # GUI启动脚本 (Windows)
├── requirements.txt         # 依赖清单（用于pip安装）
└── README.md               # 项目文档
```

## 🚀 快速开始

### 效果展示

重置前与重置后的对比（仅清理未受领地保护的区块）：

![重置前](res/before_reset.png)

![重置后](res/after_reset.png)

### 图形界面

1. **Windows用户**:
   ```bash
   # 双击运行
   start_gui.bat
   ```

2. **其他系统**:
   ```bash
   python ChunkResetterGUI.py
   ```

3. **操作步骤**:
   - 选择Minecraft世界文件夹
   - 选择领地数据库文件 (database.db)
   - 设置搜索范围和额外保护距离
   - 点击"加载配置"查看领地信息
   - 点击"预览重置操作"查看影响范围
   - 确认无误后点击"执行重置"

### 数据库格式说明
 - 程序会自动读取数据库中 `lands` 表的数据来计算需要保护的区块
 - 坐标单位为方块（block），区块大小为 16×16 方块；程序内部会按 16 取整映射到区块坐标

必需的表与字段（与截图一致）：

```sql
-- 建议的表结构（SQLite）
CREATE TABLE IF NOT EXISTS lands (
  land_id               INTEGER PRIMARY KEY,   -- 领地ID
  owner_uuid            TEXT NOT NULL,         -- 拥有者UUID
  land_name             TEXT NOT NULL,         -- 领地名称
  dimension             TEXT NOT NULL,         -- 维度: Overworld/Nether/TheEnd
  min_x                 INTEGER NOT NULL,      -- 边界最小X（方块坐标）
  max_x                 INTEGER NOT NULL,      -- 边界最大X（方块坐标）
  min_z                 INTEGER NOT NULL,      -- 边界最小Z（方块坐标）
  max_z                 INTEGER NOT NULL,      -- 边界最大Z（方块坐标）
  tp_x                  REAL,                  -- 可选: 传送点X
  tp_y                  REAL,                  -- 可选: 传送点Y
  tp_z                  REAL,                  -- 可选: 传送点Z
  shared_users          TEXT,                  -- 可选: 共享玩家（JSON或逗号分隔）
  allow_explosion       INTEGER DEFAULT 0,     -- 可选: 是否允许爆炸 0/1
  allow_public_interact INTEGER DEFAULT 0      -- 可选: 是否允许公共交互 0/1
);
```

字段含义与要求：
- land_id: 整数主键，唯一标识一个领地
- owner_uuid: 拥有者玩家UUID（字符串）
- land_name: 领地名称（字符串）
- dimension: 维度名称，需为以下三者之一：`Overworld`、`Nether`、`TheEnd`
- min_x/max_x/min_z/max_z: 领地边界在方块坐标系中的包围盒（包含端点）
- tp_x/tp_y/tp_z: 领地传送点（可为空，不影响本程序）
- shared_users: 共享用户列表；格式不限，程序不解析此字段
- allow_explosion/allow_public_interact: 行为开关；程序不依赖

维度映射（数据库 -> Minecraft ID）：
- Overworld -> `minecraft:overworld`
- Nether -> `minecraft:the_nether`
- TheEnd -> `minecraft:the_end`

说明：
- 程序会将边界盒按区块维度转换为区块范围 `[min_x//16, max_x//16] × [min_z//16, max_z//16]`
- 若设置了“额外保护距离”，会在区块范围四周再扩展 N 圈区块后参与保护判断


## ⚙️ 配置说明

### 重置设置

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| **搜索范围** | 检查的区块坐标范围 | 750 | 50表示检查-50到50共101×101个区块 |
| **额外保护距离** | 领地边界外的额外保护距离 | 0 | 2表示在领地外再保护2圈区块 |
| **维度** | 要处理的游戏维度 | 主世界 | 主世界/下界/末地 |

### 维度对应关系

| 游戏维度 | Minecraft ID | 数据库名称 |
|----------|-------------|-----------|
| 主世界 | `minecraft:overworld` | `Overworld` |
| 下界 | `minecraft:the_nether` | `Nether` |
| 末地 | `minecraft:the_end` | `TheEnd` |

## 🔧 高级用法

### 手动指定保护区块

```python
# 不使用领地数据库，手动指定要保护的区块
resetter = ChunkAutoResetter("path/to/world")  # 不传入数据库路径
resetter.load_world()

# 指定要保护的区块坐标
preserve_chunks = [(0, 0), (1, 0), (0, 1), (1, 1)]  # 保护spawn点附近

stats = resetter.reset_chunks_with_preserve(
    preserve_chunks=preserve_chunks,
    search_range=50,
    dry_run=False
)
```

## ⚠️ 重要注意事项

### 🔴 使用前必读

1. **备份世界** - 操作前务必备份您的世界文件！
2. **关闭服务器** - 操作期间确保Minecraft服务器已关闭
3. **测试环境** - 建议先在测试环境中验证效果
4. **内存要求** - 大世界处理需要足够的系统内存

### 🛡️ 安全机制

- ✅ 支持试运行模式，可预览而不实际修改
- ✅ 详细的操作统计和日志记录
- ✅ 自动错误处理和恢复机制
- ✅ 严格的领地边界计算和保护

### 📊 性能建议

- **搜索范围**: 建议不超过1000，避免内存不足
- **分批处理**: 大范围重置可分多次小范围执行
- **进度监控**: 使用GUI界面可更好地监控处理进度

## 🐛 故障排除

### 常见问题

**Q: 提示"无法解析导入amulet"**
```bash
A: 确保已安装amulet-core包
pip install amulet-core
```

**Q: 中文显示乱码**
```bash
A: Windows用户请使用start_gui.bat启动，已自动设置UTF-8编码
```

**Q: 找不到领地数据**
```bash
A: 检查数据库路径是否正确，确保是EndStone ARC Core的database.db文件
```

**Q: 内存不足错误**
```bash
A: 减小搜索范围，或增加系统内存
```

### 错误日志

程序运行时会在GUI日志区域或控制台显示详细的错误信息，请根据错误提示进行相应处理。

## 🔄 更新日志
### v1.0
- 🎉 初始版本发布
- 🛡️ 基础领地保护功能
- 🌍 多维度支持
- 🖥️ 添加图形用户界面
- 📊 实现实时进度监控
- 🔍 添加操作预览功能
- ✨ 新增额外保护距离功能
- 🎨 GUI进度条升级为真实进度显示
- 🐛 修复区块删除后的状态一致性问题
- ⚡ 优化大范围处理的性能和稳定性

## 📞 技术支持

如果您在使用过程中遇到问题，请：

1. 检查上述故障排除部分
2. 确保按照安装要求正确配置环境
3. 查看程序日志中的详细错误信息
4. 在测试环境中重现问题

## 📄 许可证

本项目采用 **GNU Affero General Public License v3.0 (AGPL-3.0)** 授权。

- 当您修改并部署或以网络服务形式提供本项目时，您必须在同等许可下对外提供完整源代码。
- 详见本仓库根目录的 `LICENSE` 文件。

致谢（Attribution）：
- 本项目基于 [Amulet-Core](https://github.com/Amulet-Team/Amulet-Core) 提供的底层读写能力进行世界数据的操作与保存，特此感谢其开源生态与文档支持。[Amulet-Core GitHub 仓库](https://github.com/Amulet-Team/Amulet-Core)

---

**⚡ 让我们一起打造更好的Minecraft服务器体验！** 🎮
