function createAttendanceSession({
    api,
    currentUser,
    loginForm,
    users,
    shifts,
    timeoffList,
    overtimeList,
    myStats,
    webhookForm,
    wechatConfig
}) {
    const handleLogin = async () => {
        const data = await api('/login', { method: 'POST', body: JSON.stringify(loginForm.value) });
        localStorage.setItem('token', data.token);
        currentUser.value = data.user;
        await loadData();
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        currentUser.value = null;
    };

    const loadData = async () => {
        const stats = await api('/stats/summary');
        myStats.value = stats;

        if (currentUser.value.role === 'admin') {
            const [u, s, t, o] = await Promise.all([api('/users'), api('/shifts'), api('/time-off'), api('/overtime')]);
            users.value = u;
            shifts.value = s;
            timeoffList.value = t;
            overtimeList.value = o;

            const webhookConfig = await api('/webhook/config');
            webhookForm.value = webhookConfig;

            const wechatCfg = await api('/wechat/config');
            wechatConfig.value = wechatCfg;
            return;
        }

        const me = await api('/me');
        currentUser.value = { ...currentUser.value, ...me };
        users.value = [];
        const uid = me.id;
        const [myS, teamS, t, o] = await Promise.all([
            api(`/shifts?user_id=${uid}`),
            api('/shifts/team'),
            api(`/time-off?user_id=${uid}`),
            api(`/overtime?user_id=${uid}`)
        ]);

        shifts.value = [...myS, ...teamS].reduce((acc, cur) => {
            if (!acc.find((item) => item.id === cur.id)) {
                acc.push(cur);
            }
            return acc;
        }, []).sort((a, b) => new Date(a.date) - new Date(b.date));
        timeoffList.value = t;
        overtimeList.value = o;
    };

    const loadUserInfo = async () => {
        try {
            const me = await api('/me');
            currentUser.value = { ...currentUser.value, ...me };
        } catch (e) {
            console.error('加载用户信息失败:', e);
        }
    };

    return {
        handleLogin,
        handleLogout,
        loadData,
        loadUserInfo
    };
}
