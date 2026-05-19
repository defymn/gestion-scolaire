document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.getElementById('sidebar');
  var toggle = document.getElementById('sidebar-toggle');
  if (sidebar && toggle) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
  }

  document.querySelectorAll('[data-auto-dismiss="true"]').forEach(function (el) {
    setTimeout(function () {
      el.remove();
    }, 4000);
  });

  document.querySelectorAll('.js-delete-confirm').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      if (!confirm('Are you sure you want to delete this item?')) {
        e.preventDefault();
      }
    });
  });

  var gradeForm = document.getElementById('grade-form');
  if (gradeForm) {
    gradeForm.addEventListener('submit', function (e) {
      var valueInput = gradeForm.querySelector('input[name="value"]');
      if (valueInput) {
        var value = parseFloat(valueInput.value);
        if (isNaN(value) || value < 0 || value > 20) {
          e.preventDefault();
          alert('Grade value must be between 0 and 20.');
        }
      }
    });
  }

  var selectAllPresent = document.getElementById('select-all-present');
  if (selectAllPresent) {
    selectAllPresent.addEventListener('click', function () {
      document.querySelectorAll('.attendance-row select').forEach(function (select) {
        select.value = 'present';
      });
    });
  }

  var dayMap = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var today = dayMap[new Date().getDay()];
  document.querySelectorAll('.schedule-col').forEach(function (col) {
    if (col.dataset.day === today) {
      col.classList.add('today');
    }
  });

  var tableRows = document.querySelectorAll('#report-table tbody tr');
  var canvas = document.getElementById('report-chart');
  if (canvas && tableRows.length) {
    var ctx = canvas.getContext('2d');
    var width = canvas.width = canvas.offsetWidth;
    var height = canvas.height = 220;
    var max = 100;
    var barWidth = Math.max(30, (width - 40) / tableRows.length - 12);
    tableRows.forEach(function (row, index) {
      var value = parseFloat(row.dataset.value || '0');
      var x = 20 + index * (barWidth + 12);
      var barHeight = (value / max) * (height - 40);
      var y = height - 20 - barHeight;
      ctx.fillStyle = '#1a56db';
      ctx.fillRect(x, y, barWidth, barHeight);
      ctx.fillStyle = '#111827';
      ctx.font = '12px Arial';
      ctx.fillText(row.dataset.label, x, height - 5);
      ctx.fillText(value.toFixed(1) + '%', x, y - 4);
    });
  }
});
