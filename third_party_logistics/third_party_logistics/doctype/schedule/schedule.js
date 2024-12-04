// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Schedule', {
    validate: function(frm) {
        let time_slots = {};

        frm.doc.time_slots.forEach((row) => {
            if (!time_slots[row.day]) {
                time_slots[row.day] = [];
            }
            const slot = row.from_time;
            if (time_slots[row.day].includes(slot)) {
                frappe.throw(
                    `The time slot ${slot} is already selected for ${row.day}. Please choose a different time.`
                );
            }
            time_slots[row.day].push(slot);
        });
    },
});
