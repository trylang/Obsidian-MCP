# trae_obsidian_mcp.py（整合版）
from mcp.server.fast_mcp import FastMCP
import jieba.analyse
import re
import yaml
from datetime import datetime
from pathlib import Path

# 初始化 MCP 服务（全局唯一实例）
mcp_server = FastMCP("Trae-Obsidian-Memory")

# ----------------------
# Tool 1: 核心结论关键词提取
# ----------------------
@mcp_server.tool(
    name="extract_summary_keywords",
    description="从当日重点对话总结中提取核心关键词，用于 Dataview 表格",
    input_schema={
        "summary_text": {"type": "string", "description": "当日重点对话总结文本（含#标签）"},
        "top_k": {"type": "integer", "default": 3, "description": "提取关键词数量"}
    },
    output_schema={"keywords": {"type": "string", "description": "逗号分隔的关键词字符串"}}
)
def extract_summary_keywords(summary_text: str, top_k: int = 3) -> dict:
    if not summary_text:
        return {"keywords": "无重点内容"}
    # 提取名词、动名词、动词（避免标签干扰，先移除#标签再提取）
    text_without_tags = re.sub(r"#\w+/?\w*", "", summary_text)  # 移除#标签
    keywords = jieba.analyse.extract_tags(
        text_without_tags,
        topK=top_k,
        allowPOS=('n', 'vn', 'v')  # 仅保留核心实词
    )
    return {"keywords": ", ".join(keywords)}

# ----------------------
# Tool 2: 标签自动补全（优先使用已有标签）
# ----------------------
@mcp_server.tool(
    name="auto_complete_tags",
    description="基于已有标签库自动补全对话标签，避免生成过多标签",
    input_schema={
        "user_input": {"type": "string", "description": "用户当前输入的文本"},
        "trae_response": {"type": "string", "description": "Trae 的回复内容"},
        "existing_tags": {"type": "array", "items": {"type": "string"}, "description": "用户手动添加的标签列表"},
        "tag_library_path": {"type": "string", "default": "标签库.md", "description": "Obsidian 标签库文件路径"}
    },
    output_schema={"tags": {"type": "array", "items": {"type": "string"}, "description": "补全后的标签列表（含去重）"}}
)
def auto_complete_tags(
    user_input: str,
    trae_response: str,
    existing_tags: list,
    tag_library_path: str = "标签库.md"
) -> dict:
    # 1. 加载已有标签库（从 Obsidian 的标签库.md 中读取）
    def load_existing_tags():
        try:
            with open(tag_library_path, "r", encoding="utf-8") as f:
                return set(re.findall(r"#\w+/?\w*", f.read()))  # 提取所有#标签
        except FileNotFoundError:
            return set()  # 首次使用时标签库为空，后续手动添加

    library_tags = load_existing_tags()
    full_content = user_input + " " + trae_response

    # 2. 关键词-标签映射（仅使用标签库中已存在的标签）
    scene_keywords = {
        ("代码", "Python", "编程"): "#技术/编程",
        ("论文", "文献", "学术"): "#学习/学术",
        ("需求", "项目", "任务"): "#工作/项目管理"
    }

    # 3. 匹配标签库中的标签（不生成新标签）
    auto_tags = []
    for keywords, tag in scene_keywords.items():
        if tag in library_tags and any(keyword in full_content for keyword in keywords):
            auto_tags.append(tag)

    # 4. 合并用户手动标签和自动标签（去重）
    all_tags = list(set(existing_tags + auto_tags))
    return {"tags": sorted(all_tags)}  # 排序后返回，保持一致性

# ----------------------
# Tool 3: 对话内容增量存储到 Obsidian 笔记
# ----------------------
@mcp_server.tool(
    name="append_daily_note",
    description="将对话内容增量追加到当日 Obsidian 笔记，支持自然结束/主动指令触发",
    input_schema={
        "user_message": {"type": "string", "description": "用户的单轮消息内容"},
        "trae_message": {"type": "string", "description": "Trae 的单轮回复内容"},
        "tags": {"type": "array", "items": {"type": "string"}, "description": "当前对话的标签列表"},
        "vault_path": {"type": "string", "description": "Obsidian 库的根路径"},
        "note_dir": {"type": "string", "default": "AI-Memory", "description": "对话笔记存放的文件夹"}
    },
    output_schema={"status": {"type": "string", "description": "存储结果状态（success/failed）"}, "file_path": {"type": "string"}}
)
def append_daily_note(
    user_message: str,
    trae_message: str,
    tags: list,
    vault_path: str,
    note_dir: str = "AI-Memory"
) -> dict:
    # 1. 生成当日笔记路径（如：AI-Memory/2025-12-31-Trae对话.md）
    today = datetime.now().strftime("%Y-%m-%d")
    note_path = Path(vault_path) / note_dir / f"{today}-Trae对话.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)  # 自动创建文件夹

    # 2. 格式化对话内容（带时间戳）
    timestamp = datetime.now().strftime("%H:%M:%S")
    message_block = f"- **用户**（{timestamp}）：{user_message}\n- **Trae**（{timestamp}）：{trae_message}\n\n"

    # 3. 增量追加到笔记（无弹窗，静默执行）
    try:
        # 首次创建笔记时添加 YAML 头信息
        if not note_path.exists():
            yaml_header = f"---\ntags: {tags}\ncreated: {today}\n---\n# {today} Trae 对话记录\n\n"
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(yaml_header)
        
        # 追加对话内容
        with open(note_path, "a", encoding="utf-8") as f:
            f.write(message_block)
        
        return {
            "status": "success",
            "file_path": str(note_path.relative_to(vault_path))  # 返回相对路径，便于 Obsidian 内部链接
        }
    except Exception as e:
        return {"status": "failed", "file_path": str(note_path), "error": str(e)}

# ----------------------
# 启动 MCP 服务（监听端口 5000，支持所有 tool 函数）
# ----------------------
if __name__ == "__main__":
    mcp_server.run(host="0.0.0.0", port=5000)  # 0.0.0.0 允许外部访问（如 Trae 客户端）
