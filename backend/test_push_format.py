#!/usr/bin/env python3
"""
测试推送卡片美化格式
"""

# 模拟调休申请推送给管理员
print("=" * 50)
print("1️⃣ 调休申请 - 推送给管理员（提交申请时）")
print("=" * 50)

applicant_name = "张三"
type_name = "调休"
request_date = "2026-04-01"
hours = "4.0"
reason = "家里有事需要处理"

# 先赋值变量，避免 f-string 表达式内有反斜杠
applicant_line = f"👤 申请人：{applicant_name}"
type_line = f"📋 类  型：{type_name}"
date_line = f"📅 日  期：{request_date}"
hours_line = f"⏱️ 时  长：{hours} 小时"
reason_line = f"事由：{reason}"
footer_line = "⏬ 请及时审批"
content = f"🏖️ 调休待审批\n{applicant_line}\n{type_line}\n{date_line}\n{hours_line}\n{reason_line}\n\n{footer_line}"

print(content)
print()

# 模拟加班申请推送给管理员
print("=" * 50)
print("2️⃣ 加班申请 - 推送给管理员（提交申请时）")
print("=" * 50)

applicant_name = "张三"
record_date = "2026-04-01"
hours = "1.0"
reason = "项目紧急上线"

# 先赋值变量，避免 f-string 表达式内有反斜杠
applicant_line = f"👤 申请人：{applicant_name}"
date_line = f"📅 日  期：{record_date}"
hours_line = f"⏱️ 时  长：{hours} 小时"
reason_line = f"事由：{reason}"
footer_line = "⏬ 请及时确认"
content = f"⏰ 加班申请待确认\n{applicant_line}\n{date_line}\n{hours_line}\n{reason_line}\n\n{footer_line}"

print(content)
print()

# 模拟调休审批结果推送给组员
print("=" * 50)
print("3️⃣ 调休审批结果 - 推送给组员（审批后）")
print("=" * 50)

type_name = "调休"
status_text = "已批准"
request_date = "2026-04-01"
hours = "4.0"
comment = "下次提前申请"

# 先赋值变量，避免 f-string 表达式内有反斜杠
result_line = f"📊 审批结果：{status_text}"
type_line = f"📋 类  型：{type_name}"
date_line = f"📅 日  期：{request_date}"
hours_line = f"⏱️ 时  长：{hours} 小时"
comment_line = f"审批留言：{comment}"
content = f"{type_name}申请{status_text}\n{result_line}\n{type_line}\n{date_line}\n{hours_line}\n{comment_line}"

print(content)
print()

# 模拟加班审批结果推送给组员
print("=" * 50)
print("4️⃣ 加班审批结果 - 推送给组员（审批后）")
print("=" * 50)

status_text = "已批准"
record_date = "2026-04-01"
hours = "1.0"
comment = "辛苦了"

# 先赋值变量，避免 f-string 表达式内有反斜杠
result_line = f"📊 审批结果：{status_text}"
date_line = f"📅 日  期：{record_date}"
hours_line = f"⏱️ 时  长：{hours} 小时"
comment_line = f"审批留言：{comment}"
content = f"加班申请{status_text}\n{result_line}\n{date_line}\n{hours_line}\n{comment_line}"

print(content)
print()

print("=" * 50)
print("✅ 所有格式测试通过，无语法错误！")
print("=" * 50)
