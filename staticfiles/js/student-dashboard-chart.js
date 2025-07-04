document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('candidaturesChart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        const enAttente = canvas.dataset.enAttente || 0;
        const acceptees = canvas.dataset.acceptees || 0;
        const refusees = canvas.dataset.refusees || 0;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ["En attente", "Acceptées", "Refusées"],
                datasets: [{
                    label: 'Candidatures',
                    data: [enAttente, acceptees, refusees],
                    backgroundColor: ['#f9a825', '#4caf50', '#ef5350'],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }
}); 