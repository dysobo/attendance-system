#!/usr/bin/env python3
"""
测试推送卡片美化格式
企业微信 textcard 支持的 HTML 标签：
  <div class="gray">灰色文字</div>
  <div class="normal">正常文字</div>
  <div class="highlight">高亮文字</div>
"""

def main():
    # 1. 调休申请 → 管理员
    print("=" * 50)
    print("1. 调休申请 → 管理员")
    print("=" * 50)
    print('title: 📋 调休申请 · 待审批')
    print('description:')
    print('  <div class="highlight">张三 提交了调休申请</div>')
    print('  <div class="normal">📅 日期：2026-04-01</div>')
    print('  <div class="normal">⏱ 时长：4.0 小时</div>')
    print('  <div class="normal">💬 事由：家里有事需要处理</div>')
    print('  <div class="gray">请及时审批处理</div>')
    print()

    # 2. 调休审批结果 → 组员
    print("=" * 50)
    print("2. 调休审批结果 → 组员")
    print("=" * 50)
    print('title: ✅ 调休申请已批准')
    print('description:')
    print('  <div class="highlight">您的调休申请已批准</div>')
    print('  <div class="normal">📅 日期：2026-04-01</div>')
    print('  <div class="normal">⏱ 时长：4.0 小时</div>')
    print('  <div class="normal">💬 留言：下次提前申请</div>')
    print('  <div class="gray">点击查看详情</div>')
    print()

    # 3. 加班申请 → 管理员
    print("=" * 50)
    print("3. 加班申请 → 管理员")
    print("=" * 50)
    print('title: 📋 加班申请 · 待确认')
    print('description:')
    print('  <div class="highlight">张三 提交了加班申请</div>')
    print('  <div class="normal">📅 日期：2026-04-01</div>')
    print('  <div class="normal">⏱ 时长：1.0 小时</div>')
    print('  <div class="normal">💬 事由：项目紧急上线</div>')
    print('  <div class="gray">请及时确认处理</div>')
    print()

    # 4. 加班审批结果 → 组员
    print("=" * 50)
    print("4. 加班审批结果 → 组员")
    print("=" * 50)
    print('title: ✅ 加班申请已确认')
    print('description:')
    print('  <div class="highlight">您的加班申请已确认</div>')
    print('  <div class="normal">📅 日期：2026-04-01</div>')
    print('  <div class="normal">⏱ 时长：1.0 小时</div>')
    print('  <div class="normal">💬 留言：辛苦了</div>')
    print('  <div class="gray">点击查看详情</div>')
    print()

    print("=" * 50)
    print("✅ 格式预览完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
