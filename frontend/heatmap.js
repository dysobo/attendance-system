function createAttendanceHeatmap({ ref, computed, overtimeList, timeoffList }) {
    const months = ['1 月', '2 月', '3 月', '4 月', '5 月', '6 月', '7 月', '8 月', '9 月', '10 月', '11 月', '12 月'];
    const heatmapYear = new Date().getFullYear();
    const cellColumnWidth = 18;
    const tooltip = ref({ visible: false, x: 0, y: 0, date: '', type: null, typeText: '', reason: '', color: '', key: '' });

    function formatDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function formatDisplayDate(dateStr) {
        const [y, m, d] = dateStr.split('-');
        return `${y}年${parseInt(m, 10)}月${parseInt(d, 10)}日`;
    }

    function formatHours(hours) {
        const normalized = Number(hours) || 0;
        return Number.isInteger(normalized) ? String(normalized) : normalized.toFixed(1).replace(/\.0$/, '');
    }

    function getColorLevel(hours) {
        if (hours <= 0) return 0;
        if (hours <= 2) return 1;
        if (hours <= 4) return 2;
        if (hours <= 6) return 3;
        return 4;
    }

    function getColor(type, hours) {
        const colors = {
            overtime: ['rgba(15, 23, 42, 0.55)', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0369a1'],
            leave: ['rgba(15, 23, 42, 0.55)', '#ffd166', '#ffb347', '#ff922b', '#f97316'],
            both: ['rgba(15, 23, 42, 0.55)', '#8b5cf6', '#7c3aed', '#6d28d9', '#5b21b6']
        };
        return colors[type][getColorLevel(hours)];
    }

    const approvedOvertimeRecords = computed(() => overtimeList.value.filter((record) => record.status === 'approved'));
    const approvedTimeoffRecords = computed(() => timeoffList.value.filter((record) => record.status === 'approved'));

    const summary = computed(() => {
        let overtimeHours = 0;
        let leaveHours = 0;
        const activeDays = new Set();
        const monthlyTotals = Array(12).fill(0);

        approvedOvertimeRecords.value.forEach((record) => {
            const hours = Number(record.hours) || 0;
            const date = new Date(record.date);
            if (Number.isNaN(date.getTime())) return;
            overtimeHours += hours;
            monthlyTotals[date.getMonth()] += hours;
            activeDays.add(record.date);
        });

        approvedTimeoffRecords.value.forEach((record) => {
            const hours = Number(record.hours) || 0;
            const date = new Date(record.date);
            if (Number.isNaN(date.getTime())) return;
            leaveHours += hours;
            monthlyTotals[date.getMonth()] += hours;
            activeDays.add(record.date);
        });

        let peakMonthIndex = -1;
        let peakMonthHours = 0;
        monthlyTotals.forEach((hours, index) => {
            if (hours > peakMonthHours) {
                peakMonthHours = hours;
                peakMonthIndex = index;
            }
        });

        return {
            totalOvertimeHours: formatHours(overtimeHours),
            totalLeaveHours: formatHours(leaveHours),
            activeDayCount: activeDays.size,
            peakMonthLabel: peakMonthIndex >= 0 ? `${peakMonthIndex + 1} 月` : '暂无',
            peakMonthHours: formatHours(peakMonthHours)
        };
    });

    const weekData = computed(() => {
        const weeks = [];
        const firstDay = new Date(heatmapYear, 0, 1);
        const lastDay = new Date(heatmapYear, 11, 31);
        const currentWeekStart = new Date(firstDay);
        currentWeekStart.setDate(currentWeekStart.getDate() - firstDay.getDay());

        const allRecords = {};

        function ensureRecord(dateStr) {
            if (!allRecords[dateStr]) {
                allRecords[dateStr] = {
                    overtimeHours: 0,
                    leaveHours: 0,
                    reasonParts: []
                };
            }
            return allRecords[dateStr];
        }

        approvedOvertimeRecords.value.forEach((record) => {
            const hours = Number(record.hours) || 0;
            const dayRecord = ensureRecord(record.date);
            dayRecord.overtimeHours += hours;
            if (record.reason) {
                dayRecord.reasonParts.push(record.reason.trim());
            }
        });

        approvedTimeoffRecords.value.forEach((record) => {
            const hours = Number(record.hours) || 0;
            const dayRecord = ensureRecord(record.date);
            dayRecord.leaveHours += hours;
            if (record.reason) {
                dayRecord.reasonParts.push(record.reason.trim());
            }
        });

        while (currentWeekStart <= lastDay) {
            const week = { days: [] };

            for (let i = 0; i < 7; i++) {
                const currentDate = new Date(currentWeekStart);
                currentDate.setDate(currentDate.getDate() + i);
                const dateStr = formatDate(currentDate);
                const isCurrentYear = currentDate.getFullYear() === heatmapYear;

                if (!isCurrentYear) {
                    week.days.push(null);
                    continue;
                }

                const info = allRecords[dateStr];
                if (!info) {
                    week.days.push({ date: dateStr, type: null, hours: 0, reason: '' });
                    continue;
                }

                const overtimeHours = info.overtimeHours;
                const leaveHours = info.leaveHours;
                const totalHours = overtimeHours + leaveHours;
                const type = overtimeHours > 0 && leaveHours > 0
                    ? 'both'
                    : overtimeHours > 0
                        ? 'overtime'
                        : 'leave';

                week.days.push({
                    date: dateStr,
                    type,
                    hours: totalHours,
                    reason: info.reasonParts.filter(Boolean).join(' / '),
                    overtimeHours,
                    leaveHours
                });
            }

            weeks.push(week);
            currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        }

        return weeks;
    });

    const monthLabels = computed(() => {
        const monthWeekCount = Array(12).fill(0);

        weekData.value.forEach((week) => {
            const validDays = week.days.filter((day) => day !== null);
            if (validDays.length === 0) return;
            const representativeDay = validDays[Math.floor(validDays.length / 2)];
            const monthIndex = new Date(representativeDay.date).getMonth();
            monthWeekCount[monthIndex] += 1;
        });

        return months
            .map((label, index) => ({
                label,
                width: Math.max(monthWeekCount[index], 1) * cellColumnWidth
            }))
            .filter((item) => item.width > 0);
    });

    const monthWidths = computed(() => monthLabels.value.map((item) => item.width));

    function getCellClass(day) {
        if (!day || !day.type) return '';
        return `cell-${day.type}-${getColorLevel(day.hours)}`;
    }

    function getPointerPoint(event) {
        if (event && event.touches && event.touches[0]) {
            return { x: event.touches[0].clientX, y: event.touches[0].clientY };
        }

        if (event && event.changedTouches && event.changedTouches[0]) {
            return { x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY };
        }

        return {
            x: event && typeof event.clientX === 'number' ? event.clientX : window.innerWidth / 2,
            y: event && typeof event.clientY === 'number' ? event.clientY : window.innerHeight / 2
        };
    }

    function buildTooltipState(event, day) {
        if (!day) return;

        let detailText = '无记录';
        if (day.type === 'both') {
            detailText = `加班 ${formatHours(day.overtimeHours)}h / 调休 ${formatHours(day.leaveHours)}h`;
        } else if (day.type === 'overtime') {
            detailText = `加班 ${formatHours(day.hours)}h`;
        } else if (day.type === 'leave') {
            detailText = `调休 ${formatHours(day.hours)}h`;
        }

        const point = getPointerPoint(event);
        const tooltipWidth = 240;
        const tooltipHeight = day.reason ? 108 : 76;
        const viewportWidth = window.innerWidth || 390;
        const viewportHeight = window.innerHeight || 844;
        const maxX = Math.max(16, viewportWidth - tooltipWidth - 16);
        const maxY = Math.max(16, viewportHeight - tooltipHeight - 16);

        return {
            visible: true,
            x: Math.min(Math.max(point.x + 12, 16), maxX),
            y: Math.min(Math.max(point.y + 12, 16), maxY),
            date: formatDisplayDate(day.date),
            type: day.type,
            typeText: detailText,
            reason: day.reason || '',
            color: day.type ? getColor(day.type, day.hours) : 'rgba(148, 163, 184, 0.7)',
            key: day.date
        };
    }

    function showTooltip(event, day) {
        const nextTooltip = buildTooltipState(event, day);
        if (!nextTooltip) return;
        tooltip.value = nextTooltip;
    }

    function toggleTooltip(event, day) {
        if (!day) {
            hideTooltip();
            return;
        }

        if (tooltip.value.visible && tooltip.value.key === day.date) {
            hideTooltip();
            return;
        }

        const nextTooltip = buildTooltipState(event, day);
        if (!nextTooltip) return;
        tooltip.value = nextTooltip;
    }

    function hideTooltip() {
        tooltip.value = { visible: false, x: 0, y: 0, date: '', type: null, typeText: '', reason: '', color: '', key: '' };
    }

    return {
        months,
        heatmapYear,
        tooltip,
        monthLabels,
        monthWidths,
        weekData,
        totalOvertimeHours: computed(() => summary.value.totalOvertimeHours),
        totalLeaveHours: computed(() => summary.value.totalLeaveHours),
        activeDayCount: computed(() => summary.value.activeDayCount),
        peakMonthLabel: computed(() => summary.value.peakMonthLabel),
        peakMonthHours: computed(() => summary.value.peakMonthHours),
        getCellClass,
        showTooltip,
        toggleTooltip,
        hideTooltip
    };
}
