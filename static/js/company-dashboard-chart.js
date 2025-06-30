document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('offresChart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        const offresActives = canvas.dataset.offresActives || 0;
        const offresPourvues = canvas.dataset.offresPourvues || 0;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Actives', 'Pourvues'],
                datasets: [{
                    data: [offresActives, offresPourvues],
                    backgroundColor: ['#3b5cb8', '#adb5bd'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { color: '#3556a8', font: { size: 14 } }
                    }
                },
                cutout: '70%'
            }
        });
    }
}); 