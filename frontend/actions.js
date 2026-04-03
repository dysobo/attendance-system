function createAttendanceActions({
    ref,
    api,
    loadData,
    shiftForm,
    timeoffForm,
    overtimeForm,
    userForm,
    webhookForm,
    wechatConfig,
    showShiftDialog,
    showTimeoffDialog,
    showOvertimeDialog,
    showUserDialog,
    editingShiftId,
    editingTimeoffId,
    editingOvertimeId,
    editingUserId
}) {
    const showApproveTimeoffDialog = ref(false);
    const showApproveOvertimeDialog = ref(false);
    const approveForm = ref({ id: null, user_name: '', type_name: '', date: '', hours: 0, reason: '', admin_comment: '' });

    const openEditUser = (user) => {
        editingUserId.value = user.id;
        userForm.value = {
            name: user.name,
            password: '',
            role: user.role,
            phone: user.phone || '',
            wechat_user_id: user.wechat_user_id || '',
            enable_push: user.enable_push !== false
        };
        showUserDialog.value = true;
    };

    const openApproveTimeoff = (row) => {
        const typeNames = { U: '调休', B: '病假', S: '事假', H: '婚假', C: '产假', L: '护理假', J: '经期假', Y: '孕期假', R: '哺乳假', N: '年休假', T: '探亲假', Z: '丧假' };
        approveForm.value = {
            id: row.id,
            user_name: row.user_name,
            type_name: typeNames[row.type] || row.type,
            date: row.date,
            hours: row.hours,
            reason: row.reason,
            admin_comment: ''
        };
        showApproveTimeoffDialog.value = true;
    };

    const doApproveTimeoff = async (ok) => {
        await api(`/time-off/${approveForm.value.id}/approve`, {
            method: 'POST',
            body: JSON.stringify({ approved: ok, admin_comment: approveForm.value.admin_comment })
        });
        showApproveTimeoffDialog.value = false;
        await loadData();
    };

    const openApproveOvertime = (row) => {
        approveForm.value = {
            id: row.id,
            user_name: row.user_name,
            date: row.date,
            hours: row.hours,
            reason: row.reason,
            admin_comment: ''
        };
        showApproveOvertimeDialog.value = true;
    };

    const doApproveOvertime = async (ok) => {
        await api(`/overtime/${approveForm.value.id}/approve`, {
            method: 'POST',
            body: JSON.stringify({ approved: ok, admin_comment: approveForm.value.admin_comment })
        });
        showApproveOvertimeDialog.value = false;
        await loadData();
    };

    const saveTimeoff = async () => {
        const d = timeoffForm.value.date.split('T')[0];
        if (editingTimeoffId.value) {
            await api(`/time-off/${editingTimeoffId.value}`, { method: 'PUT', body: JSON.stringify({ date: d, hours: timeoffForm.value.hours, type: timeoffForm.value.type, reason: timeoffForm.value.reason }) });
        } else {
            await api('/time-off', { method: 'POST', body: JSON.stringify({ date: d, hours: timeoffForm.value.hours, type: timeoffForm.value.type, reason: timeoffForm.value.reason }) });
        }
        showTimeoffDialog.value = false;
        await loadData();
    };

    const saveOvertime = async () => {
        const d = overtimeForm.value.date.split('T')[0];
        if (editingOvertimeId.value) {
            await api(`/overtime/${editingOvertimeId.value}`, { method: 'PUT', body: JSON.stringify({ date: d, hours: overtimeForm.value.hours, reason: overtimeForm.value.reason }) });
        } else {
            await api('/overtime', { method: 'POST', body: JSON.stringify({ date: d, hours: overtimeForm.value.hours, reason: overtimeForm.value.reason }) });
        }
        showOvertimeDialog.value = false;
        await loadData();
    };

    const saveUser = async () => {
        if (editingUserId.value) {
            await api(`/users/${editingUserId.value}`, { method: 'PUT', body: JSON.stringify(userForm.value) });
        } else {
            await api('/users', { method: 'POST', body: JSON.stringify(userForm.value) });
        }
        showUserDialog.value = false;
        editingUserId.value = null;
        await loadData();
    };

    const openEditTimeoff = (row) => {
        editingTimeoffId.value = row.id;
        timeoffForm.value = { date: row.date, hours: row.hours, type: row.type || 'U', reason: row.reason };
        showTimeoffDialog.value = true;
    };

    const openEditOvertime = (row) => {
        editingOvertimeId.value = row.id;
        overtimeForm.value = { date: row.date, hours: row.hours, reason: row.reason };
        showOvertimeDialog.value = true;
    };

    const confirmDeleteTimeoff = async (id) => {
        if (confirm('确定删除？')) {
            await api(`/time-off/${id}`, { method: 'DELETE' });
            await loadData();
        }
    };

    const confirmDeleteOvertime = async (id) => {
        if (confirm('确定删除？')) {
            await api(`/overtime/${id}`, { method: 'DELETE' });
            await loadData();
        }
    };

    const confirmDeleteUser = async (id) => {
        if (confirm('确定删除？')) {
            await api(`/users/${id}`, { method: 'DELETE' });
            await loadData();
        }
    };

    const confirmDeleteShift = async (id) => {
        if (confirm('确定删除？')) {
            await api(`/shifts/${id}`, { method: 'DELETE' });
            await loadData();
        }
    };

    const notifyShift = async (row) => {
        try {
            const res = await api(`/shifts/${row.id}/notify`, { method: 'POST' });
            alert(res.message || '提醒已发送');
        } catch (e) {
            alert(`推送失败：${e.message || '请检查该用户是否绑定企业微信'}`);
        }
    };

    const openShiftDialog = (edit, row) => {
        editingShiftId.value = row ? row.id : null;
        shiftForm.value = row ? { user_id: row.user_id, date: row.date, shift_type: row.shift_type, note: row.note || '' } : { user_id: null, date: new Date().toISOString().split('T')[0], shift_type: '', note: '' };
        showShiftDialog.value = true;
    };

    const saveShift = async () => {
        if (!shiftForm.value.user_id) {
            alert('请选择人员');
            return;
        }
        const d = shiftForm.value.date.split('T')[0];
        if (editingShiftId.value) {
            await api(`/shifts/${editingShiftId.value}`, { method: 'PUT', body: JSON.stringify({ shift_type: shiftForm.value.shift_type, note: shiftForm.value.note }) });
        } else {
            await api('/shifts', { method: 'POST', body: JSON.stringify({ user_id: shiftForm.value.user_id, date: d, shift_type: shiftForm.value.shift_type, note: shiftForm.value.note }) });
        }
        showShiftDialog.value = false;
        await loadData();
    };

    const toggleUserRole = async (user) => {
        await api(`/users/${user.id}/role`, { method: 'PUT', body: JSON.stringify({ role: user.role === 'admin' ? 'member' : 'admin' }) });
        await loadData();
    };

    const openResetPassword = async (user) => {
        await api(`/users/${user.id}/reset-password`, { method: 'POST', body: JSON.stringify({ password: '123456' }) });
        alert('密码已重置为 123456');
    };

    const saveWebhookConfig = async () => {
        await api('/webhook/config', { method: 'POST', body: JSON.stringify(webhookForm.value) });
        alert('配置已保存');
    };

    const testWebhook = async () => {
        await api('/webhook/test', { method: 'POST', body: JSON.stringify({ title: '测试', content: '测试消息' }) });
        alert('测试推送已发送');
    };

    const saveWechatConfig = async () => {
        await api('/wechat/config', { method: 'POST', body: JSON.stringify(wechatConfig.value) });
        alert('企业微信配置已保存');
    };

    const testWechatPush = async () => {
        try {
            const result = await api('/wechat/test-push', { method: 'POST', body: JSON.stringify({ title: '测试推送', content: '这是一条测试消息', link: 'http://x.dysobo.cn:8888/kq/' }) });
            alert(result.message || '测试推送已发送');
        } catch (e) {
            alert(`测试失败：${e.message}`);
        }
    };

    return {
        showApproveTimeoffDialog,
        showApproveOvertimeDialog,
        approveForm,
        openEditUser,
        openApproveTimeoff,
        doApproveTimeoff,
        openApproveOvertime,
        doApproveOvertime,
        saveTimeoff,
        saveOvertime,
        saveUser,
        openEditTimeoff,
        openEditOvertime,
        confirmDeleteTimeoff,
        confirmDeleteOvertime,
        confirmDeleteUser,
        confirmDeleteShift,
        notifyShift,
        openShiftDialog,
        saveShift,
        toggleUserRole,
        openResetPassword,
        saveWebhookConfig,
        testWebhook,
        saveWechatConfig,
        testWechatPush
    };
}
