const { createApp, ref, computed, onMounted, watch } = Vue;

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
        const exportUserOrder = ref([]);
        const selectedExportUserIds = ref([]);
        const exportUserSelectionInitialized = ref(false);
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

        const pageTitle = computed(() => ({
            dashboard: '📊 仪表盘',
            shifts: '📅 排班管理',
            timeoff: '🏖️ 调休申请',
            overtime: '⏰ 加班记录',
            users: '👥 用户管理',
            webhook: '🔔 消息推送',
            export: '📊 数据导出',
            password: '🔑 修改密码'
        })[currentPage.value] || '考勤管理');

        const exportCandidates = computed(() => {
            const memberMap = new Map(users.value.filter((user) => user.role === 'member').map((user) => [Number(user.id), user]));
            return exportUserOrder.value.map((id) => memberMap.get(Number(id))).filter(Boolean);
        });

        const exportSelectedUserIds = computed(() => exportUserOrder.value.filter((id) => selectedExportUserIds.value.includes(id)));
        const selectedExportUsers = computed(() => exportCandidates.value.filter((user) => selectedExportUserIds.value.includes(Number(user.id))));

        function syncExportUsers(nextUsers) {
            const memberIds = (nextUsers || []).filter((user) => user.role === 'member').map((user) => Number(user.id));
            const previousOrder = exportUserOrder.value.slice();
            exportUserOrder.value = [
                ...previousOrder.filter((id) => memberIds.includes(id)),
                ...memberIds.filter((id) => !previousOrder.includes(id))
            ];

            const keptSelectedIds = selectedExportUserIds.value.filter((id) => memberIds.includes(id));
            const newMemberIds = memberIds.filter((id) => !previousOrder.includes(id));
            if (!exportUserSelectionInitialized.value) {
                selectedExportUserIds.value = exportUserOrder.value.slice();
                exportUserSelectionInitialized.value = true;
            } else {
                selectedExportUserIds.value = [...keptSelectedIds, ...newMemberIds];
            }
        }

        function moveExportUser(userId, direction) {
            const currentIndex = exportUserOrder.value.indexOf(Number(userId));
            const targetIndex = currentIndex + direction;
            if (currentIndex < 0 || targetIndex < 0 || targetIndex >= exportUserOrder.value.length) {
                return;
            }

            const nextOrder = exportUserOrder.value.slice();
            [nextOrder[currentIndex], nextOrder[targetIndex]] = [nextOrder[targetIndex], nextOrder[currentIndex]];
            exportUserOrder.value = nextOrder;
        }

        function selectAllExportUsers() {
            selectedExportUserIds.value = exportUserOrder.value.slice();
        }

        function clearExportUsers() {
            selectedExportUserIds.value = [];
        }

        const recentShifts = computed(() => {
            if (!currentUser.value) return [];
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const future30Days = new Date(today.getTime() + 29 * 24 * 60 * 60 * 1000);
            const myId = Number(currentUser.value.id);

            if (currentUser.value.role === 'admin') {
                return shifts.value.filter((shift) => {
                    const shiftDate = new Date(shift.date);
                    return shiftDate >= today && shiftDate <= future30Days;
                }).sort((a, b) => new Date(a.date) - new Date(b.date) || a.user_name.localeCompare(b.user_name));
            }

            return shifts.value.filter((shift) => {
                const shiftDate = new Date(shift.date);
                return shiftDate >= today && shiftDate <= future30Days && Number(shift.user_id) === myId;
            }).sort((a, b) => new Date(a.date) - new Date(b.date));
        });

        const myShifts = computed(() => {
            if (!currentUser.value) return [];
            const today = new Date();
            const past3Months = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);
            const future1Month = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
            const myId = Number(currentUser.value.id);
            return shifts.value.filter((shift) => {
                const shiftDate = new Date(shift.date);
                return shiftDate >= past3Months && shiftDate <= future1Month && Number(shift.user_id) === myId;
            }).sort((a, b) => new Date(a.date) - new Date(b.date));
        });

        const teamShifts = computed(() => {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const future30Days = new Date(today.getTime() + 29 * 24 * 60 * 60 * 1000);
            return shifts.value.filter((shift) => {
                const shiftDate = new Date(shift.date);
                return shiftDate >= today && shiftDate <= future30Days;
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
            exportSelectedUserIds,
            passwordForm,
            loadData
        });

        watch(users, (nextUsers) => {
            syncExportUsers(nextUsers);
        });

        onMounted(() => {
            const token = localStorage.getItem('token');
            if (!token) {
                return;
            }

            const payload = JSON.parse(atob(token.split('.')[1]));
            currentUser.value = { id: payload.sub, name: '用户', role: payload.role };
            loadData().then(() => {
                loadUserInfo();
                const urlParams = new URLSearchParams(window.location.search);
                const page = urlParams.get('page');
                const recordId = urlParams.get('id');
                const action = urlParams.get('action');

                if (action === 'tx') {
                    currentPage.value = 'timeoff';
                    setTimeout(() => {
                        showTimeoffDialog.value = true;
                    }, 500);
                } else if (action === 'jj') {
                    currentPage.value = 'overtime';
                    setTimeout(() => {
                        showOvertimeDialog.value = true;
                    }, 500);
                } else if (page && recordId && currentUser.value.role === 'admin') {
                    if (page === 'timeoff') {
                        currentPage.value = 'timeoff';
                        setTimeout(() => {
                            const row = timeoffList.value.find((item) => item.id == recordId);
                            if (row) {
                                openApproveTimeoff(row);
                            }
                        }, 500);
                    } else if (page === 'overtime') {
                        currentPage.value = 'overtime';
                        setTimeout(() => {
                            const row = overtimeList.value.find((item) => item.id == recordId);
                            if (row) {
                                openApproveOvertime(row);
                            }
                        }, 500);
                    }
                }
            });
        });

        return {
            currentUser,
            currentPage,
            menuOpen,
            loginForm,
            users,
            shifts,
            timeoffList,
            overtimeList,
            myStats,
            webhookForm,
            wechatConfig,
            passwordForm,
            exportMonth,
            exportYear,
            exportCandidates,
            selectedExportUsers,
            selectedExportUserIds,
            importFile,
            showShiftDialog,
            showTimeoffDialog,
            showOvertimeDialog,
            showUserDialog,
            showApproveTimeoffDialog,
            showApproveOvertimeDialog,
            shiftForm,
            timeoffForm,
            overtimeForm,
            userForm,
            approveForm,
            pageTitle,
            recentShifts,
            myShifts,
            teamShifts,
            months,
            heatmapYear,
            monthLabels,
            monthWidths,
            weekData,
            totalOvertimeHours,
            totalLeaveHours,
            activeDayCount,
            peakMonthLabel,
            peakMonthHours,
            tooltip,
            handleLogin,
            handleLogout,
            loadData,
            loadUserInfo,
            openShiftDialog,
            saveShift,
            confirmDeleteShift,
            notifyShift,
            saveTimeoff,
            saveOvertime,
            saveUser,
            openApproveTimeoff,
            doApproveTimeoff,
            openApproveOvertime,
            doApproveOvertime,
            openEditTimeoff,
            openEditOvertime,
            openEditUser,
            confirmDeleteTimeoff,
            confirmDeleteOvertime,
            confirmDeleteUser,
            toggleUserRole,
            openResetPassword,
            saveWebhookConfig,
            testWebhook,
            saveWechatConfig,
            testWechatPush,
            exportMonthlyStats,
            exportBackup,
            importBackup,
            changePassword,
            moveExportUser,
            selectAllExportUsers,
            clearExportUsers,
            getCellClass,
            showTooltip,
            toggleTooltip,
            hideTooltip
        };
    }
}).use(ElementPlus).mount('#app');
