function createAttendanceDataTools({ api, exportMonth, exportYear, exportSelectedUserIds, passwordForm, loadData }) {
    async function exportMonthlyStats() {
        try {
            const token = localStorage.getItem('token');
            const selectedIds = exportSelectedUserIds.value || [];
            if (!selectedIds.length) {
                throw new Error('请至少勾选一名组员');
            }

            const response = await fetch('/kq/api/export/monthly', {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    month: exportMonth.value,
                    year: exportYear.value,
                    user_ids: selectedIds
                })
            });

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/html')) {
                throw new Error('认证失败，请重新登录');
            }

            if (!response.ok) {
                const err = contentType && contentType.includes('application/json')
                    ? await response.json().catch(() => ({ detail: '导出失败' }))
                    : { detail: '导出失败' };
                throw new Error(err.detail || '导出失败');
            }

            const blob = await response.blob();
            const disposition = response.headers.get('content-disposition') || '';
            const match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
            const filename = match ? decodeURIComponent(match[1]) : `考勤统计_${exportYear.value}年${exportMonth.value}月.xlsx`;
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
            URL.revokeObjectURL(link.href);
            alert('✅ 导出成功');
        } catch (e) {
            alert(`❌ 导出失败：${e.message}`);
        }
    }

    async function exportBackup() {
        try {
            const response = await api('/backup/export?include_sensitive=true');
            const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = response.filename || `考勤备份_${new Date().toISOString().slice(0, 10)}.json`;
            link.click();
            alert('✅ 备份成功');
        } catch (e) {
            alert(`❌ 备份失败：${e.message}`);
        }
    }

    async function importBackup(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!confirm('⚠️ 警告：导入操作会清空现有数据！确定要继续吗？')) {
            event.target.value = '';
            return;
        }

        try {
            const reader = new FileReader();
            reader.onload = async (loadEvent) => {
                try {
                    const backupData = JSON.parse(loadEvent.target.result);
                    const result = await api('/backup/import', { method: 'POST', body: JSON.stringify(backupData) });
                    alert(`✅ 恢复成功！\n${JSON.stringify(result.count, null, 2)}`);
                    await loadData();
                } catch (err) {
                    alert(`❌ 恢复失败：${err.message}`);
                }
            };
            reader.readAsText(file);
        } catch (e) {
            alert(`❌ 读取文件失败：${e.message}`);
        } finally {
            event.target.value = '';
        }
    }

    async function changePassword() {
        await api('/auth/change-password', { method: 'POST', body: JSON.stringify(passwordForm.value) });
        alert('密码修改成功');
    }

    return {
        exportMonthlyStats,
        exportBackup,
        importBackup,
        changePassword
    };
}
