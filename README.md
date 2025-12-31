```json
{
    "entry_file": "trae_obsidian_mcp.py",
    "requirements": [
        "mcp - server - sdk>=1.0.0",
        "jieba>=0.42.1",
        "pyyaml>=6.0.1"
    ],
    "start_command": "python trae_obsidian_mcp.py",
    "port": 5000,
    "health_check": "/health",
    "tool_definitions": [
        {
            "name": "extract_summary_keywords",
            "description": "从当日重点对话总结中提取核心关键词，用于Dataview表格",
            "input_schema": {
                "summary_text": {
                    "type": "string",
                    "description": "当日重点对话总结文本（含#标签）"
                },
                "top_k": {
                    "type": "integer",
                    "default": 3,
                    "description": "提取关键词数量"
                }
            },
            "output_schema": {
                "keywords": {
                    "type": "string",
                    "description": "逗号分隔的关键词字符串"
                }
            }
        },
        {
            "name": "auto_complete_tags",
            "description": "基于已有标签库自动补全对话标签，避免生成过多标签",
            "input_schema": {
                "user_input": {
                    "type": "string",
                    "description": "用户当前输入的文本"
                },
                "trae_response": {
                    "type": "string",
                    "description": "Trae的回复内容"
                },
                "existing_tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "用户手动添加的标签列表"
                },
                "tag_library_path": {
                    "type": "string",
                    "default": "标签库.md",
                    "description": "Obsidian标签库文件路径"
                }
            },
            "output_schema": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "补全后的标签列表（含去重）"
                }
            }
        },
        {
            "name": "append_daily_note",
            "description": "将对话内容增量存储到Obsidian笔记",
            "input_schema": {
                "user_message": {
                    "type": "string",
                    "description": "用户的单轮输入内容"
                },
                "trae_message": {
                    "type": "string",
                    "description": "Trae的单轮回复内容"
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "当前对话的标签列表"
                },
                "vault_path": {
                    "type": "string",
                    "description": "Obsidian库的根路径"
                },
                "note_dir": {
                    "type": "string",
                    "default": "AI - Memory",
                    "description": "对话笔记存放的文件夹"
                }
            },
            "output_schema": {
                "status": {
                    "type": "string",
                    "description": "存储结果状态（success/failed）"
                },
                "file_path": {
                    "type": "string"
                }
            }
        }
    ]
}
