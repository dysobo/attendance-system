        const { createApp, ref, computed, onMounted } = Vue;
        
        createApp({
            setup() {
                const currentUser = ref(null);
                const currentPage = ref('dashboard');
                const menuOpen = ref(false);
                const loginForm = ref({ name: '', password: '' });
                const users = ref([]);
                const shifts = ref([]);
                const timeoffList = ref([]);
                const overtimeList = ref([]);
                const myStats = ref({});
                const webhookForm = ref({ enabled: false, url: '', route_id: '', notify_time_off: true, notify_overtime: true });
                const wechatConfig = ref({ enabled: false, api_url: 'https://qyapi.weixin.qq.com', corp_id: '', secret: '', agent_id: 1000006, token: '', encoding_aes_key: '' });
                const passwordForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' });
                const exportMonth = ref(new Date().getMonth() + 1);
                const exportYear = ref(new Date().getFullYear());
                const importFile = ref(null);
                const showShiftDialog = ref(false);
                const showTimeoffDialog = ref(false);
                const showOvertimeDialog = ref(false);
                const showUserDialog = ref(false);
                const shiftForm = ref({ user_id: null, date: '', shift_type: '', note: '' });
                const timeoffForm = ref({ date: '', hours: 4, type: 'U', reason: '' });
                const overtimeForm = ref({ date: '', hours: 1, reason: '' });
                const userForm = ref({ name: '', password: '', role: 'member', phone: '', wechat_user_id: '', enable_push: true });
                const editingShiftId = ref(null);
                const editingTimeoffId = ref(null);
                const editingOvertimeId = ref(null);
                const editingUserId = ref(null);
                
                const pageTitle = computed(() => ({ dashboard:'📊 仪表盘', shifts:'📅 排班管理', timeoff:'🏖️ 调休申请', overtime:'⏰ 加班记录', users:'👥 用户管理', webhook:'🔔 消息推送', password:'🔑 修改密码' })[currentPage.value] || '考勤管理');
                
                const recentShifts = computed(() => {
                    if (!currentUser.value) return [];
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    const future30Days = new Date(today.getTime() + 29 * 24 * 60 * 60 * 1000);
                    const myId = Number(currentUser.value.id);
                    
                    // 管理员显示所有人的排班，组员只显示自己的
                    if (currentUser.value.role === 'admin') {
                        return shifts.value.filter(s => {
                            const d = new Date(s.date);
                            return d >= today && d <= future30Days;
                        }).sort((a, b) => new Date(a.date) - new Date(b.date) || a.user_name.localeCompare(b.user_name));
                    } else {
                        return shifts.value.filter(s => {
                            const d = new Date(s.date);
                            return d >= today && d <= future30Days && Number(s.user_id) === myId;
                        }).sort((a, b) => new Date(a.date) - new Date(b.date));
                    }
                });
                
                const myShifts = computed(() => {
                    if (!currentUser.value) return [];
                    const today = new Date();
                    const past3Months = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);
                    const future1Month = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
                    const myId = Number(currentUser.value.id);
                    return shifts.value.filter(s => {
                        const d = new Date(s.date);
                        return d >= past3Months && d <= future1Month && Number(s.user_id) === myId;
                    }).sort((a, b) => new Date(a.date) - new Date(b.date));
                });
                
                // 班组排班 - 今日往后 30 天
                const teamShifts = computed(() => {
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    const future30Days = new Date(today.getTime() + 29 * 24 * 60 * 60 * 1000);
                    return shifts.value.filter(s => {
                        const d = new Date(s.date);
                        return d >= today && d <= future30Days;
                    }).sort((a, b) => new Date(a.date) - new Date(b.date) || a.user_name.localeCompare(b.user_name));
                });
                
                const {
                    months,
                    heatmapYear,
                    tooltip,
                    monthLabels,
                    monthWidths,
                    weekData,
                    totalOvertimeHours,
                    totalLeaveHours,
                    activeDayCount,
                    peakMonthLabel,
                    peakMonthHours,
                    getCellClass,
                    showTooltip,
                    toggleTooltip,
                    hideTooltip
                } = createAttendanceHeatmap({
                    ref,
                    computed,
                    overtimeList,
                    timeoffList
                });
                
        const api = createAttendanceApi(currentUser);
                
                const { handleLogin, handleLogout, loadData, loadUserInfo } = createAttendanceSession({
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
                });
                
                const {
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
                } = createAttendanceActions({
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
                });
                
                const { exportMonthlyStats, exportBackup, importBackup, changePassword } = createAttendanceDataTools({
                    api,
                    exportMonth,
                    exportYear,
                    passwordForm,
                    loadData
                });
                
                onMounted(() => {
                    const token = localStorage.getItem('token');
                    if (token) {
                        const payload = JSON.parse(atob(token.split('.')[1]));
                        currentUser.value = { id: payload.sub, name: '用户', role: payload.role };
                        loadData().then(() => {
                            loadUserInfo();
                            // 检查 URL 参数，支持从推送消息直接跳转和快捷方式
                            const urlParams = new URLSearchParams(window.location.search);
                            const page = urlParams.get('page');
                            const recordId = urlParams.get('id');
                            const action = urlParams.get('action');
                            
                            // 快捷方式：?action=tx 直接打开调休申请对话框
                            if (action === 'tx') {
                                currentPage.value = 'timeoff';
                                setTimeout(() => {
                                    showTimeoffDialog.value = true;
                                }, 500);
                            }
                            // 快捷方式：?action=jj 直接打开加班申请对话框
                            else if (action === 'jj') {
                                currentPage.value = 'overtime';
                                setTimeout(() => {
                                    showOvertimeDialog.value = true;
                                }, 500);
                            }
                            // 管理员审批跳转
                            else if (page && recordId && currentUser.value.role === 'admin') {
                                if (page === 'timeoff') {
                                    currentPage.value = 'timeoff';
                                    setTimeout(() => {
                                        const row = timeoffList.value.find(r => r.id == recordId);
                                        if (row) {
                                            openApproveTimeoff(row);
                                        }
                                    }, 500);
                                } else if (page === 'overtime') {
                                    currentPage.value = 'overtime';
                                    setTimeout(() => {
                                        const row = overtimeList.value.find(r => r.id == recordId);
                                        if (row) {
                                            openApproveOvertime(row);
                                        }
                                    }, 500);
                                }
                            }
                        });
                    }
                });
                
                return { currentUser, currentPage, menuOpen, loginForm, users, shifts, timeoffList, overtimeList, myStats, webhookForm, wechatConfig, passwordForm, exportMonth, exportYear, importFile, showShiftDialog, showTimeoffDialog, showOvertimeDialog, showUserDialog, showApproveTimeoffDialog, showApproveOvertimeDialog, shiftForm, timeoffForm, overtimeForm, userForm, approveForm, pageTitle, recentShifts, myShifts, teamShifts, months, heatmapYear, monthLabels, monthWidths, weekData, totalOvertimeHours, totalLeaveHours, activeDayCount, peakMonthLabel, peakMonthHours, tooltip, handleLogin, handleLogout, loadData, loadUserInfo, openShiftDialog, saveShift, confirmDeleteShift, notifyShift, saveTimeoff, saveOvertime, saveUser, openApproveTimeoff, doApproveTimeoff, openApproveOvertime, doApproveOvertime, openEditTimeoff, openEditOvertime, openEditUser, confirmDeleteTimeoff, confirmDeleteOvertime, confirmDeleteUser, toggleUserRole, openResetPassword, saveWebhookConfig, testWebhook, saveWechatConfig, testWechatPush, exportMonthlyStats, exportBackup, importBackup, changePassword, getCellClass, showTooltip, toggleTooltip, hideTooltip };
            }
        }).use(ElementPlus).mount('#app');
    

