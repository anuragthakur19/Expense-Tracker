function renderCategoryChart(expenseData) {
  // Aggregate expenses by category
  const categoryTotals = expenseData.reduce((acc, expense) => {
    acc[expense.category] = (acc[expense.category] || 0) + expense.amount;
    return acc;
  }, {});

  const labels = Object.keys(categoryTotals);
  const data = Object.values(categoryTotals);

  // Get theme for chart colors
  const isDarkMode = document.body.classList.contains('dark-mode');
  const backgroundColors = isDarkMode
    ? ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeead', '#d4a5a5']
    : ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d'];

  // Destroy existing chart to prevent duplication
  const existingChart = Chart.getChart('categoryChart');
  if (existingChart) {
    existingChart.destroy();
  }

  const ctx = document.getElementById('categoryChart').getContext('2d');
  new Chart(ctx, {
    type: 'pie', // Changed from 'bar' to 'pie'
    data: {
      labels: labels,
      datasets: [{
        label: 'Expenses by Category',
        data: data,
        backgroundColor: backgroundColors,
        borderColor: '#fff',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: isDarkMode ? '#ffffff' : '#000000' },
          position: 'right'
        },
        title: {
          display: true,
          text: 'Expenses by Category',
          color: isDarkMode ? '#ffffff' : '#000000',
          font: { size: 16 }
        }
      }
    }
  });
}
